# 🚀 MCP Neo4j Memory Server - 本地构建指南

## 📋 概述

本指南将帮助你在本地环境中构建、测试和运行 MCP Neo4j Memory Server。

## 🛠️ 环境要求

- Python 3.10+
- uv (Universal Virtualenv) - 推荐使用
- Neo4j 数据库 (本地或远程)
- Git

## 🔧 环境设置

### 1. 安装 uv (如果还没有安装)

```bash
# 使用 pip
pip install uv

# 使用 Homebrew (macOS)
brew install uv

# 使用 cargo (Rust)
cargo install uv
```

### 2. 克隆项目

```bash
git clone https://github.com/neo4j-contrib/mcp-neo4j.git
cd mcp-neo4j/servers/mcp-neo4j-memory
```

### 3. 创建虚拟环境

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate
```

### 4. 安装依赖

```bash
# 安装开发依赖
uv pip install -e ".[dev]"

# 或者安装所有依赖
uv pip install -e .
```

## 🧪 运行测试

### 单元测试

```bash
# 运行所有单元测试
uv run python -m pytest tests/ -v

# 运行特定测试文件
uv run python -m pytest tests/test_neo4j_memory_pytest.py -v

# 运行特定测试函数
uv run python -m pytest tests/test_neo4j_memory_pytest.py::test_create_entities -v
```

### 集成测试

```bash
# 运行集成测试 (需要 Neo4j 数据库)
uv run python -m pytest tests/integration/ -v
```

## 🗄️ 数据库配置

### 环境变量设置

#### 方法1：使用环境变量文件（推荐）

项目提供了 `test.env.example` 文件作为模板：

```bash
# 复制示例文件
cp test.env.example test.env

# 编辑 test.env 文件，填入你的实际配置
nano test.env  # 或使用你喜欢的编辑器
```

#### 方法2：直接设置环境变量

```bash
# Neo4j 连接配置
export NEO4J_URL="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="your_actual_password"  # 请修改为实际密码
export NEO4J_DATABASE="neo4j"

# MCP 服务器配置
export NEO4J_TRANSPORT="stdio"  # stdio, sse, http
export NEO4J_MCP_SERVER_HOST="127.0.0.1"
export NEO4J_MCP_SERVER_PORT="8000"
export NEO4J_MCP_SERVER_PATH="/mcp/"
```

**⚠️ 安全提醒：**
- 不要将包含真实密码的配置文件提交到 Git
- `test.env` 文件已被添加到 `.gitignore`
- 使用 `test.env.example` 作为配置模板

### 本地 Neo4j 数据库

```bash
# 使用 Docker 运行 Neo4j
docker run \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5.15

# 访问 Neo4j Browser: http://localhost:7474
```

## 🚀 运行服务器

### 1. STDIO 模式 (默认)

```bash
# 基本运行
uv run python -m mcp_neo4j_memory

# 指定参数
uv run python -m mcp_neo4j_memory \
  --db-url "bolt://localhost:7687" \
  --username "neo4j" \
  --password "password" \
  --database "neo4j"
```

### 2. HTTP 模式

```bash
# HTTP 模式
uv run python -m mcp_neo4j_memory \
  --transport http \
  --server-host "0.0.0.0" \
  --server-port "8000" \
  --server-path "/mcp/"
```

### 3. 使用 uvx

```bash
# 本地开发模式
uvx mcp-neo4j-memory@editable \
  --db-url "bolt://localhost:7687" \
  --username "neo4j" \
  --password "password"
```

## 📝 开发工作流

### 1. 代码修改

```bash
# 查看修改状态
git status

# 添加修改
git add .

# 提交修改
git commit -m "描述你的修改"

# 推送到你的 fork
git push fork main
```

### 2. 测试修改

```bash
# 运行测试确保没有破坏现有功能
uv run python -m pytest tests/ -v

# 运行特定测试
uv run python -m pytest tests/test_neo4j_memory_pytest.py::test_create_entities -v
```

### 3. 代码质量检查

```bash
# 类型检查
uv run pyright src/

# 代码格式化 (如果安装了 black)
uv run black src/ tests/

# 代码检查 (如果安装了 flake8)
uv run flake8 src/ tests/
```

## 🐳 Docker 支持

### 构建镜像

```bash
# 构建 Docker 镜像
docker build -t mcp/neo4j-memory:latest .

# 运行容器
docker run -e NEO4J_URL="bolt://localhost:7687" \
           -e NEO4J_USERNAME="neo4j" \
           -e NEO4J_PASSWORD="password" \
           mcp/neo4j-memory:latest
```

## 🔍 调试技巧

### 1. 日志级别

```bash
# 设置更详细的日志
export PYTHONPATH=src
export LOG_LEVEL=DEBUG
uv run python -m mcp_neo4j_memory
```

### 2. 数据库连接测试

```python
# 在 Python 中测试连接
from neo4j import AsyncGraphDatabase

async def test_connection():
    driver = AsyncGraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "password")
    )
    try:
        await driver.verify_connectivity()
        print("连接成功!")
    except Exception as e:
        print(f"连接失败: {e}")
    finally:
        await driver.close()

# 运行测试
import asyncio
asyncio.run(test_connection())
```

### 3. 使用 ipdb 调试

```bash
# 安装调试器
uv add ipdb

# 在代码中添加断点
import ipdb; ipdb.set_trace()
```

## 📚 有用的命令

### 清理和重置

```bash
# 清理 Python 缓存
find . -type d -name "__pycache__" -delete
find . -name "*.pyc" -delete

# 重新安装依赖
rm -rf .venv
uv venv
uv pip install -e ".[dev]"
```

### 查看帮助

```bash
# 查看命令行帮助
uv run python -m mcp_neo4j_memory --help

# 查看包信息
uv run python -c "import mcp_neo4j_memory; print(mcp_neo4j_memory.__version__)"
```

## 🚨 常见问题

### 1. 导入错误

```bash
# 确保在正确的目录中
cd mcp-neo4j/servers/mcp-neo4j-memory

# 设置 PYTHONPATH
export PYTHONPATH=src:$PYTHONPATH
```

### 2. 数据库连接失败

- 检查 Neo4j 是否正在运行
- 验证连接字符串和认证信息
- 检查防火墙设置

### 3. 权限问题

```bash
# 确保有正确的文件权限
chmod +x src/mcp_neo4j_memory/__init__.py
```

## 📞 获取帮助

如果遇到问题：

1. 检查日志输出
2. 查看 Neo4j 数据库状态
3. 运行测试确认功能正常
4. 查看 GitHub Issues

## 🎯 下一步

完成本地构建后，你可以：

1. 运行测试确保所有功能正常
2. 测试与 Claude Desktop 的集成
3. 贡献代码到原项目
4. 创建 Pull Request

---

**Happy Coding! 🎉**
