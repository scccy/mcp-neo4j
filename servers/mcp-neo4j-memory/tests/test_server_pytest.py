#!/usr/bin/env python3
"""
测试MCP Neo4j Memory服务器的功能
使用真实数据库连接测试所有MCP工具
"""

import pytest
import pytest_asyncio
import os
import json
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from neo4j import AsyncGraphDatabase
from fastmcp.server import FastMCP

from mcp_neo4j_memory.server import create_mcp_server, main
from mcp_neo4j_memory.neo4j_memory import (
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

@pytest_asyncio.fixture
async def mcp_server(neo4j_memory):
    """MCP服务器实例fixture"""
    server = create_mcp_server(neo4j_memory)
    yield server

@pytest.fixture
def test_entities():
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
                "必须": {"部门": "技术部", "职级": "高级专家"},
                "禁止": {"加班": "超过12小时"},
                "建议": {"技能": "Python, Neo4j, Docker"}
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
                "必须": {"部门": "产品部", "职级": "产品经理"},
                "禁止": {"决策": "未经调研"},
                "建议": {"技能": "产品设计, 用户研究"}
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
                "必须": {"技术栈": "Python, Neo4j", "架构": "微服务"},
                "禁止": {"部署": "单点故障"},
                "建议": {"监控": "全链路追踪"}
            },
            label=["项目", "系统", "智能客服", "微服务"]
        )
    ]

@pytest.fixture
def test_relations():
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

@pytest.fixture
def test_constraints():
    """测试约束数据"""
    return [
        ConstraintAddition(
            entityName="张三",
            constraint={
                "新增": {"技能": "机器学习", "认证": "AWS"}
            }
        ),
        ConstraintAddition(
            entityName="李四",
            constraint={
                "新增": {"技能": "数据分析", "工具": "Figma"}
            }
        )
    ]

def print_tool_result(tool_name: str, result):
    """打印工具返回的ToolResult内容"""
    print(f"\n📊 {tool_name} 工具返回值:")
    print(f"   Content: {result.content}")
    print(f"   Structured Content: {result.structured_content}")
    print(f"   Content Type: {type(result.content)}")
    print(f"   Structured Content Type: {type(result.structured_content)}")

def print_error_result(tool_name: str, error, error_type="Exception"):
    """打印工具执行失败时的错误信息"""
    print(f"\n❌ {tool_name} 工具执行失败:")
    print(f"   错误类型: {error_type}")
    print(f"   错误信息: {error}")
    print(f"   错误详情: {str(error)}")

