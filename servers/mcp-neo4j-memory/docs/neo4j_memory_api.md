# Neo4j Memory Management API 文档

## 概述

`neo4j_memory.py` 是一个基于Neo4j图数据库的知识图谱内存管理系统。该系统提供了完整的CRUD操作来管理实体（Entity）、关系（Relation）和约束（Constraint），支持全文搜索和复杂的图查询操作。

## 核心特性

- 🗄️ **异步操作**: 基于Neo4j的异步驱动，支持高并发操作
- 🔍 **全文搜索**: 内置全文搜索索引，支持模糊查询
- 🏷️ **约束管理**: 支持"必须"、"禁止"、"建议"三种约束类型
- 📊 **图数据模型**: 完整的实体-关系图数据模型
- 🚀 **批量操作**: 支持批量创建、删除和更新操作

## 数据模型

### 1. Entity（实体）

```python
class Entity(BaseModel):
    name: str          # 实体名称
    type: str          # 实体类型
    constraint: Dict[  # 约束条件
        '必须': Any,    # 必须满足的条件
        '禁止': Any,    # 禁止的条件
        '建议': Any     # 建议的条件
    ]
```

**说明**: 实体是知识图谱中的基本节点，代表现实世界中的对象、概念或事件。每个实体都有名称、类型和约束属性。

### 2. Relation（关系）

```python
class Relation(BaseModel):
    source: str        # 源实体名称
    target: str        # 目标实体名称
    relationType: str  # 关系类型
    description: str   # 关系描述
```

**说明**: 关系定义了实体之间的连接，支持有向图结构。关系类型可以是任意字符串，如"包含"、"属于"、"影响"等。

### 3. KnowledgeGraph（知识图谱）

```python
class KnowledgeGraph(BaseModel):
    entities: List[Entity]    # 实体列表
    relations: List[Relation] # 关系列表
```

**说明**: 知识图谱是实体和关系的集合，构成了完整的图数据结构。

### 4. 约束操作模型

```python
class ConstraintAddition(BaseModel):
    entityName: str    # 实体名称
    constraint: Dict[  # 要添加的约束
        '必须': Any,
        '禁止': Any,
        '建议': Any
    ]

class ConstraintDeletion(BaseModel):
    entityName: str    # 实体名称
    constraint: Dict[  # 要删除的约束
        '必须': Any,
        '禁止': Any,
        '建议': Any
    ]
```

## 核心类：Neo4jMemory

### 初始化

```python
class Neo4jMemory:
    def __init__(self, neo4j_driver: AsyncDriver):
        self.driver = neo4j_driver
```

**参数**:
- `neo4j_driver`: Neo4j异步驱动实例

## API 方法详解

### 索引管理

#### `create_fulltext_index()`

创建全文搜索索引，用于支持模糊查询。

```python
async def create_fulltext_index(self):
    """Create a fulltext search index for entities if it doesn't exist."""
```

**功能**: 
- 在Memory节点上创建全文搜索索引
- 索引覆盖name、type、constraint字段
- 使用`IF NOT EXISTS`避免重复创建

**Neo4j查询**:
```cypher
CREATE FULLTEXT INDEX search IF NOT EXISTS FOR (m:Memory) 
ON EACH [m.name, m.type, m.constraint];
```

**查询解释**:
- `CREATE FULLTEXT INDEX`: 创建全文搜索索引
- `search`: 索引名称
- `IF NOT EXISTS`: 如果索引已存在则不创建（避免重复创建错误）
- `FOR (m:Memory)`: 为标签为Memory的节点创建索引
- `ON EACH [m.name, m.type, m.constraint]`: 索引覆盖节点的name、type、constraint三个属性
- 这个索引支持对这三个字段进行全文搜索，提高查询性能

### 图数据加载

#### `load_graph(filter_query: str = "*")`

从Neo4j加载知识图谱数据。

