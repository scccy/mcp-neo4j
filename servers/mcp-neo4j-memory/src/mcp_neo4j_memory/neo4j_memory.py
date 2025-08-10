import logging
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from neo4j import AsyncDriver, RoutingControl
from pydantic import BaseModel, Field, field_validator

# Set up logging
logger = logging.getLogger('mcp_neo4j_memory')
logger.setLevel(logging.INFO)

# # 定义约束类型
# ConstraintType = Literal["必须", "禁止"]
#
# # Models for our knowledge graph
# class Entity(BaseModel):
#     name: str
#     operation_type: str  # 操作类型（原来的type）
#     node_type: str       # 节点类型
#     point: int           # 级别（改为强制需要）
#     description: str     # name中文描述
#     node_description: str  # node_type中文描述
#     constraint: Dict[ConstraintType, List[str]] = Field(
#         default_factory=lambda: {"必须": [], "禁止": []},
#         description="约束条件，包含必须满足的条件和禁止的条件"
#     )
#     label: List[str]

class ConstraintType(str, Enum):
  REQUIRED = "必须"
  FORBIDDEN = "禁止"


class Entity(BaseModel):
  name: str
  operation_type: str
  node_type: str
  point: int
  description: str
  node_description: str
  constraint: Optional[Dict[ConstraintType, List[str]]] = None
  label: List[str]

  @field_validator('constraint', mode='before')
  def set_default_constraint(cls, v):
    if v is None:
      return {
        ConstraintType.REQUIRED: [],
        ConstraintType.FORBIDDEN: []
      }
    return v

class Relation(BaseModel):
    source: str
    target: str
    relationType: str
    description: str


class KnowledgeGraph(BaseModel):
    entities: List[Entity]
    relations: List[Relation]

class ConstraintAddition(BaseModel):
    entityName: str
    constraint: Dict[ConstraintType, List[str]] = Field(
        description="要添加的约束条件，包含必须满足的条件和禁止的条件"
    )


class ConstraintDeletion(BaseModel):
    entityName: str
    constraint: Dict[ConstraintType, List[str]] = Field(
        description="要删除的约束条件，包含必须满足的条件和禁止的条件"
    )

