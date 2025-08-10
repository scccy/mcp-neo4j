#!/usr/bin/env python3
"""
清空Neo4j数据库的脚本
"""

import asyncio
import os
from neo4j import AsyncGraphDatabase

# 设置环境变量
# 数据库连接配置 - 请根据你的实际环境修改
os.environ["NEO4J_URL"] = "neo4j://localhost:7687"  # 或者使用 NEO4J_URI
os.environ["NEO4J_USERNAME"] = "neo4j"  # 或者使用 NEO4J_USER
os.environ["NEO4J_PASSWORD"] = "password"  # 请修改为你的实际密码
os.environ["NEO4J_DATABASE"] = "neo4j"

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

async def main():
    """主函数"""
    await clear_database()

if __name__ == "__main__":
    asyncio.run(main())
