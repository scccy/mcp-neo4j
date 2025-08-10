"""
pytest配置文件
用于配置测试环境和路径
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault("NEO4J_URI", "neo4j://localhost:7687")
os.environ.setdefault("NEO4J_USER", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "password")  # 请修改为你的实际密码
os.environ.setdefault("NEO4J_DATABASE", "neo4j")

import pytest
import asyncio
from neo4j import AsyncGraphDatabase
from mcp_neo4j_memory.neo4j_memory import Neo4jMemory


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def neo4j_driver():
    """创建真实的Neo4j数据库连接"""
    # 从环境变量获取连接信息，如果没有设置则使用默认值
    uri = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password')  # 请根据您的实际密码修改
    
    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    
    # 测试连接
    try:
        await driver.verify_connectivity()
        print(f"✅ 成功连接到Neo4j数据库: {uri}")
    except Exception as e:
        print(f"❌ 无法连接到Neo4j数据库: {e}")
        print("请确保Neo4j数据库正在运行，并检查连接参数")
        pytest.skip(f"Neo4j数据库连接失败: {e}")
    
    yield driver
    
    # 清理连接
    await driver.close()


@pytest.fixture
async def neo4j_memory(neo4j_driver):
    """创建真实的Neo4jMemory实例"""
    memory = Neo4jMemory(neo4j_driver)
    
    # 清理测试数据
    await cleanup_test_database(memory)
    
    yield memory
    
    # 测试后清理
    await cleanup_test_database(memory)


@pytest.fixture
def neo4j_memory_sync(neo4j_driver):
    """创建同步版本的Neo4jMemory实例，用于同步测试"""
    # 这是一个同步fixture，返回一个协程函数
    async def _create_memory():
        memory = Neo4jMemory(neo4j_driver)
        await cleanup_test_database(memory)
        return memory
    
    return _create_memory


async def cleanup_test_database(memory):
    """清理测试数据库中的所有数据"""
    try:
        # 删除所有节点和关系
        async with memory.driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
        print("🧹 测试数据库已清理")
    except Exception as e:
        print(f"⚠️ 清理数据库时出现警告: {e}")


@pytest.fixture
def test_env():
    """设置测试环境变量"""
    # 保存原始环境变量
    original_env = {}
    for key in ['NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD', 'NEO4J_DATABASE']:
        if key in os.environ:
            original_env[key] = os.environ[key]

    # 设置测试环境变量
    test_env_vars = {
        'NEO4J_URI': 'neo4j://localhost:7687',
        'NEO4J_USER': 'neo4j',
        'NEO4J_PASSWORD': 'password',  # 请根据您的实际密码修改
        'NEO4J_DATABASE': 'neo4j'
    }

    for key, value in test_env_vars.items():
        os.environ[key] = value

    yield test_env_vars

    # 恢复原始环境变量
    for key, value in original_env.items():
        os.environ[key] = value
    for key in test_env_vars:
        if key not in original_env:
            del os.environ[key]


@pytest.fixture
def sample_test_data():
    """提供测试用的样本数据"""
    return {
        'entities': [
            {
                'name': '张三',
                'type': 'Person',
                'properties': {'age': 30, 'occupation': '工程师'}
            },
            {
                'name': 'ABC公司',
                'type': 'Company',
                'properties': {'industry': '科技', 'founded': 2020}
            }
        ],
        'relations': [
            {
                'source': '张三',
                'target': 'ABC公司',
                'type': 'WORKS_FOR',
                'properties': {'start_date': '2023-01-01'}
            }
        ],
        'observations': [
            {
                'entity_name': '张三',
                'constraint_type': 'has_skill',
                'constraint_value': 'Python编程'
            }
        ]
    }


@pytest.fixture
def sample_entities():
    """创建测试用的实体数据"""
    from mcp_neo4j_memory.neo4j_memory import Entity
    
    return [
        Entity(
            name="张三",
            operation_type="员工",
            node_type="人员",
            point="高级",
            description="张三是一名技术部的高级工程师",
            node_description="人员是指公司中的员工个体",
            constraint={
                "必须": {"部门": "技术部", "职级": "高级工程师"},
                "禁止": {"加班": "超过12小时"},
                "建议": {"技能": "Python, Neo4j"}
            },
            label=["员工", "技术部", "高级工程师"]
        ),
        Entity(
            name="ABC公司",
            operation_type="公司",
            node_type="组织",
            point="大型",
            description="ABC公司是一家科技公司",
            node_description="组织是指公司或机构",
            constraint={
                "必须": {"行业": "科技", "成立时间": "2020年"},
                "建议": {"规模": "大型企业"}
            },
            label=["公司", "科技", "大型企业"]
        )
    ]


@pytest.fixture
def sample_relations():
    """创建测试用的关系数据"""
    from mcp_neo4j_memory.neo4j_memory import Relation
    
    return [
        Relation(
            source="张三",
            target="ABC公司",
            relationType="WORKS_FOR",
            description="张三在ABC公司工作"
        )
    ]


@pytest.fixture
def sample_observations():
    """创建测试用的约束数据"""
    from mcp_neo4j_memory.neo4j_memory import ConstraintAddition
    
    return [
        ConstraintAddition(
            entityName="张三",
            constraint={
                "技能": {"Python编程": "熟练", "Neo4j": "熟练"}
            }
        )
    ]
