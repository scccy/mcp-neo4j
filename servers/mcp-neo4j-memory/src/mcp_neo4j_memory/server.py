import json
import logging
from typing import Literal

from neo4j import AsyncGraphDatabase
from pydantic import Field

from fastmcp.server import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult, TextContent
from neo4j.exceptions import Neo4jError
from mcp.types import ToolAnnotations

from .neo4j_memory import Neo4jMemory, Entity, Relation, ConstraintAddition, ConstraintDeletion, KnowledgeGraph

# Set up logging
logger = logging.getLogger('mcp_neo4j_memory')
logger.setLevel(logging.INFO)


def create_mcp_server(memory: Neo4jMemory) -> FastMCP:
    """Create an MCP server instance for memory management."""

    mcp: FastMCP = FastMCP("mcp-neo4j-memory", dependencies=["neo4j", "pydantic"])

    @mcp.tool(annotations=ToolAnnotations(title="Read Graph",
                                          readOnlyHint=True,
                                          destructiveHint=False,
                                          idempotentHint=True,
                                          openWorldHint=True))
    async def read_graph() -> KnowledgeGraph:
        """Read the entire knowledge graph."""
        logger.info("MCP tool: read_graph")
        try:
            result = await memory.read_graph()
            return ToolResult(content=[TextContent(type="text", text=result.model_dump_json())],
                          structured_content=result)
        except Neo4jError as e:
            logger.error(f"Neo4j error reading full knowledge graph: {e}")
            raise ToolError(f"Neo4j error reading full knowledge graph: {e}")
        except Exception as e:
            logger.error(f"Error reading full knowledge graph: {e}")
            raise ToolError(f"Error reading full knowledge graph: {e}")

    @mcp.tool(annotations=ToolAnnotations(title="Create Entities",
                                          readOnlyHint=False,
                                          destructiveHint=False,
                                          idempotentHint=True,
                                          openWorldHint=True))
    async def create_entities(entities: list[Entity] = Field(..., description="List of entities to create")) -> list[Entity]:

        """Create multiple new entities in the knowledge graph."""
        logger.info(f"MCP tool: create_entities ({len(entities)} entities)")
        try:
            entity_objects = [Entity.model_validate(entity) for entity in entities]
            result = await memory.create_entities(entity_objects)
            return ToolResult(content=[TextContent(type="text", text=json.dumps([e.model_dump() for e in result]))],
                          structured_content={"result": result})
        except Neo4jError as e:
            logger.error(f"Neo4j error creating entities: {e}")
            raise ToolError(f"Neo4j error creating entities: {e}")
        except Exception as e:
            logger.error(f"Error creating entities: {e}")
            raise ToolError(f"Error creating entities: {e}")

    @mcp.tool(annotations=ToolAnnotations(title="Create Relations",
                                          readOnlyHint=False,
                                          destructiveHint=False,
                                          idempotentHint=True,
                                          openWorldHint=True))
    async def create_relations(relations: list[Relation] = Field(..., description="List of relations to create")) -> list[Relation]:
        """Create multiple new relations between entities."""
        logger.info(f"MCP tool: create_relations ({len(relations)} relations)")
        try:
            relation_objects = [Relation.model_validate(relation) for relation in relations]
            result = await memory.create_relations(relation_objects)
            return ToolResult(content=[TextContent(type="text", text=json.dumps([r.model_dump() for r in result]))],
                          structured_content={"result": result})
        except Neo4jError as e:
            logger.error(f"Neo4j error creating relations: {e}")
            raise ToolError(f"Neo4j error creating relations: {e}")
        except Exception as e:
            logger.error(f"Error creating relations: {e}")
            raise ToolError(f"Error creating relations: {e}")

    @mcp.tool(annotations=ToolAnnotations(title="Add Constraints",
                                          readOnlyHint=False,
                                          destructiveHint=False,
                                          idempotentHint=True,
                                          openWorldHint=True))
    async def add_constraints(constraints: list[ConstraintAddition] = Field(..., description="List of constraints to add")) -> list[dict[str, str | list[str]]]:
        """Add new constraints to existing entities."""
        logger.info(f"MCP tool: add_constraints ({len(constraints)} additions)")
        try:
            constraint_objects = [ConstraintAddition.model_validate(obs) for obs in constraints]
            result = await memory.add_constraint(constraint_objects)
            return ToolResult(content=[TextContent(type="text", text=json.dumps(result))],
                          structured_content={"result": result})
        except Neo4jError as e:
            logger.error(f"Neo4j error adding constraints: {e}")
            raise ToolError(f"Neo4j error adding constraints: {e}")
        except Exception as e:
            logger.error(f"Error adding constraints: {e}")
            raise ToolError(f"Error adding constraints: {e}")

    @mcp.tool(annotations=ToolAnnotations(title="Delete Entities",
                                          readOnlyHint=False,
                                          destructiveHint=True,
                                          idempotentHint=True,
                                          openWorldHint=True))
    async def delete_entities(entityNames: list[str] = Field(..., description="List of entity names to delete")) -> str:
        """Delete multiple entities and their associated relations."""
        logger.info(f"MCP tool: delete_entities ({len(entityNames)} entities)")
        try:
            await memory.delete_entities(entityNames)
            return ToolResult(content=[TextContent(type="text", text="Entities deleted successfully")],
                              structured_content={"result": "Entities deleted successfully"})
        except Neo4jError as e:
            logger.error(f"Neo4j error deleting entities: {e}")
            raise ToolError(f"Neo4j error deleting entities: {e}")
        except Exception as e:
            logger.error(f"Error deleting entities: {e}")
            raise ToolError(f"Error deleting entities: {e}")

    @mcp.tool(annotations=ToolAnnotations(title="Delete Constraints",
                                          readOnlyHint=False,
                                          destructiveHint=True,
                                          idempotentHint=True,
                                          openWorldHint=True))
    async def delete_constraints(deletions: list[ConstraintDeletion] = Field(..., description="List of constraints to delete")) -> str:
        """Delete specific constraints from entities."""
        logger.info(f"MCP tool: delete_constraints ({len(deletions)} deletions)")
        try:
            deletion_objects = [ConstraintDeletion.model_validate(deletion) for deletion in deletions]
            await memory.delete_constraint(deletion_objects)
            return ToolResult(content=[TextContent(type="text", text="Constraints deleted successfully")],
                          structured_content={"result": "Constraints deleted successfully"})
        except Neo4jError as e:
            logger.error(f"Neo4j error deleting constraints: {e}")
            raise ToolError(f"Neo4j error deleting constraints: {e}")
        except Exception as e:
            logger.error(f"Error deleting constraints: {e}")
            raise ToolError(f"Error deleting constraints: {e}")

    @mcp.tool(annotations=ToolAnnotations(title="Delete Relations",
                                          readOnlyHint=False,
                                          destructiveHint=True,
                                          idempotentHint=True,
                                          openWorldHint=True))

    async def delete_relations(relations: list[Relation] = Field(..., description="List of relations to delete")) -> str:
        """Delete multiple relations from the graph."""
        logger.info(f"MCP tool: delete_relations ({len(relations)} relations)")
        try:
            relation_objects = [Relation.model_validate(relation) for relation in relations]
            await memory.delete_relations(relation_objects)
            return ToolResult(content=[TextContent(type="text", text="Relations deleted successfully")],
                          structured_content={"result": "Relations deleted successfully"})
        except Neo4jError as e:
            logger.error(f"Neo4j error deleting relations: {e}")
            raise ToolError(f"Neo4j error deleting relations: {e}")
        except Exception as e:
            logger.error(f"Error deleting relations: {e}")
            raise ToolError(f"Error deleting relations: {e}")

    @mcp.tool(annotations=ToolAnnotations(title="Search Memories",
                                          readOnlyHint=True,
                                          destructiveHint=False,
                                          idempotentHint=True,
                                          openWorldHint=True))
    async def search_memories(query: str = Field(..., description="Search query for nodes")) -> KnowledgeGraph:
        """Search for memories based on a query containing search terms."""
        logger.info(f"MCP tool: search_memories ('{query}')")
        try:
            result = await memory.search_memories(query)
            return ToolResult(content=[TextContent(type="text", text=result.model_dump_json())],
                              structured_content=result)
        except Neo4jError as e:
            logger.error(f"Neo4j error searching memories: {e}")
            raise ToolError(f"Neo4j error searching memories: {e}")
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise ToolError(f"Error searching memories: {e}")

    @mcp.tool(annotations=ToolAnnotations(title="Find Memories by Name",
                                          readOnlyHint=True,
                                          destructiveHint=False,
                                          idempotentHint=True,
                                          openWorldHint=True))
    async def find_memories_by_name(names: list[str] = Field(..., description="List of node names to find")) -> KnowledgeGraph:
        """Find specific memories by name."""
        logger.info(f"MCP tool: find_memories_by_name ({len(names)} names)")
        try:
            result = await memory.find_memories_by_name(names)
            return ToolResult(content=[TextContent(type="text", text=result.model_dump_json())],
                              structured_content=result)
        except Neo4jError as e:
            logger.error(f"Neo4j error finding memories by name: {e}")
            raise ToolError(f"Neo4j error finding memories by name: {e}")
        except Exception as e:
            logger.error(f"Error finding memories by name: {e}")
            raise ToolError(f"Error finding memories by name: {e}")

    return mcp


