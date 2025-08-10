#!/usr/bin/env python3
"""
快速测试脚本：验证新的 Entity 结构
"""

import asyncio
import json
from src.mcp_neo4j_memory.neo4j_memory import Entity, Relation, ConstraintType

async def test_new_structure():
    """测试新的数据结构"""
    
    print("🧪 测试新的 Entity 结构")
    print("=" * 50)
    
    # 测试 Entity 创建
    print("\n1️⃣ 测试 Entity 创建:")
    try:
        entity = Entity(
            name="测试模块",
            operation_type="READ",
            node_type="测试类型",
            point=3,
            description="这是一个测试模块",
            node_description="测试节点类型",
            constraint={
                ConstraintType.REQUIRED: ["测试条件1", "测试条件2"],
                ConstraintType.FORBIDDEN: ["禁止条件1"]
            },
            label=["测试", "模块", "示例"]
        )
        print(f"✅ Entity 创建成功: {entity.name}")
        print(f"   约束: {json.dumps(entity.constraint, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ Entity 创建失败: {e}")
    
    # 测试 Relation 创建
    print("\n2️⃣ 测试 Relation 创建:")
    try:
        relation = Relation(
            source="源模块",
            target="目标模块",
            relationType="关联",
            description="这是一个测试关系"
        )
        print(f"✅ Relation 创建成功: {relation.source} -> {relation.target}")
    except Exception as e:
        print(f"❌ Relation 创建失败: {e}")
    
    # 测试约束类型枚举
    print("\n3️⃣ 测试约束类型枚举:")
    print(f"   必须: {ConstraintType.REQUIRED}")
    print(f"   禁止: {ConstraintType.FORBIDDEN}")
    
    # 测试默认约束
    print("\n4️⃣ 测试默认约束:")
    try:
        entity_without_constraint = Entity(
            name="无约束模块",
            operation_type="WRITE",
            node_type="基础类型",
            point=1,
            description="没有设置约束的模块",
            node_description="基础节点类型",
            label=["基础", "模块"]
        )
        print(f"✅ 默认约束设置成功: {entity_without_constraint.constraint}")
    except Exception as e:
        print(f"❌ 默认约束设置失败: {e}")
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    asyncio.run(test_new_structure())