```python
async def load_graph(self, filter_query: str = "*") -> KnowledgeGraph:
    """Load the entire knowledge graph from Neo4j."""
```

**参数**:
- `filter_query`: 全文搜索过滤条件，默认为"*"（匹配所有）

**功能**:
- 使用全文搜索索引查询节点
- 自动获取节点的关系信息
- 返回完整的KnowledgeGraph对象

**Neo4j查询**:
```cypher
CALL db.index.fulltext.queryNodes('search', $filter) yield node as entity, score
OPTIONAL MATCH (entity)-[r]-(other)
RETURN collect(distinct {
    name: entity.name,
    type: entity.type,
    constraint: entity.constraint
}) as nodes,
collect(distinct {
    source: startNode(r).name,
    target: endNode(r).name,
    relationType: type(r)
}) as relations
```

**查询解释**:
- `CALL db.index.fulltext.queryNodes('search', $filter)`: 调用全文搜索索引'search'，使用$filter参数进行搜索
- `yield node as entity, score`: 返回匹配的节点（重命名为entity）和匹配分数
- `OPTIONAL MATCH (entity)-[r]-(other)`: 可选地匹配与entity节点相关的所有关系r和相邻节点other
- `collect(distinct {...}) as nodes`: 收集去重后的节点信息（name、type、constraint）
- `collect(distinct {...}) as relations`: 收集去重后的关系信息（source、target、relationType）
- `startNode(r).name`: 获取关系r的起始节点名称
- `endNode(r).name`: 获取关系r的结束节点名称
- `type(r)`: 获取关系r的类型

### 实体管理

#### `create_entities(entities: List[Entity])`

批量创建实体。

```python
async def create_entities(self, entities: List[Entity]) -> List[Entity]:
    """Create multiple new entities in the knowledge graph."""
```

**功能**:
- 使用MERGE操作避免重复创建
- 自动设置节点标签为实体类型
- 支持批量操作提高性能

**Neo4j查询**:
```cypher
WITH $entity as entity
MERGE (e:Memory { name: entity.name })
SET e += entity { .type, .constraint }
SET e:`{entity.type}`
```

**查询解释**:
- `WITH $entity as entity`: 将参数$entity赋值给变量entity，便于后续使用
- `MERGE (e:Memory { name: entity.name })`: 如果不存在name为entity.name的Memory节点则创建，如果存在则匹配
- `SET e += entity { .type, .constraint }`: 将entity的type和constraint属性合并到节点e上（+=表示合并属性）
- `SET e:\`{entity.type}\``: 为节点e添加一个动态标签，标签名称为entity.type的值
- 例如：如果entity.type="Person"，则节点会同时具有Memory和Person两个标签

#### `delete_entities(entity_names: List[str])`

批量删除实体及其关系。

```python
async def delete_entities(self, entity_names: List[str]) -> None:
    """Delete multiple entities and their associated relations."""
```

**功能**:
- 使用DETACH DELETE删除节点及其所有关系
- 支持批量删除操作

**Neo4j查询**:
```cypher
UNWIND $entities as name
MATCH (e:Memory { name: name })
DETACH DELETE e
```

**查询解释**:
- `UNWIND $entities as name`: 将$entities数组展开，每个元素赋值给变量name
- `MATCH (e:Memory { name: name })`: 匹配name属性等于当前name值的Memory节点
- `DETACH DELETE e`: 删除节点e及其所有相关关系，DETACH确保先删除关系再删除节点
- 这个操作会级联删除，避免出现悬空的关系

### 关系管理

#### `create_relations(relations: List[Relation])`

批量创建关系。

```python
async def create_relations(self, relations: List[Relation]) -> List[Relation]:
    """Create multiple new relations between entities."""
```

**功能**:
- 在已存在的实体之间创建关系
- 使用MERGE避免重复关系
- 支持动态关系类型