class Neo4jMemory:
    def __init__(self, neo4j_driver: AsyncDriver):
        self.driver = neo4j_driver

    def _parse_constraint(self, constraint_data):
        """Parse constraint data from Neo4j, handling both JSON strings and dictionaries."""
        if isinstance(constraint_data, str):
            try:
                import json
                return json.loads(constraint_data)
            except (json.JSONDecodeError, TypeError):
                return {}
        elif isinstance(constraint_data, dict):
            return constraint_data
        else:
            return {}

    async def create_fulltext_index(self):
        """Create a fulltext search index for entities if it doesn't exist."""
        try:
            query = "CREATE FULLTEXT INDEX search IF NOT EXISTS FOR (m:Memory) ON EACH [m.name, m.operation_type, m.node_type, m.point, m.description, m.constraint];"
            await self.driver.execute_query(query, routing_control=RoutingControl.WRITE)
            logger.info("Created fulltext search index")
        except Exception as e:
            # Index might already exist, which is fine
            logger.debug(f"Fulltext index creation: {e}")

    async def load_graph(self, filter_query: str = "*"):
        """Load the entire knowledge graph from Neo4j."""
        logger.info("Loading knowledge graph from Neo4j")
        query = """
            MATCH (e)
            OPTIONAL MATCH (e)-[r]-(other)
            RETURN collect(distinct {
                name: e.name,
                operation_type: e.operation_type,
                node_type: e.node_type,
                point: e.point,
                description: e.description,
                node_description: e.node_description,
                constraint: e.constraint,
                labels: labels(e)
            }) as nodes,
            collect(distinct {
                source: startNode(r).name,
                target: endNode(r).name,
                relationType: type(r),
                description: r.description
            }) as relations
        """

        result = await self.driver.execute_query(query, {"filter": filter_query}, routing_control=RoutingControl.READ)

        if not result.records:
            return KnowledgeGraph(entities=[], relations=[])

        record = result.records[0]
        nodes = record.get('nodes', list())
        rels = record.get('relations', list())

        entities = [
            Entity(
                name=node['name'],
                operation_type=node['operation_type'],
                node_type=node['node_type'],
                point=node['point'],
                description=node['description'],
                node_description=node['node_description'],
                constraint=self._parse_constraint(node.get('constraint', {})),
                label=node.get('labels', [])
            )
            for node in nodes if node.get('name')
        ]

        relations = [
            Relation(
                source=rel['source'],
                target=rel['target'],
                relationType=rel['relationType'],
                description=rel.get('description', "")  # 从数据库读取描述，如果没有则使用空字符串
            )
            for rel in rels if rel.get('relationType')
        ]

        logger.debug(f"Loaded entities: {entities}")
        logger.debug(f"Loaded relations: {relations}")

        return KnowledgeGraph(entities=entities, relations=relations)

    async def search_memories(self, query: str) -> KnowledgeGraph:
        """Search for memories by name exact match or label contains."""
        logger.info(f"Searching for memories with query: '{query}'")

        # 构建查询：按名称精确匹配或标签包含
        query_cypher = """
        MATCH (e)
        WHERE e.name = $query
           OR ANY(label IN labels(e) WHERE label CONTAINS $query)
        OPTIONAL MATCH (e)-[r]-(other)
        RETURN collect(distinct {
            name: e.name,
            operation_type: e.operation_type,
            node_type: e.node_type,
            point: e.point,
            description: e.description,
            node_description: e.node_description,
            constraint: e.constraint,
            labels: labels(e)
        }) as nodes,
        collect(distinct {
            source: startNode(r).name,
            target: endNode(r).name,
            relationType: type(r),
            description: r.description
        }) as relations
        """

        result = await self.driver.execute_query(
            query_cypher,
            {"query": query},
            routing_control=RoutingControl.READ
        )

        if not result.records:
            return KnowledgeGraph(entities=[], relations=[])

        record = result.records[0]
        nodes = record.get('nodes', list())
        rels = record.get('relations', list())

        entities = [
            Entity(
                name=node['name'],
                operation_type=node['operation_type'],
                node_type=node['node_type'],
                point=node['point'],
                description=node['description'],
                node_description=node['node_description'],
                constraint=self._parse_constraint(node.get('constraint', {})),
                label=node.get('labels', [])
            )
            for node in nodes if node.get('name')
        ]

        relations = [
            Relation(
                source=rel['source'],
                target=rel['target'],
                relationType=rel['relationType'],
                description=rel.get('description', "")  # 从数据库读取描述，如果没有则使用空字符串
            )
            for rel in rels if rel.get('relationType')
        ]

        logger.debug(f"Found entities: {entities}")
        logger.debug(f"Found relations: {relations}")

        return KnowledgeGraph(entities=entities, relations=relations)

    async def create_entities(self, entities: List[Entity]) -> List[Entity]:
      """Create multiple new entities in the knowledge graph with dynamic labels and point increment logic."""
      logger.info(f"Creating {len(entities)} entities")
      created_entities = []

      for entity in entities:
        entity_data = entity.model_dump()

        # 验证并格式化约束数据
        if 'constraint' in entity_data:
            entity_data['constraint'] = self._parse_constraint(entity_data['constraint'])

        # 获取动态标签列表
        labels = entity_data.get('label', [])
        if not labels:
          # 如果没有指定标签，使用默认标签
          labels = ['Memory']

        # 构建标签字符串，支持多个标签
        label_string = '`:`'.join(labels)

        # 检查是否存在相同name和node_type的实体
        check_query = """
        MATCH (e)
        WHERE e.name = $name AND e.node_type = $node_type
        RETURN e.point as current_point
        ORDER BY e.point DESC
        LIMIT 1
        """

        check_result = await self.driver.execute_query(
            check_query,
            {"name": entity_data['name'], "node_type": entity_data['node_type']},
            routing_control=RoutingControl.READ
        )

        old_point = 0  # 默认值改为0

        if check_result.records:
            record = check_result.records[0]
            old_point = record.get('current_point', 0)

            # 如果存在相同name和node_type的实体，point+1
            entity_data['point'] = old_point + 1
            print(f"🔢 发现相同name和node_type的实体，point从{old_point}递增到{entity_data['point']}")
        else:
            # 如果不存在相同name和node_type的实体，保持原始point值
            print(f"🆕 首次创建实体，使用原始point值: {entity_data['point']}")

        # 构建属性设置（排除name和label，因为name用于MERGE，label用于设置标签）
        properties = []
        for key, value in entity_data.items():
          if key not in ['name', 'label']:
            # 如果值是复杂类型（如dict），转换为JSON字符串
            if isinstance(value, dict):
              import json
              entity_data[key] = json.dumps(value, ensure_ascii=False)
            properties.append(f"e.{key} = entity.{key}")

        # 构建查询
        query = f"""
          WITH $entity as entity
          CREATE (e:{labels[0]})
          SET e.name = entity.name
          SET {', '.join(properties) if properties else 'e = e'}
          SET e:`{label_string}`
          """

        await self.driver.execute_query(query, {"entity": entity_data}, routing_control=RoutingControl.WRITE)

        # 如果存在旧实体，创建延伸关系
        if old_point and old_point != 0: # Changed from 1 to 0
            print(f"🔗 创建延伸关系：从{old_point}级到{entity_data['point']}级")
            
            # 直接执行关系创建查询，创建从旧实体到新实体的延伸关系
            extension_query = """
            MATCH (old_entity), (new_entity)
            WHERE old_entity.name = $name AND old_entity.point = $old_point
            AND new_entity.name = $name AND new_entity.point = $new_point
            AND old_entity <> new_entity
            MERGE (old_entity)-[r:延伸]->(new_entity)
            SET r.description = $description
            """
            
            try:
                result = await self.driver.execute_query(
                    extension_query,
                    {
                        "name": entity_data['name'],
                        "old_point": old_point,
                        "new_point": entity_data['point'],
                        "description": f"从{old_point}级延伸到{entity_data['point']}级"
                    },
                    routing_control=RoutingControl.WRITE
                )
                print(f"✅ 延伸关系创建成功：{old_point}级 -> {entity_data['point']}级")
            except Exception as e:
                print(f"❌ 延伸关系创建失败：{e}")

        # 将创建的实体添加到结果列表
        # 需要重新解析constraint字段，因为之前被转换为JSON字符串
        if 'constraint' in entity_data and isinstance(entity_data['constraint'], str):
            try:
                import json
                entity_data['constraint'] = json.loads(entity_data['constraint'])
            except (json.JSONDecodeError, TypeError):
                entity_data['constraint'] = {}

        created_entity = Entity(**entity_data)
        created_entities.append(created_entity)

      return created_entities



    async def create_relations(self, relations: List[Relation]) -> List[Relation]:
        """Create multiple new relations between entities."""
        logger.info(f"Creating {len(relations)} relations")
        for relation in relations:
            query = f"""
            WITH $relation as relation
            MATCH (from),(to)
            WHERE from.name = relation.source
            AND  to.name = relation.target
            MERGE (from)-[r:`{relation.relationType}`]->(to)
            SET r.description = relation.description
            """

            await self.driver.execute_query(
                query,
                {"relation": relation.model_dump()},
                routing_control=RoutingControl.WRITE
            )

        return relations

    async def add_constraint(self, constraint: List[ConstraintAddition]) -> List[Dict[str, Any]]:
        """Add new constraint to existing entities."""
        logger.info(f"Adding constraint to {len(constraint)} entities")

        results = []
        for constraint_item in constraint:
            # 先获取现有约束
            get_query = """
            MATCH (e)
            WHERE e.name = $entityName
            RETURN e.constraint as current_constraint
            """

            get_result = await self.driver.execute_query(
                get_query,
                {"entityName": constraint_item.entityName},
                routing_control=RoutingControl.READ
            )

            if get_result.records:
                record = get_result.records[0]
                current_constraint = self._parse_constraint(record.get('current_constraint', {}))

                # 合并约束
                if isinstance(current_constraint, dict):
                    # 深度合并约束
                    for key, value in constraint_item.constraint.items():
                        if key in current_constraint:
                            # 新的约束格式：值是字符串列表，需要合并列表
                            if isinstance(current_constraint[key], list) and isinstance(value, list):
                                # 合并列表，去重
                                current_constraint[key] = list(set(current_constraint[key] + value))
                            else:
                                # 如果不是列表，直接替换
                                current_constraint[key] = value
                        else:
                            current_constraint[key] = value
                else:
                    current_constraint = constraint_item.constraint

                # 更新约束
                update_query = """
                MATCH (e)
                WHERE e.name = $entityName
                SET e.constraint = $new_constraint
                RETURN e.name as name
                """

                # 转换为JSON字符串存储
                import json
                constraint_json = json.dumps(current_constraint, ensure_ascii=False)

                update_result = await self.driver.execute_query(
                    update_query,
                    {
                        "entityName": constraint_item.entityName,
                        "new_constraint": constraint_json
                    },
                    routing_control=RoutingControl.WRITE
                )

                if update_result.records:
                    results.append({
                        "entityName": constraint_item.entityName,
                        "addedconstraint": constraint_item.constraint
                    })

        return results

    async def delete_entities(self, entity_names: List[str]) -> None:
        """Delete multiple entities and their associated relations."""
        logger.info(f"Deleting {len(entity_names)} entities")
        query = """
        UNWIND $entities as name
        MATCH (e)
        WHERE e.name = name
        DETACH DELETE e
        """

        await self.driver.execute_query(query, {"entities": entity_names}, routing_control=RoutingControl.WRITE)
        logger.info(f"Successfully deleted {len(entity_names)} entities")

    async def delete_constraint(self, deletions: List[ConstraintDeletion]) -> None:
        """Delete specific constraint from entities."""
        logger.info(f"Deleting constraint from {len(deletions)} entities")

        for deletion in deletions:
            # 先获取现有约束
            get_query = """
            MATCH (e)
            WHERE e.name = $entityName
            RETURN e.constraint as current_constraint
            """

            get_result = await self.driver.execute_query(
                get_query,
                {"entityName": deletion.entityName},
                routing_control=RoutingControl.READ
            )

            if get_result.records:
                record = get_result.records[0]
                current_constraint = self._parse_constraint(record.get('current_constraint', {}))

                if isinstance(current_constraint, dict):
                    # 删除指定的约束
                    for key, value in deletion.constraint.items():
                        if key in current_constraint:
                            if isinstance(current_constraint[key], dict) and isinstance(value, dict):
                                # 从嵌套字典中删除指定的键值对
                                for sub_key in value.keys():
                                    if sub_key in current_constraint[key]:
                                        del current_constraint[key][sub_key]
                                # 如果嵌套字典为空，删除整个键
                                if not current_constraint[key]:
                                    del current_constraint[key]
                            else:
                                # 直接删除键值对
                                del current_constraint[key]

                # 更新约束
                update_query = """
                MATCH (e)
                WHERE e.name = $entityName
                SET e.constraint = $new_constraint
                """

                # 转换为JSON字符串存储
                import json
                constraint_json = json.dumps(current_constraint, ensure_ascii=False)

                await self.driver.execute_query(
                    update_query,
                    {
                        "entityName": deletion.entityName,
                        "new_constraint": constraint_json
                    },
                    routing_control=RoutingControl.WRITE
                )

        logger.info(f"Successfully deleted constraint from {len(deletions)} entities")

    async def delete_relations(self, relations: List[Relation]) -> None:
        """Delete multiple relations from the graph."""
        logger.info(f"Deleting {len(relations)} relations")
        for relation in relations:
            query = f"""
            WITH $relation as relation
            MATCH (source)-[r:`{relation.relationType}`]->(target)
            WHERE source.name = relation.source
            AND target.name = relation.target
            DELETE r
            """
            await self.driver.execute_query(
                query,
                {"relation": relation.model_dump()},
                routing_control=RoutingControl.WRITE
            )
        logger.info(f"Successfully deleted {len(relations)} relations")

    async def read_graph(self) -> KnowledgeGraph:
        """Read the entire knowledge graph."""
        return await self.load_graph()

    async def find_memories_by_name(self, names: List[str]) -> KnowledgeGraph:
        """Find specific memories by their names. This does not use fulltext search."""
        logger.info(f"Finding {len(names)} memories by name")
        query = """
        MATCH (e)
        WHERE e.name IN $names
        RETURN  e.name as name,
                e.operation_type as operation_type,
                e.node_type as node_type,
                e.point as point,
                e.description as description,
                e.node_description as node_description,
                e.constraint as constraint,
                labels(e) as labels
        """
        result_nodes = await self.driver.execute_query(query, {"names": names}, routing_control=RoutingControl.READ)
        entities: list[Entity] = list()
        for record in result_nodes.records:
            entities.append(Entity(
                name=record['name'],
                operation_type=record['operation_type'],
                node_type=record['node_type'],
                point=record['point'],
                description=record['description'],
                node_description=record['node_description'],
                constraint=self._parse_constraint(record.get('constraint', {})),
                label=record.get('labels', [])
            ))

        # Get relations for found entities
        relations: list[Relation] = list()
        if entities:
            query = """
            MATCH (source)-[r]->(target)
            WHERE source.name IN $names OR target.name IN $names
            RETURN  source.name as source,
                    target.name as target,
                    type(r) as relationType,
                    r.description as description
            """
            result_relations = await self.driver.execute_query(query, {"names": names}, routing_control=RoutingControl.READ)
            for record in result_relations.records:
                relations.append(Relation(
                    source=record["source"],
                    target=record["target"],
                    relationType=record["relationType"],
                    description=record.get("description", "")
                ))

        logger.info(f"Found {len(entities)} entities and {len(relations)} relations")
        return KnowledgeGraph(entities=entities, relations=relations)

