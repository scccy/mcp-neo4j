import logging
from typing import Any, Dict, List, Literal

from neo4j import AsyncGraphDatabase
from pydantic import BaseModel, Field

from fastmcp.server import FastMCP

# Set up logging
logger = logging.getLogger('mcp_neo4j_memory')
logger.setLevel(logging.INFO)

# Models for our knowledge graph
class Entity(BaseModel):
    name: str
    type: str
    observations: List[str]

class Relation(BaseModel):
    source: str
    target: str
    relationType: str

class KnowledgeGraph(BaseModel):
    entities: List[Entity]
    relations: List[Relation]

class ObservationAddition(BaseModel):
    entityName: str
    contents: List[str]

class ObservationDeletion(BaseModel):
    entityName: str
    observations: List[str]

class Neo4jMemory:
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver

    async def create_fulltext_index(self):
        """Create a fulltext search index for entities if it doesn't exist."""
        try:
            await self.driver.execute_query("""
                CALL db.index.fulltext.createNodeIndex("entity_search", ["Entity"], ["name", "type", "observations"])
            """)
            logger.info("Created fulltext search index")
        except Exception as e:
            # Index might already exist, which is fine
            logger.debug(f"Fulltext index creation: {e}")

    async def load_graph(self, filter_query="*"):
        """Load the entire knowledge graph from Neo4j."""
        logger.info("Loading knowledge graph from Neo4j")
        async with self.driver.session() as session:
            # Load all entities
            entity_result = await session.run("""
                MATCH (e:Entity)
                RETURN e.name as name, e.type as type, e.observations as observations
            """)
            
            entities = []
            async for record in entity_result:
                entities.append(Entity(
                    name=record.get("name", ""),
                    type=record.get("type", ""),
                    observations=record.get("observations") or []
                ))
            
            # Load all relations
            relation_result = await session.run("""
                MATCH (source:Entity)-[r:RELATION]->(target:Entity)
                RETURN source.name as source, target.name as target, type(r) as relationType
            """)
            
            relations = []
            async for record in relation_result:
                relations.append(Relation(
                    source=record.get("source", ""),
                    target=record.get("target", ""),
                    relationType=record.get("relationType", "")
                ))
            
            logger.info(f"Loaded {len(entities)} entities and {len(relations)} relations")
            
            return KnowledgeGraph(entities=entities, relations=relations)

    async def create_entities(self, entities: List[Entity]) -> List[Entity]:
        """Create multiple new entities in the knowledge graph."""
        logger.info(f"Creating {len(entities)} entities")
        async with self.driver.session() as session:
            for entity in entities:
                await session.run("""
                    MERGE (e:Entity {name: $name})
                    SET e.type = $type, e.observations = $observations
                """, name=entity.name, type=entity.type, observations=entity.observations)
            logger.info(f"Successfully created {len(entities)} entities")
            return entities

    async def create_relations(self, relations: List[Relation]) -> List[Relation]:
        """Create multiple new relations between entities."""
        logger.info(f"Creating {len(relations)} relations")
        async with self.driver.session() as session:
            for relation in relations:
                await session.run("""
                    MATCH (source:Entity {name: $source})
                    MATCH (target:Entity {name: $target})
                    MERGE (source)-[r:RELATION]->(target)
                    SET r.relationType = $relationType
                """, source=relation.source, target=relation.target, relationType=relation.relationType)
            logger.info(f"Successfully created {len(relations)} relations")
            return relations

    async def add_observations(self, observations: List[ObservationAddition]) -> List[Dict[str, Any]]:
        """Add new observations to existing entities."""
        logger.info(f"Adding observations to {len(observations)} entities")
        results = []
        async with self.driver.session() as session:
            for obs in observations:
                await session.run("""
                    MATCH (e:Entity {name: $entityName})
                    SET e.observations = CASE 
                        WHEN e.observations IS NULL THEN $contents
                        ELSE e.observations + $contents
                    END
                """, entityName=obs.entityName, contents=obs.contents)
                results.append({"entity": obs.entityName, "added_observations": obs.contents})
        logger.info(f"Successfully added observations to {len(observations)} entities")
        return results

    async def delete_entities(self, entity_names: List[str]) -> None:
        """Delete multiple entities and their associated relations."""
        logger.info(f"Deleting {len(entity_names)} entities")
        async with self.driver.session() as session:
            await session.run("""
                MATCH (e:Entity)
                WHERE e.name IN $entityNames
                DETACH DELETE e
            """, entityNames=entity_names)
        logger.info(f"Successfully deleted {len(entity_names)} entities")

    async def delete_observations(self, deletions: List[ObservationDeletion]) -> None:
        """Delete specific observations from entities."""
        logger.info(f"Deleting observations from {len(deletions)} entities")
        async with self.driver.session() as session:
            for deletion in deletions:
                await session.run("""
                    MATCH (e:Entity {name: $entityName})
                    SET e.observations = [obs IN e.observations WHERE NOT obs IN $observations]
                """, entityName=deletion.entityName, observations=deletion.observations)
        logger.info(f"Successfully deleted observations from {len(deletions)} entities")

    async def delete_relations(self, relations: List[Relation]) -> None:
        """Delete multiple relations from the graph."""
        logger.info(f"Deleting {len(relations)} relations")
        async with self.driver.session() as session:
            for relation in relations:
                await session.run("""
                    MATCH (source:Entity {name: $source})-[r:RELATION]->(target:Entity {name: $target})
                    DELETE r
                """, source=relation.source, target=relation.target)
        logger.info(f"Successfully deleted {len(relations)} relations")

    async def read_graph(self) -> KnowledgeGraph:
        """Read the entire knowledge graph."""
        return await self.load_graph()

    async def search_nodes(self, query: str) -> KnowledgeGraph:
        """Search for nodes based on a query."""
        logger.info(f"Searching for nodes with query: '{query}'")
        async with self.driver.session() as session:
            # Use fulltext search if available, otherwise fallback to simple text search
            try:
                result = await session.run("""
                    CALL db.index.fulltext.queryNodes("entity_search", $query)
                    YIELD node
                    RETURN node.name as name, node.type as type, node.observations as observations
                """, query=query)
                logger.debug("Using fulltext search index")
            except:
                # Fallback to simple text search
                result = await session.run("""
                    MATCH (e:Entity)
                    WHERE e.name CONTAINS $q OR e.type CONTAINS $q OR ANY(obs IN e.observations WHERE obs CONTAINS $q)
                    RETURN e.name as name, e.type as type, e.observations as observations
                """, q=query)
                logger.debug("Using fallback text search")
            
            entities = []
            async for record in result:
                entities.append(Entity(
                    name=record.get("name", ""),
                    type=record.get("type", ""),
                    observations=record.get("observations") or []
                ))
            
            # Get relations for found entities
            if entities:
                entity_names = [e.name for e in entities]
                relation_result = await session.run("""
                    MATCH (source:Entity)-[r:RELATION]->(target:Entity)
                    WHERE source.name IN $entityNames OR target.name IN $entityNames
                    RETURN source.name as source, target.name as target, type(r) as relationType
                """, entityNames=entity_names)
                
                relations = []
                async for record in relation_result:
                    relations.append(Relation(
                        source=record.get("source", ""),
                        target=record.get("target", ""),
                        relationType=record.get("relationType", "")
                    ))
            else:
                relations = []
            
            logger.info(f"Search found {len(entities)} entities and {len(relations)} relations")
            return KnowledgeGraph(entities=entities, relations=relations)

    async def find_nodes(self, names: List[str]) -> KnowledgeGraph:
        """Find specific nodes by their names."""
        logger.info(f"Finding {len(names)} nodes by name")
        async with self.driver.session() as session:
            # Load specified entities
            entity_result = await session.run("""
                MATCH (e:Entity)
                WHERE e.name IN $names
                RETURN e.name as name, e.type as type, e.observations as observations
            """, names=names)
            
            entities = []
            async for record in entity_result:
                entities.append(Entity(
                    name=record.get("name", ""),
                    type=record.get("type", ""),
                    observations=record.get("observations") or []
                ))
            
            # Get relations for found entities
            if entities:
                relation_result = await session.run("""
                    MATCH (source:Entity)-[r:RELATION]->(target:Entity)
                    WHERE source.name IN $names OR target.name IN $names
                    RETURN source.name as source, target.name as target, type(r) as relationType
                """, names=names)
                
                relations = []
                async for record in relation_result:
                    relations.append(Relation(
                        source=record.get("source", ""),
                        target=record.get("target", ""),
                        relationType=record.get("relationType", "")
                    ))
            else:
                relations = []
            
            logger.info(f"Found {len(entities)} entities and {len(relations)} relations")
            return KnowledgeGraph(entities=entities, relations=relations)