**Neo4j查询**:
```cypher
WITH $relation as relation
MATCH (from:Memory),(to:Memory)
WHERE from.name = relation.source AND to.name = relation.target
MERGE (from)-[r:`{relation.relationType}`]->(to)
```

**查询解释**:
- `WITH $relation as relation`: 将参数$relation赋值给变量relation
- `MATCH (from:Memory),(to:Memory)`: 匹配两个Memory节点，分别赋值给from和to
- `WHERE from.name = relation.source AND to.name = relation.target`: 筛选条件：from节点的name等于relation.source，to节点的name等于relation.target
- `MERGE (from)-[r:\`{relation.relationType}\`]->(to)`: 在from和to节点之间创建类型为relation.relationType的关系，如果关系已存在则不重复创建
- 动态关系类型：关系类型在运行时根据relation.relationType的值确定

#### `delete_relations(relations: List[Relation])`

批量删除关系。

```python
async def delete_relations(self, relations: List[Relation]) -> None:
    """Delete multiple relations from the graph."""
```

**功能**:
- 精确匹配并删除指定关系
- 不影响实体节点

**Neo4j查询**:
```cypher
WITH $relation as relation
MATCH (source:Memory)-[r:`{relation.relationType}`]->(target:Memory)
WHERE source.name = relation.source AND target.name = relation.target
DELETE r
```

**查询解释**:
- `WITH $relation as relation`: 将参数$relation赋值给变量relation
- `MATCH (source:Memory)-[r:\`{relation.relationType}\`]->(target:Memory)`: 匹配特定类型的关系r，连接source和target两个Memory节点
- `WHERE source.name = relation.source AND target.name = relation.target`: 精确匹配源节点和目标节点的名称
- `DELETE r`: 删除匹配到的关系r，保留节点不变

### 约束管理

#### `add_constraint(constraint: List[ConstraintAddition])`

为实体添加约束。

```python
async def add_constraint(self, constraint: List[ConstraintAddition]) -> List[Dict[str, Any]]:
    """Add new constraint to existing entities."""
```

**功能**:
- 向现有实体添加新约束
- 避免重复约束
- 返回添加结果

**Neo4j查询**:
```cypher
UNWIND $constraint as obs
MATCH (e:Memory { name: obs.entityName })
WITH e, [o in obs.constraint WHERE NOT o IN e.constraint] as new
SET e.constraint = coalesce(e.constraint,[]) + new
RETURN e.name as name, new
```

**查询解释**:
- `UNWIND $constraint as obs`: 将$constraint数组展开，每个元素赋值给变量obs
- `MATCH (e:Memory { name: obs.entityName })`: 匹配name为obs.entityName的Memory节点
- `WITH e, [o in obs.constraint WHERE NOT o IN e.constraint] as new`: 筛选出obs.constraint中不在e.constraint中的新约束，赋值给new
- `SET e.constraint = coalesce(e.constraint,[]) + new`: 设置节点的constraint属性
  - `coalesce(e.constraint,[])`: 如果e.constraint为null则使用空数组[]
  - `+ new`: 将新约束添加到现有约束数组中
- `RETURN e.name as name, new`: 返回节点名称和新添加的约束

#### `delete_constraint(deletions: List[ObservationDeletion])`

删除实体约束。

```python
async def delete_constraint(self, deletions: List[ObservationDeletion]) -> None:
    """Delete specific constraint from entities."""
```

**注意**: 代码中存在类型不一致问题，参数类型应该是`ConstraintDeletion`而不是`ObservationDeletion`。

**Neo4j查询**:
```cypher
UNWIND $deletions as d
MATCH (e:Memory { name: d.entityName })
SET e.constraint = [o in coalesce(e.constraint,[]) WHERE NOT o IN d.constraint]
```