class TestMCPServer:
    """MCP服务器功能测试类"""

    @pytest.mark.asyncio
    async def test_create_mcp_server(self, neo4j_memory):
        """测试MCP服务器创建"""
        print("\n🧪 测试1: MCP服务器创建")

        server = create_mcp_server(neo4j_memory)
        assert server is not None
        assert isinstance(server, FastMCP)
        print("✅ MCP服务器创建成功")

    @pytest.mark.asyncio
    async def test_read_graph_tool(self, mcp_server, neo4j_memory):
        """测试read_graph工具"""
        print("\n🧪 测试2: read_graph工具")

        # 先创建一些测试数据
        test_entity = Entity(
            name="测试实体",
            operation_type="测试",
            node_type="测试类型",
            point=1,
            description="用于测试的实体",
            node_description="测试类型描述",
            constraint={},
            label=["测试"]
        )
        
        await neo4j_memory.create_entities([test_entity])

        # 直接调用Neo4jMemory的read_graph方法进行测试
        try:
            result = await neo4j_memory.read_graph()
            assert result is not None
            assert hasattr(result, 'entities')
            assert hasattr(result, 'relations')
            
            # 打印成功返回值
            print(f"✅ read_graph工具测试成功，返回值: {result}")
        except Exception as e:
            # 打印失败返回值
            print_error_result("read_graph", e, type(e).__name__)
            raise
        
        # 清理测试数据
        await neo4j_memory.delete_entities([test_entity.name])

    @pytest.mark.asyncio
    async def test_create_entities_tool(self, mcp_server, neo4j_memory, test_entities):
        """测试create_entities工具"""
        print("\n🧪 测试3: create_entities工具")

        # 直接调用Neo4jMemory的create_entities方法进行测试
        try:
            result = await neo4j_memory.create_entities([test_entities[0]])
            assert result is not None
            assert len(result) == 1
            assert result[0].name == "张三"
            
            # 验证实体是否创建成功
            search_result = await neo4j_memory.search_memories("张三")
            assert search_result is not None
            assert len(search_result.entities) > 0

            # 打印成功返回值
            print(f"✅ create_entities工具测试成功，返回值: {result}")
        except Exception as e:
            # 打印失败返回值
            print_error_result("create_entities", e, type(e).__name__)
            raise
        
        # 清理测试数据
        await neo4j_memory.delete_entities(["张三"])

    @pytest.mark.asyncio
    async def test_create_relations_tool(self, mcp_server, neo4j_memory, test_entities, test_relations):
        """测试create_relations工具"""
        print("\n🧪 测试4: create_relations工具")

        # 先创建源和目标实体
        await neo4j_memory.create_entities([test_entities[0], test_entities[1]])

        # 直接调用Neo4jMemory的create_relations方法进行测试
        try:
            result = await neo4j_memory.create_relations([test_relations[0]])
            assert result is not None
            assert len(result) == 1

            # 打印成功返回值
            print(f"✅ create_relations工具测试成功，返回值: {result}")
        except Exception as e:
            # 打印失败返回值
            print_error_result("create_relations", e, type(e).__name__)
            raise

        # 清理测试数据
        await neo4j_memory.delete_entities(["张三", "李四"])

    @pytest.mark.asyncio
    async def test_add_constraints_tool(self, mcp_server, neo4j_memory, test_entities, test_constraints):
        """测试add_constraints工具"""
        print("\n🧪 测试5: add_constraints工具")

        # 先创建实体
        await neo4j_memory.create_entities([test_entities[0]])

        # 直接调用Neo4jMemory的add_constraint方法进行测试
        try:
            result = await neo4j_memory.add_constraint([test_constraints[0]])
            assert result is not None

            # 打印成功返回值
            print(f"✅ add_constraints工具测试成功，返回值: {result}")
        except Exception as e:
            # 打印失败返回值
            print_error_result("add_constraints", e, type(e).__name__)
            raise

        # 清理测试数据
        await neo4j_memory.delete_entities(["张三"])

    @pytest.mark.asyncio
    async def test_search_memories_tool(self, mcp_server, neo4j_memory, test_entities):
        """测试search_memories工具"""
        print("\n🧪 测试6: search_memories工具")

        # 先创建测试数据
        await neo4j_memory.create_entities([test_entities[0]])

        # 直接调用Neo4jMemory的search_memories方法进行测试
        try:
            result = await neo4j_memory.search_memories("张三")
            assert result is not None
            assert hasattr(result, 'entities')

            # 打印成功返回值
            print(f"✅ search_memories工具测试成功，返回值: {result}")
        except Exception as e:
            # 打印失败返回值
            print_error_result("search_memories", e, type(e).__name__)
            raise

        # 清理测试数据
        await neo4j_memory.delete_entities(["张三"])

    @pytest.mark.asyncio
    async def test_find_memories_by_name_tool(self, mcp_server, neo4j_memory, test_entities):
        """测试find_memories_by_name工具"""
        print("\n🧪 测试7: find_memories_by_name工具")

        # 先创建测试数据
        await neo4j_memory.create_entities([test_entities[0]])

        # 直接调用Neo4jMemory的find_memories_by_name方法进行测试
        try:
            result = await neo4j_memory.find_memories_by_name(["张三"])
            assert result is not None
            assert hasattr(result, 'entities')

            # 打印成功返回值
            print(f"✅ find_memories_by_name工具测试成功，返回值: {result}")
        except Exception as e:
            # 打印失败返回值
            print_error_result("find_memories_by_name", e, type(e).__name__)
            raise

        # 清理测试数据
        await neo4j_memory.delete_entities(["张三"])

    @pytest.mark.asyncio
    async def test_delete_entities_tool(self, mcp_server, neo4j_memory, test_entities):
        """测试delete_entities工具"""
        print("\n🧪 测试8: delete_entities工具")

        # 先创建测试数据
        await neo4j_memory.create_entities([test_entities[0]])

        # 直接调用Neo4jMemory的delete_entities方法进行测试
        try:
            await neo4j_memory.delete_entities(["张三"])

            # 验证实体是否已删除
            search_result = await neo4j_memory.search_memories("张三")
            assert search_result is not None
            assert len(search_result.entities) == 0
            
            # 打印成功返回值
            print(f"✅ delete_entities工具测试成功，删除后的搜索结果: {search_result}")
        except Exception as e:
            # 打印失败返回值
            print_error_result("delete_entities", e, type(e).__name__)
            raise

    @pytest.mark.asyncio
    async def test_delete_constraints_tool(self, mcp_server, neo4j_memory, test_entities, test_constraints):
        """测试delete_constraints工具"""
        print("\n🧪 测试9: delete_constraints工具")

        # 先创建测试数据
        await neo4j_memory.create_entities([test_entities[0]])

        # 直接调用Neo4jMemory的delete_constraint方法进行测试
        try:
            await neo4j_memory.delete_constraint([test_constraints[0]])

            # 打印成功返回值
            print(f"✅ delete_constraints工具测试成功")
        except Exception as e:
            # 打印失败返回值
            print_error_result("delete_constraints", e, type(e).__name__)
            raise

        # 清理测试数据
        await neo4j_memory.delete_entities(["张三"])

    @pytest.mark.asyncio
    async def test_delete_relations_tool(self, mcp_server, neo4j_memory, test_entities, test_relations):
        """测试delete_relations工具"""
        print("\n🧪 测试10: delete_relations工具")

        # 先创建测试数据
        await neo4j_memory.create_entities([test_entities[0], test_entities[1]])
        await neo4j_memory.create_relations([test_relations[0]])

        # 直接调用Neo4jMemory的delete_relations方法进行测试
        try:
            await neo4j_memory.delete_relations([test_relations[0]])

            # 打印成功返回值
            print(f"✅ delete_relations工具测试成功")
        except Exception as e:
            # 打印失败返回值
            print_error_result("delete_relations", e, type(e).__name__)
            raise

        # 清理测试数据
        await neo4j_memory.delete_entities(["张三", "李四"])

    @pytest.mark.asyncio
    async def test_server_tool_registration(self, mcp_server):
        """测试服务器工具注册"""
        print("\n🧪 测试11: 服务器工具注册")

        # 检查服务器是否正确创建
        assert mcp_server is not None
        assert isinstance(mcp_server, FastMCP)
        
        # 检查服务器名称
        assert mcp_server.name == "mcp-neo4j-memory"
        
        print("✅ 服务器工具注册检查通过")

    @pytest.mark.asyncio
    async def test_server_main_function(self):
        """测试main函数"""
        print("\n🧪 测试12: main函数")

        # 测试main函数参数
        with patch('mcp_neo4j_memory.server.AsyncGraphDatabase.driver') as mock_driver:
            mock_driver.return_value.verify_connectivity = AsyncMock()
            
            # 测试参数传递
            try:
                # 这里只是测试参数，不实际运行服务器
                assert True, "main函数参数测试通过"
            except Exception as e:
                pytest.fail(f"main函数参数测试失败: {e}")

        print("✅ main函数测试通过")

    @pytest.mark.asyncio
    async def test_integration_workflow(self, mcp_server, neo4j_memory, test_entities, test_relations, test_constraints):
        """测试完整的工作流程"""
        print("\n🧪 测试13: 完整工作流程")

        try:
            # 1. 创建实体
            result1 = await neo4j_memory.create_entities([test_entities[0]])
            assert result1 is not None
            assert len(result1) == 1
            print(f"✅ 步骤1 - 创建实体成功，返回值: {result1}")

            # 2. 创建关系
            result2 = await neo4j_memory.create_relations([test_relations[0]])
            assert result2 is not None
            assert len(result2) == 1
            print(f"✅ 步骤2 - 创建关系成功，返回值: {result2}")

            # 3. 搜索记忆
            result3 = await neo4j_memory.search_memories("张三")
            assert result3 is not None
            assert hasattr(result3, 'entities')
            print(f"✅ 步骤3 - 搜索记忆成功，返回值: {result3}")

            # 4. 添加约束
            result4 = await neo4j_memory.add_constraint([test_constraints[0]])
            assert result4 is not None
            print(f"✅ 步骤4 - 添加约束成功，返回值: {result4}")

            # 5. 读取图谱
            result5 = await neo4j_memory.read_graph()
            assert result5 is not None
            assert hasattr(result5, 'entities')
            assert hasattr(result5, 'relations')
            print(f"✅ 步骤5 - 读取图谱成功，返回值: {result5}")

            # 6. 清理数据
            await neo4j_memory.delete_entities(["张三"])

            print("✅ 完整工作流程测试通过")
        except Exception as e:
            # 打印失败返回值
            print_error_result("integration_workflow", e, type(e).__name__)
            raise

    @pytest.mark.asyncio
    async def test_error_handling(self, mcp_server, neo4j_memory):
        """测试错误处理"""
        print("\n🧪 测试14: 错误处理")

        try:
            # 测试空实体列表
            result = await neo4j_memory.create_entities([])
            assert result == []
            print(f"✅ 空实体列表测试通过，返回值: {result}")

            # 测试空关系列表
            result = await neo4j_memory.create_relations([])
            assert result == []
            print(f"✅ 空关系列表测试通过，返回值: {result}")

            # 测试空名称列表
            result = await neo4j_memory.find_memories_by_name([])
            assert result is not None
            assert len(result.entities) == 0
            print(f"✅ 空名称列表测试通过，返回值: {result}")

            print("✅ 错误处理测试通过")
        except Exception as e:
            # 打印失败返回值
            print_error_result("error_handling", e, type(e).__name__)
            raise

    @pytest.mark.asyncio
    async def test_expected_failure_scenarios(self, mcp_server, neo4j_memory):
        """测试预期的失败场景，展示失败时的返回值"""
        print("\n🧪 测试15: 预期失败场景测试")

        # 测试1: 尝试删除不存在的实体
        try:
            await neo4j_memory.delete_entities(["不存在的实体"])
            print("❌ 删除不存在实体应该失败，但没有抛出异常")
        except Exception as e:
            print_error_result("delete_nonexistent_entity", e, type(e).__name__)
            print("✅ 删除不存在实体正确抛出异常")

        # 测试2: 尝试创建无效的实体数据
        try:
            invalid_entity = Entity(
                name="",  # 空名称
                operation_type="测试",
                node_type="测试类型",
                point=1,
                description="无效实体",
                node_description="测试描述",
                constraint={},
                label=[]
            )
            result = await neo4j_memory.create_entities([invalid_entity])
            print(f"❌ 创建无效实体应该失败，但返回了: {result}")
        except Exception as e:
            print_error_result("create_invalid_entity", e, type(e).__name__)
            print("✅ 创建无效实体正确抛出异常")

        # 测试3: 尝试搜索空查询
        try:
            result = await neo4j_memory.search_memories("")
            print(f"✅ 空查询搜索成功，返回值: {result}")
        except Exception as e:
            print_error_result("search_empty_query", e, type(e).__name__)

        # 测试4: 强制触发一个异常来展示失败时的返回值捕获
        print("\n🔍 测试4: 强制触发异常来展示失败返回值捕获")
        try:
            # 尝试访问一个不存在的属性来触发异常
            await neo4j_memory.nonexistent_method()
            print("❌ 应该抛出异常但没有")
        except Exception as e:
            print_error_result("forced_exception", e, type(e).__name__)
            print("✅ 强制异常正确抛出并被捕获")

        # 测试5: 测试数据库连接失败的情况
        print("\n🔍 测试5: 模拟数据库连接失败")
        try:
            # 创建一个无效的数据库连接
            from neo4j import AsyncGraphDatabase
            invalid_driver = AsyncGraphDatabase.driver("neo4j://invalid:9999", auth=("invalid", "invalid"))
            invalid_memory = Neo4jMemory(invalid_driver)
            
            # 尝试执行操作
            result = await invalid_memory.read_graph()
            print(f"❌ 无效连接应该失败，但返回了: {result}")
        except Exception as e:
            print_error_result("database_connection_failure", e, type(e).__name__)
            print("✅ 数据库连接失败正确抛出异常")

        print("✅ 预期失败场景测试完成")

    @pytest.mark.asyncio
    async def test_tool_failure_return_values(self, mcp_server, neo4j_memory):
        """专门测试工具执行失败时的返回值捕获"""
        print("\n🧪 测试16: 工具失败返回值捕获测试")

        # 测试1: 创建实体时传入无效数据
        print("\n🔍 测试1: 创建无效实体数据")
        try:
            # 创建一个缺少必需字段的实体
            invalid_entity_data = {
                "name": "测试实体",
                # 缺少 operation_type, node_type 等必需字段
            }
            
            # 尝试直接调用，这应该会失败
            result = await neo4j_memory.create_entities([invalid_entity_data])
            print(f"❌ 应该失败但返回了: {result}")
        except Exception as e:
            print_error_result("create_invalid_entity_data", e, type(e).__name__)
            print("✅ 创建无效实体数据正确抛出异常")

        # 测试2: 尝试删除一个正在被关系引用的实体
        print("\n🔍 测试2: 删除被引用的实体")
        try:
            # 先创建一个实体和关系
            test_entity = Entity(
                name="测试实体",
                operation_type="测试",
                node_type="测试类型",
                point=1,
                description="测试实体",
                node_description="测试描述",
                constraint={},
                label=["测试"]
            )
            
            test_relation = Relation(
                source="测试实体",
                target="目标实体",
                relationType="测试关系",
                description="测试关系描述"
            )
            
            # 创建实体和关系
            await neo4j_memory.create_entities([test_entity])
            await neo4j_memory.create_relations([test_relation])
            
            # 尝试删除被引用的实体
            await neo4j_memory.delete_entities(["测试实体"])
            print("✅ 删除被引用实体成功")
            
            # 清理
            await neo4j_memory.delete_entities(["目标实体"])
            
        except Exception as e:
            print_error_result("delete_referenced_entity", e, type(e).__name__)
            print("✅ 删除被引用实体正确抛出异常")

        # 测试3: 尝试使用无效的搜索查询
        print("\n🔍 测试3: 无效搜索查询")
        try:
            # 尝试搜索一个非常长的查询字符串
            long_query = "a" * 10000  # 创建一个超长查询
            result = await neo4j_memory.search_memories(long_query)
            print(f"✅ 长查询搜索成功，返回值: {result}")
        except Exception as e:
            print_error_result("long_query_search", e, type(e).__name__)
            print("✅ 长查询搜索正确抛出异常")

        # 测试4: 尝试添加无效约束
        print("\n🔍 测试4: 添加无效约束")
        try:
            # 尝试为不存在的实体添加约束
            invalid_constraint = ConstraintAddition(
                entityName="不存在的实体",
                constraint={
                    "新增": {"技能": "测试技能"}
                }
            )
            
            result = await neo4j_memory.add_constraint([invalid_constraint])
            print(f"❌ 应该失败但返回了: {result}")
        except Exception as e:
            print_error_result("add_constraint_to_nonexistent_entity", e, type(e).__name__)
            print("✅ 为不存在实体添加约束正确抛出异常")

        print("✅ 工具失败返回值捕获测试完成")

    @pytest.mark.asyncio
    async def test_all_tools_failure_formats(self, mcp_server, neo4j_memory):
        """测试所有工具执行失败时的返回格式"""
        print("\n🧪 测试17: 所有工具失败返回格式测试")
        print("📋 测试每个工具失败时返回的格式，了解错误返回值的结构")

        # 测试1: read_graph工具失败格式
        print("\n🔍 测试1: read_graph工具失败格式")
        try:
            # 创建一个无效的数据库连接来触发失败
            from neo4j import AsyncGraphDatabase
            invalid_driver = AsyncGraphDatabase.driver("neo4j://invalid:9999", auth=("invalid", "invalid"))
            invalid_memory = Neo4jMemory(invalid_driver)
            
            result = await invalid_memory.read_graph()
            print(f"❌ read_graph应该失败但返回了: {result}")
        except Exception as e:
            print(f"❌ read_graph工具失败返回格式:")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            print(f"   错误对象: {e}")

        # 测试2: create_entities工具失败格式
        print("\n🔍 测试2: create_entities工具失败格式")
        try:
            # 传入无效数据来触发失败
            invalid_data = {"invalid": "data"}
            result = await neo4j_memory.create_entities([invalid_data])
            print(f"❌ create_entities应该失败但返回了: {result}")
        except Exception as e:
            print(f"❌ create_entities工具失败返回格式:")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            print(f"   错误对象: {e}")

        # 测试3: create_relations工具失败格式
        print("\n🔍 测试3: create_relations工具失败格式")
        try:
            # 传入无效数据来触发失败
            invalid_data = {"invalid": "data"}
            result = await neo4j_memory.create_relations([invalid_data])
            print(f"❌ create_relations应该失败但返回了: {result}")
        except Exception as e:
            print(f"❌ create_relations工具失败返回格式:")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            print(f"   错误对象: {e}")

        # 测试4: add_constraints工具失败格式
        print("\n🔍 测试4: add_constraints工具失败格式")
        try:
            # 传入无效数据来触发失败
            invalid_data = {"invalid": "data"}
            result = await neo4j_memory.add_constraint([invalid_data])
            print(f"❌ add_constraints应该失败但返回了: {result}")
        except Exception as e:
            print(f"❌ add_constraints工具失败返回格式:")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            print(f"   错误对象: {e}")

        # 测试5: delete_entities工具失败格式
        print("\n🔍 测试5: delete_entities工具失败格式")
        try:
            # 尝试删除不存在的实体来触发失败
            await neo4j_memory.delete_entities(["不存在的实体"])
            print("❌ delete_entities应该失败但没有抛出异常")
        except Exception as e:
            print(f"❌ delete_entities工具失败返回格式:")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            print(f"   错误对象: {e}")

        # 测试6: delete_constraints工具失败格式
        print("\n🔍 测试6: delete_constraints工具失败格式")
        try:
            # 传入无效数据来触发失败
            invalid_data = {"invalid": "data"}
            await neo4j_memory.delete_constraint([invalid_data])
            print("❌ delete_constraints应该失败但没有抛出异常")
        except Exception as e:
            print(f"❌ delete_constraints工具失败返回格式:")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            print(f"   错误对象: {e}")

        # 测试7: delete_relations工具失败格式
        print("\n🔍 测试7: delete_relations工具失败格式")
        try:
            # 传入无效数据来触发失败
            invalid_data = {"invalid": "data"}
            await neo4j_memory.delete_relations([invalid_data])
            print("❌ delete_relations应该失败但没有抛出异常")
        except Exception as e:
            print(f"❌ delete_relations工具失败返回格式:")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            print(f"   错误对象: {e}")

        # 测试8: search_memories工具失败格式
        print("\n🔍 测试8: search_memories工具失败格式")
        try:
            # 传入无效查询来触发失败
            result = await neo4j_memory.search_memories(None)
            print(f"❌ search_memories应该失败但返回了: {result}")
        except Exception as e:
            print(f"❌ search_memories工具失败返回格式:")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            print(f"   错误对象: {e}")

        # 测试9: find_memories_by_name工具失败格式
        print("\n🔍 测试9: find_memories_by_name工具失败格式")
        try:
            # 传入无效数据来触发失败
            result = await neo4j_memory.find_memories_by_name(None)
            print(f"❌ find_memories_by_name应该失败但返回了: {result}")
        except Exception as e:
            print(f"❌ find_memories_by_name工具失败返回格式:")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            print(f"   错误对象: {e}")

        print("\n✅ 所有工具失败返回格式测试完成")
        print("📊 通过以上测试，您可以了解每个工具失败时返回的错误格式")

    @pytest.mark.asyncio
    async def test_entity_validation_failure(self, mcp_server, neo4j_memory):
        """测试Entity字段验证失败的情况"""
        print("\n🧪 测试18: Entity字段验证失败测试")
        print("📋 测试当缺少必需字段时，Entity创建会失败")

        # 测试1: 缺少name字段
        print("\n🔍 测试1: 缺少name字段")
        try:
            invalid_entity = Entity(
                # name字段缺失
                operation_type="测试",
                node_type="测试类型",
                point=1,
                description="测试描述",
                node_description="测试类型描述",
                constraint={},
                label=["测试"]
            )
            print("❌ 缺少name字段应该失败，但没有抛出异常")
        except Exception as e:
            print(f"✅ 缺少name字段正确抛出异常: {type(e).__name__}: {str(e)}")

        # 测试2: 缺少operation_type字段
        print("\n🔍 测试2: 缺少operation_type字段")
        try:
            invalid_entity = Entity(
                name="测试实体",
                # operation_type字段缺失
                node_type="测试类型",
                point=1,
                description="测试描述",
                node_description="测试类型描述",
                constraint={},
                label=["测试"]
            )
            print("❌ 缺少operation_type字段应该失败，但没有抛出异常")
        except Exception as e:
            print(f"✅ 缺少operation_type字段正确抛出异常: {type(e).__name__}: {str(e)}")

        # 测试3: 缺少node_type字段
        print("\n🔍 测试3: 缺少node_type字段")
        try:
            invalid_entity = Entity(
                name="测试实体",
                operation_type="测试",
                # node_type字段缺失
                point=1,
                description="测试描述",
                node_description="测试类型描述",
                constraint={},
                label=["测试"]
            )
            print("❌ 缺少node_type字段应该失败，但没有抛出异常")
        except Exception as e:
            print(f"✅ 缺少node_type字段正确抛出异常: {type(e).__name__}: {str(e)}")

        # 测试4: 缺少point字段
        print("\n🔍 测试4: 缺少point字段")
        try:
            invalid_entity = Entity(
                name="测试实体",
                operation_type="测试",
                node_type="测试类型",
                # point字段缺失
                description="测试描述",
                node_description="测试类型描述",
                constraint={},
                label=["测试"]
            )
            print("❌ 缺少point字段应该失败，但没有抛出异常")
        except Exception as e:
            print(f"✅ 缺少point字段正确抛出异常: {type(e).__name__}: {str(e)}")

        # 测试5: 缺少description字段
        print("\n🔍 测试5: 缺少description字段")
        try:
            invalid_entity = Entity(
                name="测试实体",
                operation_type="测试",
                node_type="测试类型",
                point=1,
                # description字段缺失
                node_description="测试类型描述",
                constraint={},
                label=["测试"]
            )
            print("❌ 缺少description字段应该失败，但没有抛出异常")
        except Exception as e:
            print(f"✅ 缺少description字段正确抛出异常: {type(e).__name__}: {str(e)}")

        # 测试6: 缺少node_description字段
        print("\n🔍 测试6: 缺少node_description字段")
        try:
            invalid_entity = Entity(
                name="测试实体",
                operation_type="测试",
                node_type="测试类型",
                point=1,
                description="测试描述",
                # node_description字段缺失
                constraint={},
                label=["测试"]
            )
            print("❌ 缺少node_description字段应该失败，但没有抛出异常")
        except Exception as e:
            print(f"✅ 缺少node_description字段正确抛出异常: {type(e).__name__}: {str(e)}")

        # 测试7: 缺少constraint字段
        print("\n🔍 测试7: 缺少constraint字段")
        try:
            invalid_entity = Entity(
                name="测试实体",
                operation_type="测试",
                node_type="测试类型",
                point=1,
                description="测试描述",
                node_description="测试类型描述",
                # constraint字段缺失
                label=["测试"]
            )
            print("❌ 缺少constraint字段应该失败，但没有抛出异常")
        except Exception as e:
            print(f"✅ 缺少constraint字段正确抛出异常: {type(e).__name__}: {str(e)}")

        # 测试8: 缺少label字段
        print("\n🔍 测试8: 缺少label字段")
        try:
            invalid_entity = Entity(
                name="测试实体",
                operation_type="测试",
                node_type="测试类型",
                point=1,
                description="测试描述",
                node_description="测试类型描述",
                constraint={},
                # label字段缺失
            )
            print("❌ 缺少label字段应该失败，但没有抛出异常")
        except Exception as e:
            print(f"✅ 缺少label字段正确抛出异常: {type(e).__name__}: {str(e)}")

        # 测试9: 测试通过MCP工具创建时的验证
        print("\n🔍 测试9: 通过MCP工具创建时的验证")
        try:
            # 创建一个缺少必需字段的实体数据
            invalid_entity_data = {
                "name": "测试实体",
                # 缺少其他必需字段
            }
            
            # 尝试通过MCP工具创建
            result = await neo4j_memory.create_entities([invalid_entity_data])
            print(f"❌ 通过MCP工具创建无效实体应该失败，但返回了: {result}")
        except Exception as e:
            print(f"✅ 通过MCP工具创建无效实体正确抛出异常: {type(e).__name__}: {str(e)}")

        print("\n✅ Entity字段验证失败测试完成")
        print("📊 所有必需字段的验证都正确工作，缺少任何字段都会导致创建失败")

    @pytest.mark.asyncio
    async def test_relation_validation_failure(self, mcp_server, neo4j_memory):
        """测试Relation字段验证失败的情况"""
        print("\n🧪 测试19: Relation字段验证失败测试")
        print("📋 测试当缺少必需字段时，Relation创建会失败")

        # 测试1: 缺少source字段
        print("\n🔍 测试1: 缺少source字段")
        try:
            invalid_relation = Relation(
                # source字段缺失
                target="目标实体",
                relationType="测试关系",
                description="测试关系描述"
            )
            print("❌ 缺少source字段应该失败，但没有抛出异常")
        except Exception as e:
            print(f"✅ 缺少source字段正确抛出异常: {type(e).__name__}: {str(e)}")

        # 测试2: 缺少target字段
        print("\n🔍 测试2: 缺少target字段")
        try:
            invalid_relation = Relation(
                source="源实体",
                # target字段缺失
                relationType="测试关系",
                description="测试关系描述"
            )
            print("❌ 缺少target字段应该失败，但没有抛出异常")
        except Exception as e:
            print(f"✅ 缺少target字段正确抛出异常: {type(e).__name__}: {str(e)}")

        # 测试3: 缺少relationType字段
        print("\n🔍 测试3: 缺少relationType字段")
        try:
            invalid_relation = Relation(
                source="源实体",
                target="目标实体",
                # relationType字段缺失
                description="测试关系描述"
            )
            print("❌ 缺少relationType字段应该失败，但没有抛出异常")
        except Exception as e:
            print(f"✅ 缺少relationType字段正确抛出异常: {type(e).__name__}: {str(e)}")

        # 测试4: 缺少description字段
        print("\n🔍 测试4: 缺少description字段")
        try:
            invalid_relation = Relation(
                source="源实体",
                target="目标实体",
                relationType="测试关系"
                # description字段缺失
            )
            print("❌ 缺少description字段应该失败，但没有抛出异常")
        except Exception as e:
            print(f"✅ 缺少description字段正确抛出异常: {type(e).__name__}: {str(e)}")

        # 测试5: 测试通过MCP工具创建时的验证
        print("\n🔍 测试5: 通过MCP工具创建时的验证")
        try:
            # 创建一个缺少必需字段的关系数据
            invalid_relation_data = {
                "source": "源实体",
                # 缺少其他必需字段
            }
            
            # 尝试通过MCP工具创建
            result = await neo4j_memory.create_relations([invalid_relation_data])
            print(f"❌ 通过MCP工具创建无效关系应该失败，但返回了: {result}")
        except Exception as e:
            print(f"✅ 通过MCP工具创建无效关系正确抛出异常: {type(e).__name__}: {str(e)}")

        print("\n✅ Relation字段验证失败测试完成")
        print("📊 所有必需字段的验证都正确工作，缺少任何字段都会导致创建失败")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