async def main(
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    neo4j_database: str,
    transport: Literal["stdio", "sse", "http"] = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp/",
) -> None:
    logger.info(f"Starting Neo4j MCP Memory Server")
    logger.info(f"Connecting to Neo4j with DB URL: {neo4j_uri}")

    # Connect to Neo4j
    neo4j_driver = AsyncGraphDatabase.driver(
        neo4j_uri,
        auth=(neo4j_user, neo4j_password),
        database=neo4j_database
    )

    # Verify connection
    try:
        await neo4j_driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {neo4j_uri}")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        exit(1)

    # Initialize memory
    memory = Neo4jMemory(neo4j_driver)
    logger.info("Neo4jMemory initialized")

    # Create fulltext index
    await memory.create_fulltext_index()

    # Create MCP server
    mcp = create_mcp_server(memory)
    logger.info("MCP server created")

    # Run the server with the specified transport
    logger.info(f"Starting server with transport: {transport}")
    match transport:
        case "http":
            logger.info(f"HTTP server starting on {host}:{port}{path}")
            await mcp.run_http_async(host=host, port=port, path=path)
        case "stdio":
            logger.info("STDIO server starting")
            await mcp.run_stdio_async()
        case "sse":
            logger.info(f"SSE server starting on {host}:{port}{path}")
            await mcp.run_sse_async(host=host, port=port, path=path)
        case _:
            raise ValueError(f"Unsupported transport: {transport}")
