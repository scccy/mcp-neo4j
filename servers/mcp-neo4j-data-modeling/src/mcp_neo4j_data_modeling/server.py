import logging
from typing import Any, Literal
import webbrowser
import os

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from .data_model import DataModel, Node, Relationship, Property, _generate_relationship_pattern


logger = logging.getLogger("mcp_neo4j_data_modeling")


def create_mcp_server() -> FastMCP:
    """Create an MCP server instance for data modeling."""

    mcp: FastMCP = FastMCP("mcp-neo4j-data-modeling", dependencies=["pydantic", "webbrowser"])

    @mcp.resource("resource://init")
    def init() -> DataModel:
        """Create an empty data model."""
        return DataModel(nodes=[], relationships=[])

    @mcp.tool()
    def add_nodes(nodes: list[Node], data_model: DataModel) -> DataModel:
        "Add a new node to the data model, if it doesn't already exist. Returns the updated data model as a JSON string."
        for node in nodes:
            data_model.add_node(node)
        return data_model

    @mcp.tool()
    def add_relationships(relationships: list[Relationship], data_model: DataModel) -> DataModel:
        "Add a new relationship to the data model, if it doesn't already exist. The relationship must have a start and end node that exist in the data model. Returns the updated data model as a JSON string."
        for relationship in relationships:
            data_model.add_relationship(relationship)
        return data_model

    @mcp.tool()
    def add_node_properties(node_label: str, properties: list[Property], data_model: DataModel) -> DataModel:
        "Add new properties to the node, if they doesn't already exist. Returns the updated data model as a JSON string."
        for node in data_model.nodes:
            if node.label == node_label:
                for prop in properties:
                    if prop.name not in [p.name for p in node.properties]:
                        node.add_property(prop)
                return data_model
        raise ValueError(f"Node with label {node_label} not found in data model")

    @mcp.tool()
    def add_relationship_properties(relationship_type: str, start_node_label: str, end_node_label: str, properties: list[Property], data_model: DataModel) -> DataModel:
        "Add a new property to the relationship, if it doesn't already exist. Returns the updated data model as a JSON string."
        pattern = _generate_relationship_pattern(start_node_label, relationship_type, end_node_label)
        for relationship in data_model.relationships:
            if relationship.pattern == pattern:
                for prop in properties:
                    if prop.name not in [p.name for p in relationship.properties]:
                        relationship.add_property(prop)
                return data_model
        raise ValueError(f"Relationship with pattern {pattern} not found in data model")

    @mcp.tool()
    def remove_node(node_label: str, data_model: DataModel) -> DataModel:
        "Remove a node from the data model, if it exists. Returns the updated data model as a JSON string."
        data_model.remove_node(node_label)
        return data_model

    @mcp.tool()
    def remove_relationship(relationship_type: str, start_node_label: str, end_node_label: str, data_model: DataModel) -> DataModel:
        "Remove a relationship from the data model, if it exists. Returns the updated data model as a JSON string."
        data_model.remove_relationship(relationship_type, start_node_label, end_node_label)
        return data_model

    @mcp.tool()
    def remove_node_property(node_label: str, property_name: str, data_model: DataModel) -> DataModel:
        "Remove a property from the node, if it exists. Returns the updated data model as a JSON string."
        for node in data_model.nodes:
            if node.label == node_label:
                node.remove_property(property_name)
                return data_model
        raise ValueError(f"Node with label {node_label} not found in data model")

    @mcp.tool()
    def remove_relationship_property(relationship_type: str, start_node_label: str, end_node_label: str, property_name: str, data_model: DataModel) -> DataModel:
        "Remove a property from the relationship, if it exists. Returns the updated data model as a JSON string."
        pattern = _generate_relationship_pattern(start_node_label, relationship_type, end_node_label)
        for relationship in data_model.relationships:
            if relationship.pattern == pattern:
                relationship.remove_property(property_name)
                return data_model
        raise ValueError(f"Relationship with type {relationship_type} not found in data model")

    @mcp.tool()
    def validate_node(node: Node) -> bool:
        "Validate a single node. Returns True if the node is valid, False otherwise."
        try:
            Node.model_validate(node, strict=True)
        except ValidationError as e:
            raise ValueError(f"Validation error: {e}")
        return True

    @mcp.tool()
    def validate_relationship(relationship: Relationship) -> bool:
        "Validate a single relationship. Returns True if the relationship is valid, False otherwise."
        try:
            Relationship.model_validate(relationship, strict=True)
        except ValidationError as e:
            raise ValueError(f"Validation error: {e}")
        return True
    
    @mcp.tool()
    def validate_data_model(data_model: DataModel) -> bool:
        "Validate the entire data model. Returns True if the data model is valid, False otherwise."
        try:
            DataModel.model_validate(data_model, strict=True)
        except ValidationError as e:
            raise ValueError(f"Validation error: {e}")
        return True

    @mcp.tool()
    def visualize_data_model(data_model: DataModel) -> None:
        "Open an interactive graph visualization in the default web browser."
        try:
            dm_validated = DataModel.model_validate(data_model, strict=True)
        except ValidationError as e:
            raise ValueError(f"Validation error: {e}")

        def open_html_in_browser(html_content, filename="temp.html"):
            """Opens an HTML string in the default web browser.

            Args:
                html_content: The HTML content as a string.
                filename: The name of the temporary HTML file.
            """
            with open(filename, "w") as f:
                f.write(html_content)

            # Construct the file URL
            file_url = 'file://' + os.path.realpath(filename)
            webbrowser.open_new_tab(file_url)

        open_html_in_browser(dm_validated.to_nvl().render().data)

    @mcp.tool()
    def load_from_arrows_json(arrows_data_model_dict: dict[str, Any]) -> DataModel:
        "Load a data model from the Arrows web application format. Returns a data model as a JSON string."
        return DataModel.from_arrows(arrows_data_model_dict)
        
    return mcp


async def main(
    transport: Literal["stdio", "sse"] = "stdio",
) -> None:
    logger.info("Starting MCP Neo4j Data ModelingServer")


    mcp = create_mcp_server()

    match transport:
        case "stdio":
            await mcp.run_stdio_async()
        case "sse":
            await mcp.run_sse_async()
        case _:
            raise ValueError(f"Invalid transport: {transport} | Must be either 'stdio' or 'sse'")


if __name__ == "__main__":
    main()