def create_mcp_server(neo4j_driver, memory: Neo4jMemory) -> FastMCP:
    """Create an MCP server instance for memory management."""
    
    mcp: FastMCP = FastMCP("mcp-neo4j-memory", dependencies=["neo4j", "pydantic"], stateless_http=True)

    @mcp.tool()
    async def read_graph() -> dict:
        """Read the entire knowledge graph."""
        logger.info("MCP tool: read_graph")
        result = await memory.read_graph()
        return result.model_dump()

    @mcp.tool()
    async def create_entities(entities: List[Dict[str, Any]] = Field(..., description="List of entities to create")) -> list[dict]:
        """Create multiple new entities in the knowledge graph."""
        logger.info(f"MCP tool: create_entities ({len(entities)} entities)")
        entity_objects = [Entity(**entity) for entity in entities]
        result = await memory.create_entities(entity_objects)
        return [e.model_dump() for e in result]

    @mcp.tool()
    async def create_relations(relations: List[Dict[str, Any]] = Field(..., description="List of relations to create")) -> list[dict]:
        """Create multiple new relations between entities."""
        logger.info(f"MCP tool: create_relations ({len(relations)} relations)")
        relation_objects = [Relation(**relation) for relation in relations]
        result = await memory.create_relations(relation_objects)
        return [r.model_dump() for r in result]

    @mcp.tool()
    async def add_observations(observations: List[Dict[str, Any]] = Field(..., description="List of observations to add")) -> list[dict]:
        """Add new observations to existing entities."""
        logger.info(f"MCP tool: add_observations ({len(observations)} additions)")
        observation_objects = [ObservationAddition(**obs) for obs in observations]
        result = await memory.add_observations(observation_objects)
        return result

    @mcp.tool()
    async def delete_entities(entityNames: List[str] = Field(..., description="List of entity names to delete")) -> str:
        """Delete multiple entities and their associated relations."""
        logger.info(f"MCP tool: delete_entities ({len(entityNames)} entities)")
        await memory.delete_entities(entityNames)
        return "Entities deleted successfully"

    @mcp.tool()
    async def delete_observations(deletions: List[Dict[str, Any]] = Field(..., description="List of observations to delete")) -> str:
        """Delete specific observations from entities."""
        logger.info(f"MCP tool: delete_observations ({len(deletions)} deletions)")
        deletion_objects = [ObservationDeletion(**deletion) for deletion in deletions]
        await memory.delete_observations(deletion_objects)
        return "Observations deleted successfully"

    @mcp.tool()
    async def delete_relations(relations: List[Dict[str, Any]] = Field(..., description="List of relations to delete")) -> str:
        """Delete multiple relations from the graph."""
        logger.info(f"MCP tool: delete_relations ({len(relations)} relations)")
        relation_objects = [Relation(**relation) for relation in relations]
        await memory.delete_relations(relation_objects)
        return "Relations deleted successfully"

    @mcp.tool()
    async def search_nodes(query: str = Field(..., description="Search query for nodes")) -> dict:
        """Search for nodes based on a query."""
        logger.info(f"MCP tool: search_nodes ('{query}')")
        result = await memory.search_nodes(query)
        return result.model_dump()

    @mcp.tool()
    async def find_nodes(names: List[str] = Field(..., description="List of node names to find")) -> dict:
        """Find specific nodes by name."""
        logger.info(f"MCP tool: find_nodes ({len(names)} names)")
        result = await memory.find_nodes(names)
        return result.model_dump()

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
    mcp = create_mcp_server(neo4j_driver, memory)
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
