#!/usr/bin/env python3
"""
标准pytest测试文件：测试Neo4j Memory系统的所有功能
"""

import pytest
import pytest_asyncio
import os
import json
import asyncio
from typing import List

from neo4j import AsyncGraphDatabase

from src.mcp_neo4j_memory.neo4j_memory import (
    Neo4jMemory, Entity, Relation,
    ConstraintAddition, ConstraintDeletion, KnowledgeGraph
)

# 设置环境变量
os.environ["NEO4J_URI"] = "neo4j://localhost:7687"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"  # 请修改为你的实际密码
os.environ["NEO4J_DATABASE"] = "neo4j"


@pytest_asyncio.fixture
async def neo4j_memory():
    """Neo4j Memory实例fixture"""
    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]

    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    memory = Neo4jMemory(driver)

    # 创建全文搜索索引
    await memory.create_fulltext_index()

    yield memory

    # 清理测试数据 - 关闭数据库连接
    await driver.close()


@pytest.mark.asyncio
async def clear_database():
    """清空数据库中的所有数据"""
    print("🧹 开始清空Neo4j数据库...")

    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]

    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    try:
        # 删除所有节点和关系
        query = "MATCH (n) DETACH DELETE n"
        await driver.execute_query(query, routing_control="WRITE")
        print("✅ 已删除所有节点和关系")

        # 删除所有索引
        query = "SHOW INDEXES"
        result = await driver.execute_query(query, routing_control="READ")

        for record in result.records:
            index_name = record.get('name')
            if index_name:
                try:
                    drop_query = f"DROP INDEX {index_name}"
                    await driver.execute_query(drop_query, routing_control="WRITE")
                    print(f"🗑️  已删除索引: {index_name}")
                except Exception as e:
                    print(f"⚠️  删除索引 {index_name} 失败: {e}")

        print("✅ 数据库清空完成！")

    except Exception as e:
        print(f"❌ 清空数据库时出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await driver.close()
        print("🔌 数据库连接已关闭")


@pytest.fixture
def test_entities() -> List[Entity]:
    """测试实体数据"""
    return [
        Entity(
            name="张三",
            operation_type="技术专家",
            node_type="人员",
            point=1,
            description="张三是一名高级技术专家",
            node_description="人员是指公司中的员工个体",
            constraint={
                "必须": ["部门:技术部", "职级:高级专家", "技能:Python", "技能:Neo4j", "技能:Docker"],
                "禁止": ["加班:超过12小时"]
            },
            label=["员工", "技术部", "高级专家", "Python专家"]
        ),
        Entity(
            name="李四",
            operation_type="产品经理",
            node_type="人员",
            point=2,
            description="李四是一名产品经理",
            node_description="人员是指公司中的员工个体",
            constraint={
                "必须": ["部门:产品部", "职级:产品经理", "技能:产品设计", "技能:用户研究"],
                "禁止": ["决策:未经调研"]
            },
            label=["员工", "产品部", "产品经理", "用户研究专家"]
        ),
        Entity(
            name="智能客服系统",
            operation_type="项目",
            node_type="系统",
            point=1,
            description="智能客服系统是一个重要的项目",
            node_description="系统是指公司开发的软件系统",
            constraint={
                "必须": ["技术栈:Python", "技术栈:Neo4j", "架构:微服务", "监控:全链路追踪"],
                "禁止": ["部署:单点故障"]
            },
            label=["项目", "系统", "智能客服", "微服务"]
        )
    ]


@pytest.fixture
def test_relations() -> List[Relation]:
    """测试关系数据"""
    return [
        Relation(
            source="张三",
            target="智能客服系统",
            relationType="参与开发",
            description="张三参与智能客服系统的开发工作"
        ),
        Relation(
            source="李四",
            target="智能客服系统",
            relationType="产品管理",
            description="李四负责智能客服系统的产品管理工作"
        )
    ]


class TestNeo4jMemory:
    """Neo4j Memory功能测试类"""

    @pytest.mark.asyncio
    async def test_create_entities(self, neo4j_memory, test_entities):
        """测试实体创建功能"""
        print("\n🧪 测试1: 实体创建功能")

        # 创建测试实体
        for entity in test_entities:
            result = await neo4j_memory.create_entities([entity])
            assert result is not None
            print(f"✅ 成功创建实体: {entity.name}")

        # 验证实体是否创建成功
        for entity in test_entities:
            search_result = await neo4j_memory.search_memories(entity.name)
            assert search_result is not None
            assert len(search_result.entities) > 0

    @pytest.mark.asyncio
    async def test_create_relations(self, neo4j_memory, test_relations):
        """测试关系创建功能"""
        print("\n🧪 测试2: 关系创建功能")

        # 创建测试关系
        for relation in test_relations:
            result = await neo4j_memory.create_relations([relation])
            assert result is not None
            print(f"✅ 成功创建关系: {relation.source} -> {relation.target}")

        # 验证关系是否创建成功
        for relation in test_relations:
            search_result = await neo4j_memory.search_memories(relation.source)
            assert search_result is not None

    @pytest.mark.asyncio
    async def test_search_memories(self, neo4j_memory):
        """测试记忆搜索功能"""
        print("\n🧪 测试3: 记忆搜索功能")

        # 测试精确搜索
        result = await neo4j_memory.search_memories("张三")
        assert result is not None
        print(f"✅ 精确搜索成功: 找到 {len(result.entities)} 条结果")

        # 测试模糊搜索
        result = await neo4j_memory.search_memories("技术")
        assert result is not None
        print(f"✅ 模糊搜索成功: 找到 {len(result.entities)} 条结果")

    @pytest.mark.asyncio
    async def test_find_memories_by_name(self, neo4j_memory):
        """测试按名称查找记忆功能"""
        print("\n🧪 测试4: 按名称查找记忆功能")

        names = ["张三", "李四", "智能客服系统"]
        result = await neo4j_memory.find_memories_by_name(names)
        assert result is not None
        print(f"✅ 按名称查找成功: 找到 {len(result.entities)} 条结果")

    @pytest.mark.asyncio
    async def test_read_graph(self, neo4j_memory):
        """测试读取图谱功能"""
        print("\n🧪 测试5: 读取图谱功能")

        result = await neo4j_memory.read_graph()
        assert result is not None
        print(f"✅ 读取图谱成功: 包含 {len(result.entities)} 个实体和 {len(result.relations)} 个关系")

    @pytest.mark.asyncio
    async def test_add_constraint(self, neo4j_memory):
        """测试添加约束功能"""
        print("\n🧪 测试6: 添加约束功能")

        constraint = ConstraintAddition(
            entityName="张三",
            constraint={
                "必须": ["技能:机器学习"]
            }
        )

        result = await neo4j_memory.add_constraint([constraint])
        assert result is not None
        print("✅ 添加约束成功")

    @pytest.mark.asyncio
    async def test_delete_constraint(self, neo4j_memory):
        """测试删除约束功能"""
        print("\n🧪 测试7: 删除约束功能")

        constraint = ConstraintDeletion(
            entityName="张三",
            constraint={
                "必须": ["技能:机器学习"]
            }
        )

        result = await neo4j_memory.delete_constraint([constraint])
        assert result is None  # delete_constraint返回None
        print("✅ 删除约束成功")

    @pytest.mark.asyncio
    async def test_delete_relations(self, neo4j_memory):
        """测试删除关系功能"""
        print("\n🧪 测试8: 删除关系功能")

        # 先创建一些测试关系
        test_relation = Relation(
            source="测试源",
            target="测试目标",
            relationType="测试关系",
            description="用于测试删除的关系"
        )

        await neo4j_memory.create_relations([test_relation])

        # 删除关系
        result = await neo4j_memory.delete_relations([test_relation])
        assert result is None  # delete_relations返回None
        print("✅ 删除关系成功")

    @pytest.mark.asyncio
    async def test_delete_entities(self, neo4j_memory):
        """测试删除实体功能"""
        print("\n🧪 测试9: 删除实体功能")

        # 先创建一些测试实体
        test_entity = Entity(
            name="测试实体",
            operation_type="测试",
            node_type="测试",
            point=1,
            description="用于测试删除的实体",
            node_description="测试实体",
            constraint={},
            label=["测试"]
        )

        await neo4j_memory.create_entities([test_entity])

        # 删除实体
        result = await neo4j_memory.delete_entities([test_entity.name])
        assert result is None  # delete_entities返回None
        print("✅ 删除实体成功")

    @pytest.mark.asyncio
    async def test_load_graph_with_filter(self, neo4j_memory):
        """测试带过滤器的图谱加载功能"""
        print("\n🧪 测试10: 带过滤器的图谱加载功能")

        # 测试带过滤器的图谱加载
        result = await neo4j_memory.load_graph("张三")
        assert result is not None
        print(f"✅ 带过滤器图谱加载成功: 找到 {len(result.entities)} 个实体")

    @pytest.mark.asyncio
    async def test_search_memories_empty_query(self, neo4j_memory):
        """测试空查询的搜索功能"""
        print("\n🧪 测试11: 空查询搜索功能")

        # 测试空查询
        result = await neo4j_memory.search_memories("")
        assert result is not None
        print(f"✅ 空查询搜索成功: 找到 {len(result.entities)} 个实体")

    @pytest.mark.asyncio
    async def test_create_entities_empty_list(self, neo4j_memory):
        """测试创建空实体列表"""
        print("\n🧪 测试12: 创建空实体列表")

        # 测试空列表
        result = await neo4j_memory.create_entities([])
        assert result == []
        print("✅ 空实体列表创建成功")

    @pytest.mark.asyncio
    async def test_create_relations_empty_list(self, neo4j_memory):
        """测试创建空关系列表"""
        print("\n🧪 测试13: 创建空关系列表")

        # 测试空列表
        result = await neo4j_memory.create_relations([])
        assert result == []
        print("✅ 空关系列表创建成功")

    @pytest.mark.asyncio
    async def test_find_memories_by_name_empty_list(self, neo4j_memory):
        """测试按空名称列表查找记忆"""
        print("\n🧪 测试14: 按空名称列表查找记忆")

        # 测试空名称列表
        result = await neo4j_memory.find_memories_by_name([])
        assert result is not None
        assert len(result.entities) == 0
        print("✅ 空名称列表查找成功")

    @pytest.mark.asyncio
    async def test_constraint_operations_edge_cases(self, neo4j_memory):
        """测试约束操作的边界情况"""
        print("\n🧪 测试15: 约束操作边界情况")

        # 测试空约束
        constraint_add = ConstraintAddition(
            entityName="张三",
            constraint={}
        )

        result = await neo4j_memory.add_constraint([constraint_add])
        assert result is not None
        print("✅ 空约束添加成功")

        # 测试复杂约束结构
        complex_constraint = ConstraintAddition(
            entityName="张三",
            constraint={
                "必须": ["技能:Python", "经验:5年", "认证:AWS", "认证:Docker"],
                "禁止": ["加班:超过12小时"]
            }
        )

        result = await neo4j_memory.add_constraint([complex_constraint])
        assert result is not None
        print("✅ 复杂约束添加成功")

    @pytest.mark.asyncio
    async def test_entity_with_special_characters(self, neo4j_memory):
        """测试包含特殊字符的实体"""
        print("\n🧪 测试16: 特殊字符实体测试")

        special_entity = Entity(
            name="测试@#$%^&*()",
            operation_type="特殊测试",
            node_type="特殊节点",
            point=1,
            description="包含特殊字符的实体",
            node_description="特殊节点描述",
            constraint={"必须": ["字符:!@#$%^&*()"]},
            label=["特殊", "测试", "字符"]
        )

        result = await neo4j_memory.create_entities([special_entity])
        assert result is not None
        assert len(result) == 1
        print("✅ 特殊字符实体创建成功")

        # 清理测试数据
        await neo4j_memory.delete_entities([special_entity.name])

    @pytest.mark.asyncio
    async def test_relation_with_special_characters(self, neo4j_memory):
        """测试包含特殊字符的关系"""
        print("\n🧪 测试17: 特殊字符关系测试")

        special_relation = Relation(
            source="源@#$%",
            target="目标^&*()",
            relationType="特殊关系@#$%",
            description="包含特殊字符的关系描述"
        )

        result = await neo4j_memory.create_relations([special_relation])
        assert result is not None
        assert len(result) == 1
        print("✅ 特殊字符关系创建成功")

        # 清理测试数据
        await neo4j_memory.delete_relations([special_relation])

    @pytest.mark.asyncio
    async def test_large_constraint_data(self, neo4j_memory):
        """测试大量约束数据"""
        print("\n🧪 测试18: 大量约束数据测试")

        # 创建包含大量约束的实体
        large_constraint = {"必须": [], "禁止": []}
        for i in range(50):
            large_constraint["必须"].append(f"约束{i}:值{i}")
        for i in range(50):
            large_constraint["禁止"].append(f"约束{i}:值{i}")

        large_entity = Entity(
            name="大量约束实体",
            operation_type="约束测试",
            node_type="测试节点",
            point=1,
            description="包含大量约束的实体",
            node_description="测试节点描述",
            constraint=large_constraint,
            label=["大量约束", "测试", "性能"]
        )

        result = await neo4j_memory.create_entities([large_entity])
        assert result is not None
        assert len(result) == 1
        print("✅ 大量约束实体创建成功")

        # 清理测试数据
        await neo4j_memory.delete_entities([large_entity.name])

    @pytest.mark.asyncio
    async def test_entity_point_default_value(self, neo4j_memory):
        """测试 Entity 的 point 字段默认值功能"""
        print("\n🧪 测试19: Entity point 字段默认值功能")

        # 创建不指定 point 值的实体（应该使用默认值 0）
        entity_without_point = Entity(
            name="默认Point实体",
            operation_type="测试",
            node_type="测试类型",
            point=0,  # 明确指定默认值
            description="测试默认point值的实体",
            node_description="测试类型描述",
            constraint={},
            label=["测试", "默认值"]
        )

        result = await neo4j_memory.create_entities([entity_without_point])
        assert result is not None
        assert len(result) == 1
        assert result[0].point == 0  # 应该使用默认值 0
        print(f"✅ 默认point值测试成功，point: {result[0].point}")

        # 清理测试数据
        await neo4j_memory.delete_entities([entity_without_point.name])

    @pytest.mark.asyncio
    async def test_create_entities_duplicate_name_node_type(self, neo4j_memory):
        """测试创建相同name和node_type的实体时的point递增逻辑"""
        print("\n🧪 测试20: 相同name和node_type的实体point递增逻辑")

        # 创建第一个实体
        entity1 = Entity(
            name="测试实体",
            operation_type="测试",
            node_type="测试类型",
            point=5,
            description="第一个测试实体",
            node_description="测试类型描述",
            constraint={},
            label=["测试"]
        )

        result1 = await neo4j_memory.create_entities([entity1])
        assert result1 is not None
        assert len(result1) == 1
        assert result1[0].point == 5  # 第一个实体保持原始point值
        print(f"✅ 第一个实体创建成功，point: {result1[0].point}")

        # 创建相同name和node_type的第二个实体
        entity2 = Entity(
            name="测试实体",  # 相同的name
            operation_type="测试",
            node_type="测试类型",  # 相同的node_type
            point=10,  # 这个point应该被忽略，系统会自动递增为6
            description="第二个测试实体",
            node_description="测试类型描述",
            constraint={},
            label=["测试"]
        )

        result2 = await neo4j_memory.create_entities([entity2])
        assert result2 is not None
        assert len(result2) == 1
        # 由于存在相同name和node_type的实体，point应该自动递增为6 (5+1)
        assert result2[0].point == 6
        print(f"✅ 第二个实体创建成功，point自动递增为: {result2[0].point}")

        # 创建第三个相同name和node_type的实体
        entity3 = Entity(
            name="测试实体",  # 相同的name
            operation_type="测试",
            node_type="测试类型",  # 相同的node_type
            point=20,  # 这个point应该被忽略，系统会自动递增为7
            description="第三个测试实体",
            node_description="测试类型描述",
            constraint={},
            label=["测试"]
        )

        result3 = await neo4j_memory.create_entities([entity3])
        assert result3 is not None
        assert len(result3) == 1
        # point应该自动递增为7 (6+1)
        assert result3[0].point == 7
        print(f"✅ 第三个实体创建成功，point自动递增为: {result3[0].point}")

        # 验证数据库中确实存在三个不同point值的实体
        search_result = await neo4j_memory.search_memories("测试实体")
        assert search_result is not None
        assert len(search_result.entities) == 3

        # 检查point值是否正确
        points = [entity.point for entity in search_result.entities]
        points.sort()
        assert points == [5, 6, 7]
        print(f"✅ 验证成功：数据库中存在point值为 {points} 的三个实体")

        # 清理测试数据
        await neo4j_memory.delete_entities([entity1.name, entity2.name, entity3.name])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
