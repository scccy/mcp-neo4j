# 🔍📊 Neo4j Data Modeling MCP Server

## 🌟 Overview

A Model Context Protocol (MCP) server implementation that provides tools for creating, visualizing, and managing Neo4j graph data models. This server enables you to define nodes, relationships, and properties to design graph database schemas that can be visualized interactively.

## 🧩 Components

### 🛠️ Tools

The server offers these core tools:

#### 📊 Data Model Creation Tools
- `add_nodes`
   - Add new nodes to the data model
   - Input: 
     - `nodes` (list of Node objects): The nodes to add
     - `data_model` (DataModel): Current data model
   - Returns: Updated data model

- `add_relationships`
   - Add new relationships to the data model
   - Input:
     - `relationships` (list of Relationship objects): The relationships to add
     - `data_model` (DataModel): Current data model
   - Returns: Updated data model

- `add_node_properties`
   - Add properties to a specific node type
   - Input:
     - `node_label` (string): The label of the node to modify
     - `properties` (list of Property objects): Properties to add
     - `data_model` (DataModel): Current data model
   - Returns: Updated data model

- `add_relationship_properties`
   - Add properties to a specific relationship type
   - Input:
     - `relationship_type` (string): Type of relationship
     - `start_node_label` (string): Label of start node
     - `end_node_label` (string): Label of end node
     - `properties` (list of Property objects): Properties to add
     - `data_model` (DataModel): Current data model
   - Returns: Updated data model

#### 🗑️ Data Model Modification Tools
- `remove_node`
   - Remove a node from the data model
   - Input:
     - `node_label` (string): The label of the node to remove
     - `data_model` (DataModel): Current data model
   - Returns: Updated data model

- `remove_relationship`
   - Remove a relationship from the data model
   - Input:
     - `relationship_type` (string): Type of relationship
     - `start_node_label` (string): Label of start node
     - `end_node_label` (string): Label of end node
     - `data_model` (DataModel): Current data model
   - Returns: Updated data model

- `remove_node_property`
   - Remove a property from a node
   - Input:
     - `node_label` (string): The label of the node
     - `property_name` (string): Name of property to remove
     - `data_model` (DataModel): Current data model
   - Returns: Updated data model

- `remove_relationship_property`
   - Remove a property from a relationship
   - Input:
     - `relationship_type` (string): Type of relationship
     - `start_node_label` (string): Label of start node
     - `end_node_label` (string): Label of end node
     - `property_name` (string): Name of property to remove
     - `data_model` (DataModel): Current data model
   - Returns: Updated data model

#### ✅ Validation Tools
- `validate_node`
   - Validate a single node
   - Input:
     - `node` (Node): The node to validate
   - Returns: True if valid, error message if invalid

- `validate_relationship`
   - Validate a single relationship
   - Input:
     - `relationship` (Relationship): The relationship to validate
   - Returns: True if valid, error message if invalid

- `validate_data_model`
   - Validate the entire data model
   - Input:
     - `data_model` (DataModel): The data model to validate
   - Returns: True if valid, error message if invalid

#### 👁️ Visualization Tools
- `visualize_data_model`
   - Generate and open an interactive visualization of the data model
   - Input:
     - `data_model` (DataModel): The data model to visualize
   - Returns: None (opens browser visualization)

## 🔧 Usage with Claude Desktop

### 💾 Released Package

Can be found on PyPi https://pypi.org/project/mcp-neo4j-data-modeling/

Add the server to your `claude_desktop_config.json` with the transport method specified:

```json
"mcpServers": {
  "neo4j-data-modeling": {
    "command": "uvx",
    "args": [ "mcp-neo4j-data-modeling@0.1.0", "--transport", "stdio" ]
  }
}
```

### 🐳 Using with Docker

```json
"mcpServers": {
  "neo4j-data-modeling": {
    "command": "docker",
    "args": [
      "run",
      "--rm",
      "mcp/neo4j-data-modeling:latest"
    ]
  }
}
```

## 🚀 Development

### 📦 Prerequisites

1. Install `uv` (Universal Virtualenv):
```bash
# Using pip
pip install uv

# Using Homebrew on macOS
brew install uv

# Using cargo (Rust package manager)
cargo install uv
```

2. Clone the repository and set up development environment:
```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-neo4j-data-modeling.git
cd mcp-neo4j-data-modeling

# Create and activate virtual environment using uv
uv venv
source .venv/bin/activate  # On Unix/macOS
.venv\Scripts\activate     # On Windows

# Install dependencies including dev dependencies
uv pip install -e ".[dev]"
```

3. Run Tests

```bash
./test.sh
```

### 🔧 Development Configuration

```json
# Add the server to your claude_desktop_config.json
"mcpServers": {
  "neo4j-data-modeling": {
    "command": "uv",
    "args": [
      "--directory", "path_to_repo/src",
      "run", "mcp-neo4j-data-modeling", "--transport", "stdio"]
  }
}
```

### 🐳 Docker

Build and run the Docker container:

```bash
# Build the image
docker build -t mcp/neo4j-data-modeling:latest .

# Run the container
docker run mcp/neo4j-data-modeling:latest
```

## 📄 License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
