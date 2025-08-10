#!/usr/bin/env python3
"""
示例：使用新的约束结构创建实体和关系

这个示例展示了如何使用新的 Entity 结构，包含约束条件管理。
"""

import asyncio
import json
from typing import List

# 模拟 Neo4j 连接和 MCP 服务器
class MockNeo4jMemory:
    """模拟 Neo4j 内存管理类"""
    
    async def create_entities(self, entities: List[dict]) -> List[dict]:
        """创建实体的模拟实现"""
        print("🔧 创建实体:")
        for entity in entities:
            print(f"  - {entity['name']} ({entity['operation_type']})")
            print(f"    类型: {entity['node_type']}")
            print(f"    级别: {entity['point']}")
            print(f"    描述: {entity['description']}")
            print(f"    节点描述: {entity['node_description']}")
            print(f"    约束: {json.dumps(entity['constraint'], ensure_ascii=False, indent=4)}")
            print(f"    标签: {', '.join(entity['label'])}")
            print()
        return entities
    
    async def create_relations(self, relations: List[dict]) -> List[dict]:
        """创建关系的模拟实现"""
        print("🔗 创建关系:")
        for relation in relations:
            print(f"  - {relation['source']} --[{relation['relationType']}]--> {relation['target']}")
            print(f"    描述: {relation['description']}")
            print()
        return relations
    
    async def add_constraint(self, constraints: List[dict]) -> List[dict]:
        """添加约束的模拟实现"""
        print("📝 添加约束:")
        for constraint in constraints:
            print(f"  - 实体: {constraint['entityName']}")
            print(f"    约束: {json.dumps(constraint['constraint'], ensure_ascii=False, indent=4)}")
            print()
        return constraints

async def main():
    """主函数：演示新的约束结构"""
    
    # 创建模拟的 Neo4j 内存实例
    memory = MockNeo4jMemory()
    
    print("🚀 MCP Neo4j Memory Server - 约束结构示例")
    print("=" * 60)
    
    # 示例 1：创建用户管理模块
    print("\n📋 示例 1：创建用户管理模块")
    print("-" * 40)
    
    user_management_entity = {
        "name": "用户管理",
        "operation_type": "CRUD",
        "node_type": "功能模块",
        "point": 5,
        "description": "用户账户管理功能模块",
        "node_description": "系统核心功能模块",
        "constraint": {
            "必须": ["用户认证", "权限验证", "密码加密"],
            "禁止": ["超级管理员权限", "直接数据库访问"]
        },
        "label": ["核心模块", "安全模块", "用户相关"]
    }
    
    await memory.create_entities([user_management_entity])
    
    # 示例 2：创建权限管理模块
    print("\n📋 示例 2：创建权限管理模块")
    print("-" * 40)
    
    permission_entity = {
        "name": "权限管理",
        "operation_type": "CRUD",
        "node_type": "功能模块",
        "point": 4,
        "description": "系统权限控制功能",
        "node_description": "访问控制模块",
        "constraint": {
            "必须": ["角色定义", "权限分配", "访问日志"],
            "禁止": ["越权操作", "权限泄露"]
        },
        "label": ["安全模块", "权限相关", "审计模块"]
    }
    
    await memory.create_entities([permission_entity])
    
    # 示例 3：创建关系
    print("\n📋 示例 3：创建模块间关系")
    print("-" * 40)
    
    relations = [
        {
            "source": "用户管理",
            "target": "权限管理",
            "relationType": "依赖",
            "description": "用户管理模块依赖权限管理模块进行权限验证"
        },
        {
            "source": "权限管理",
            "target": "用户管理",
            "relationType": "被依赖",
            "description": "权限管理模块被用户管理模块依赖"
        }
    ]
    
    await memory.create_relations(relations)
    
    # 示例 4：添加新约束
    print("\n📋 示例 4：为现有实体添加新约束")
    print("-" * 40)
    
    new_constraints = [
        {
            "entityName": "用户管理",
            "constraint": {
                "必须": ["用户认证", "权限验证", "密码加密", "会话管理"],
                "禁止": ["超级管理员权限", "直接数据库访问", "明文密码存储"]
            }
        }
    ]
    
    await memory.add_constraint(new_constraints)
    
    print("\n✅ 示例完成！")
    print("\n💡 这个新的约束结构允许你：")
    print("  1. 定义必须满足的条件（必须）")
    print("  2. 定义禁止的条件（禁止）")
    print("  3. 为每个实体设置详细的元数据")
    print("  4. 支持中文描述和标签")
    print("  5. 灵活管理约束条件")

if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