**查询解释**:
- `UNWIND $deletions as d`: 将$deletions数组展开，每个元素赋值给变量d
- `MATCH (e:Memory { name: d.entityName })`: 匹配name为d.entityName的Memory节点
- `SET e.constraint = [o in coalesce(e.constraint,[]) WHERE NOT o IN d.constraint]`: 设置节点的constraint属性
  - `coalesce(e.constraint,[])`: 如果e.constraint为null则使用空数组[]
  - `[o in ... WHERE NOT o IN d.constraint]`: 列表推导式，保留不在d.constraint中的约束
  - 这个操作实现了从现有约束中删除指定约束的功能

### 查询操作

#### `read_graph()`

读取完整知识图谱。

```python
async def read_graph(self) -> KnowledgeGraph:
    """Read the entire knowledge graph."""
    return await self.load_graph()
```

#### `search_memories(query: str)`

全文搜索记忆。

```python
async def search_memories(self, query: str) -> KnowledgeGraph:
    """Search for memories based on a query with Fulltext Search."""
    return await self.load_graph(query)
```

#### `find_memories_by_name(names: List[str])`

按名称精确查找记忆。

```python
async def find_memories_by_name(self, names: List[str]) -> KnowledgeGraph:
    """Find specific memories by their names. This does not use fulltext search."""
```

**功能**:
- 不使用全文搜索，直接按名称匹配
- 同时获取相关的关系信息
- 支持批量名称查询

**Neo4j查询1 - 查找节点**:
```cypher
MATCH (e:Memory)
WHERE e.name IN $names
RETURN  e.name as name,
        e.type as type,
        e.constraint as constraint
```

**查询1解释**:
- `MATCH (e:Memory)`: 匹配所有标签为Memory的节点
- `WHERE e.name IN $names`: 筛选name属性在$names数组中的节点
- `RETURN`: 返回节点的name、type、constraint属性

**Neo4j查询2 - 查找关系**:
```cypher
MATCH (source:Memory)-[r]->(target:Memory)
WHERE source.name IN $names OR target.name IN $names
RETURN  source.name as source,
        target.name as target,
        type(r) as relationType
```

**查询2解释**:
- `MATCH (source:Memory)-[r]->(target:Memory)`: 匹配所有有向关系，source和target都是Memory节点
- `WHERE source.name IN $names OR target.name IN $names`: 筛选源节点或目标节点名称在$names数组中的关系
- `RETURN`: 返回关系的源节点、目标节点和关系类型
- 这个查询可以找到与指定节点相关的所有关系，包括入度和出度关系

## 使用示例

### 基本使用流程

```python
from neo4j import AsyncDriver
from mcp_neo4j_memory import Neo4jMemory, Entity, Relation

# 初始化
memory = Neo4jMemory(neo4j_driver)

# 创建全文索引
await memory.create_fulltext_index()

# 创建实体
entities = [
    Entity(
        name="张三",
        type="Person",
        constraint={
            "必须": ["有身份证"],
            "禁止": ["违法犯罪"],
            "建议": ["诚实守信"]
        }
    )
]

await memory.create_entities(entities)

# 创建关系
relations = [
    Relation(
        source="张三",
        target="公司A",
        relationType="工作于",
        description="张三在公司A工作"
    )
]

await memory.create_relations(relations)

# 搜索
results = await memory.search_memories("张三")
```

### 约束管理示例

```python
# 添加约束
constraint_add = [
    ConstraintAddition(
        entityName="张三",
        constraint={
            "必须": ["按时上下班"],
            "建议": ["积极学习"]
        }
    )
]

await memory.add_constraint(constraint_add)

# 删除约束
constraint_del = [
    ConstraintDeletion(
        entityName="张三",
        constraint={
            "建议": ["积极学习"]
        }
    )
]

await memory.delete_constraint(constraint_del)
```

## 注意事项

### 1. 类型不一致问题

代码中存在类型定义不一致的问题：
- `delete_constraint`方法参数类型为`ObservationDeletion`
- 但实际应该使用`ConstraintDeletion`
