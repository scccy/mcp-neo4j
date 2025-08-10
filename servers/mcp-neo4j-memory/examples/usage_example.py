#!/usr/bin/env python3
"""
MCP Neo4j Memory 工具使用示例

这个脚本展示了如何使用 MCP 工具来创建实体和关系。
"""

import asyncio
import json
from typing import List

# 模拟 Entity 和 Relation 类（在实际使用中会从 mcp_neo4j_memory 导入）
class Entity:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def model_dump(self):
        return {key: getattr(self, key) for key in dir(self) if not key.startswith('_')}

class Relation:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def model_dump(self):
        return {key: getattr(self, key) for key in dir(self) if not key.startswith('_')}

def create_sample_entities() -> List[Entity]:
    """创建示例实体"""
    return [
        Entity(
            name="张三",
            operation_type="创建",
            node_type="人员",
            point=1,
            description="张三是一名高级技术专家",
            node_description="人员是指公司中的员工个体",
            constraint={
                "必须": {"部门": "技术部", "职级": "高级专家"},
                "禁止": {"加班": "超过12小时"},
                "建议": {"技能": "Python, Neo4j, Docker"}
            },
            label=["员工", "技术部", "高级专家", "Python专家"]
        ),
        Entity(
            name="技术部",
            operation_type="创建",
            node_type="部门",
            point=1,
            description="技术部负责公司的技术研发工作",
            node_description="部门是指公司的组织架构单位",
            constraint={
                "必须": {"职责": "技术研发", "汇报对象": "CTO"},
                "禁止": {"外包": "核心业务"},
                "建议": {"技术栈": "现代化技术栈"}
            },
            label=["部门", "技术部", "研发部门"]
        ),
        Entity(
            name="智能客服系统",
            operation_type="创建",
            node_type="系统",
            point=1,
            description="智能客服系统是一个重要的项目",
            node_description="系统是指公司开发的软件系统",
            constraint={
                "必须": {"技术栈": "Python, Neo4j", "架构": "微服务"},
                "禁止": {"部署": "单点故障"},
                "建议": {"监控": "全链路追踪"}
            },
            label=["项目", "系统", "智能客服", "微服务"]
        )
    ]

def create_sample_relations() -> List[Relation]:
    """创建示例关系"""
    return [
        Relation(
            source="张三",
            target="技术部",
            relationType="属于",
            description="张三属于技术部"
        ),
        Relation(
            source="张三",
            target="智能客服系统",
            relationType="参与开发",
            description="张三参与智能客服系统的开发工作"
        ),
        Relation(
            source="技术部",
            target="智能客服系统",
            relationType="负责开发",
            description="技术部负责智能客服系统的开发工作"
        )
    ]

def print_entity_info(entity: Entity):
    """打印实体信息"""
    print(f"\n📋 实体: {entity.name}")
    print(f"   操作类型: {entity.operation_type}")
    print(f"   节点类型: {entity.node_type}")
    print(f"   级别: {entity.point}")
    print(f"   描述: {entity.description}")
    print(f"   节点描述: {entity.node_description}")
    print(f"   标签: {', '.join(entity.label)}")
    
    if entity.constraint:
        print("   约束条件:")
        for constraint_type, conditions in entity.constraint.items():
            print(f"     {constraint_type}: {conditions}")

def print_relation_info(relation: Relation):
    """打印关系信息"""
    print(f"\n🔗 关系: {relation.source} --[{relation.relationType}]--> {relation.target}")
    if relation.description:
        print(f"   描述: {relation.description}")

def main():
    """主函数"""
    print("🚀 MCP Neo4j Memory 工具使用示例")
    print("=" * 50)
    
    # 创建示例实体
    print("\n1️⃣ 创建示例实体")
    entities = create_sample_entities()
    
    for entity in entities:
        print_entity_info(entity)
    
    # 创建示例关系
    print("\n2️⃣ 创建示例关系")
    relations = create_sample_relations()
    
    for relation in relations:
        print_relation_info(relation)
    
    # 展示 JSON 格式
    print("\n3️⃣ JSON 格式示例")
    print("\n实体 JSON:")
    for entity in entities:
        print(json.dumps(entity.model_dump(), ensure_ascii=False, indent=2))
    
    print("\n关系 JSON:")
    for relation in relations:
        print(json.dumps(relation.model_dump(), ensure_ascii=False, indent=2))
    
    # 展示字段要求
    print("\n4️⃣ 字段要求说明")
    print("""
📝 Entity 字段要求:
  必填字段:
    - name: 实体名称（唯一标识，不能为空）
    - operation_type: 操作类型（必须是：创建、更新、删除、查询、分析、其他）
    - node_type: 节点类型（如：员工、部门、项目等）
    - point: 级别（非负整数，相同name+node_type的实体会自动递增）
    - description: 实体名称的中文描述
    - node_description: 节点类型的中文描述
  
  可选字段:
    - constraint: 约束条件（包含必须、禁止、建议等规则）
    - label: Neo4j节点标签列表（如不提供，默认使用['Memory']）

📝 Relation 字段要求:
  必填字段:
    - source: 源实体名称（必须存在于知识图谱中）
    - target: 目标实体名称（必须存在于知识图谱中）
    - relationType: 关系类型（如：包含、属于、影响、延伸等）
  
  可选字段:
    - description: 关系描述（如不提供，默认为空字符串）

⚠️  注意事项:
    - 所有字符串字段不能为空或只包含空白字符
    - operation_type 必须是预定义的值之一
    - point 必须是非负整数
    - 创建关系前，源实体和目标实体必须已存在
    - 系统会自动验证字段值的有效性
    """)

if __name__ == "__main__":
    main()
