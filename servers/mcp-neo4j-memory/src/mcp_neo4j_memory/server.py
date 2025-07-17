import logging
from typing import Any, Dict, List, Literal

from neo4j import AsyncGraphDatabase, AsyncDriver, RoutingControl
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
    observations: List[str]

class ObservationDeletion(BaseModel):
    entityName: str
    observations: List[str]

class Neo4jMemory:
    def __init__(self, neo4j_driver: AsyncDriver):
        self.driver = neo4j_driver

    async def create_fulltext_index(self):
        """Create a fulltext search index for entities if it doesn't exist."""
        try:
            query = "CREATE FULLTEXT INDEX search IF NOT EXISTS FOR (m:Memory) ON EACH [m.name, m.type, m.observations];"
            await self.driver.execute_query(query, routing_control=RoutingControl.WRITE)
            logger.info("Created fulltext search index")
        except Exception as e:
            # Index might already exist, which is fine
            logger.debug(f"Fulltext index creation: {e}")

    async def load_graph(self, filter_query: str = "*"):
        """Load the entire knowledge graph from Neo4j."""
        logger.info("Loading knowledge graph from Neo4j")
        query = """
            CALL db.index.fulltext.queryNodes('search', $filter) yield node as entity, score
            OPTIONAL MATCH (entity)-[r]-(other)
            RETURN collect(distinct {
                name: entity.name, 
                type: entity.type, 
                observations: entity.observations
            }) as nodes,
            collect(distinct {
                source: startNode(r).name, 
                target: endNode(r).name, 
                relationType: type(r)
            }) as relations
        """
        
        result = await self.driver.execute_query(query, {"filter": filter_query}, routing_control=RoutingControl.READ)
        
        if not result.records:
            return KnowledgeGraph(entities=[], relations=[])
        
        record = result.records[0]
        nodes = record.get('nodes', list())
        rels = record.get('relations', list())
        
        entities = [
            Entity(
                name=node['name'],
                type=node['type'],
                observations=node.get('observations', list())
            )
            for node in nodes if node.get('name')
        ]
        
        relations = [
            Relation(
                source=rel['source'],
                target=rel['target'],
                relationType=rel['relationType']
            )
            for rel in rels if rel.get('relationType')
        ]
        
        logger.debug(f"Loaded entities: {entities}")
        logger.debug(f"Loaded relations: {relations}")
        
        return KnowledgeGraph(entities=entities, relations=relations)

    async def create_entities(self, entities: List[Entity]) -> List[Entity]:
        """Create multiple new entities in the knowledge graph."""
        logger.info(f"Creating {len(entities)} entities")
        for entity in entities:
            query = f"""
            WITH $entity as entity
            MERGE (e:Memory {{ name: entity.name }})
            SET e += entity {{ .type, .observations }}
            SET e:{entity.type}
            """
            await self.driver.execute_query(query, {"entity": entity.model_dump()}, routing_control=RoutingControl.WRITE)

        return entities

    async def create_relations(self, relations: List[Relation]) -> List[Relation]:
        """Create multiple new relations between entities."""
        logger.info(f"Creating {len(relations)} relations")
        for relation in relations:
            query = f"""
            WITH $relation as relation
            MATCH (from:Memory),(to:Memory)
            WHERE from.name = relation.source
            AND  to.name = relation.target
            MERGE (from)-[r:{relation.relationType}]->(to)
            """
            
            await self.driver.execute_query(
                query, 
                {"relation": relation.model_dump()},
                routing_control=RoutingControl.WRITE
            )

        return relations

    async def add_observations(self, observations: List[ObservationAddition]) -> List[Dict[str, Any]]:
        """Add new observations to existing entities."""
        logger.info(f"Adding observations to {len(observations)} entities")
        query = """
        UNWIND $observations as obs  
        MATCH (e:Memory { name: obs.entityName })
        WITH e, [o in obs.observations WHERE NOT o IN e.observations] as new
        SET e.observations = coalesce(e.observations,[]) + new
        RETURN e.name as name, new
        """
            
        result = await self.driver.execute_query(
            query, 
            {"observations": [obs.model_dump() for obs in observations]},
            routing_control=RoutingControl.WRITE
        )

        results = [{"entityName": record.get("name"), "addedObservations": record.get("new")} for record in result.records]
        return results

    async def delete_entities(self, entity_names: List[str]) -> None:
        """Delete multiple entities and their associated relations."""
        logger.info(f"Deleting {len(entity_names)} entities")
        query = """
        UNWIND $entities as name
        MATCH (e:Memory { name: name })
        DETACH DELETE e
        """
        
        await self.driver.execute_query(query, {"entities": entity_names}, routing_control=RoutingControl.WRITE)
        logger.info(f"Successfully deleted {len(entity_names)} entities")

    async def delete_observations(self, deletions: List[ObservationDeletion]) -> None:
        """Delete specific observations from entities."""
        logger.info(f"Deleting observations from {len(deletions)} entities")
        query = """
        UNWIND $deletions as d  
        MATCH (e:Memory { name: d.entityName })
        SET e.observations = [o in coalesce(e.observations,[]) WHERE NOT o IN d.observations]
        """
        await self.driver.execute_query(
            query, 
            {"deletions": [deletion.model_dump() for deletion in deletions]},
            routing_control=RoutingControl.WRITE
        )
        logger.info(f"Successfully deleted observations from {len(deletions)} entities")

    async def delete_relations(self, relations: List[Relation]) -> None:
        """Delete multiple relations from the graph."""
        logger.info(f"Deleting {len(relations)} relations")
        for relation in relations:
            query = f"""
            WITH $relation as relation
            MATCH (source:Memory)-[r:{relation.relationType}]->(target:Memory)
            WHERE source.name = relation.source
            AND target.name = relation.target
            DELETE r
            """
            await self.driver.execute_query(
                query, 
                {"relation": relation.model_dump()},
                routing_control=RoutingControl.WRITE
            )
        logger.info(f"Successfully deleted {len(relations)} relations")

    async def read_graph(self) -> KnowledgeGraph:
        """Read the entire knowledge graph."""
        return await self.load_graph()

    async def search_memories(self, query: str) -> KnowledgeGraph:
        """Search for memories based on a query with Fulltext Search."""
        logger.info(f"Searching for memories with query: '{query}'")
        return await self.load_graph(query)

    async def find_memories_by_name(self, names: List[str]) -> KnowledgeGraph:
        """Find specific memories by their names. This does not use fulltext search."""
        logger.info(f"Finding {len(names)} memories by name")
        query = """
        MATCH (e:Memory)
        WHERE e.name IN $names
        RETURN  e.name as name, 
                e.type as type, 
                e.observations as observations
        """
        result_nodes = await self.driver.execute_query(query, {"names": names}, routing_control=RoutingControl.READ)
        entities: list[Entity] = list()
        for record in result_nodes.records:
            entities.append(Entity(
                name=record['name'],
                type=record['type'],
                observations=record.get('observations', list())
            ))
        
        # Get relations for found entities
        relations: list[Relation] = list()
        if entities:
            query = """
            MATCH (source:Memory)-[r]->(target:Memory)
            WHERE source.name IN $names OR target.name IN $names
            RETURN  source.name as source, 
                    target.name as target, 
                    type(r) as relationType
            """
            result_relations = await self.driver.execute_query(query, {"names": names}, routing_control=RoutingControl.READ)
            for record in result_relations.records:
                relations.append(Relation(
                    source=record["source"],
                    target=record["target"],
                    relationType=record["relationType"]
                ))
        
        logger.info(f"Found {len(entities)} entities and {len(relations)} relations")
        return KnowledgeGraph(entities=entities, relations=relations)


def create_mcp_server(memory: Neo4jMemory) -> FastMCP:
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
    async def search_memories(query: str = Field(..., description="Search query for nodes")) -> dict:
        """Search for memories based on a query containing search terms."""
        logger.info(f"MCP tool: search_memories ('{query}')")
        result = await memory.search_memories(query)
        return result.model_dump()

    @mcp.tool()
    async def find_memories_by_name(names: List[str] = Field(..., description="List of node names to find")) -> dict:
        """Find specific memories by name."""
        logger.info(f"MCP tool: find_memories_by_name ({len(names)} names)")
        result = await memory.find_memories_by_name(names)
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
