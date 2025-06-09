from pydantic import BaseModel, Field, field_validator
from collections import Counter
import neo4j_viz as nvl

class PropertySource(BaseModel):
    "The source of a property."
    column_name: str | None = Field(default=None, description="The column name this property maps to, if known.")
    table_name: str | None = Field(default=None, description="The name of the table this property's column is in, if known. May also be the name of a file.")

class Property(BaseModel):
    "A Neo4j Property."
    name: str = Field(description="The name of the property")
    type: str = Field(description="The Neo4j type of the property")
    source: PropertySource | None = Field(default=None, description="The source of the property, if known.")
    description: str = Field(description="The description of the property")

class Node(BaseModel):
    "A Neo4j Node."
    label: str = Field(description="The label of the node")
    key_property: Property = Field(description="The key property of the node")
    properties: list[Property] = Field(description="The properties of the node")

    def add_property(self, prop: Property) -> None:
        "Add a new property to the node."
        if prop.name in [p.name for p in self.properties]:
            raise ValueError(f"Property {prop.name} already exists in node {self.label}")
        self.properties.append(prop)

    def remove_property(self, prop: Property) -> None:
        "Remove a property from the node."
        try:
            self.properties.remove(prop)
        except ValueError:
            pass
    
    @property
    def all_properties_dict(self) -> dict[str, str]:
        "Return a dictionary of all properties of the node. {property_name: property_type}"
        props = {p.name: p.type for p in self.properties} if self.properties else {}
        if self.key_property:
            props.update({self.key_property.name: f"{self.key_property.type} | KEY"})
        return props
    
    def to_nvl(self) -> nvl.Node:
        return nvl.Node(id=self.label, caption=self.label, size=20, caption_size=1, properties=self.all_properties_dict)

class Relationship(BaseModel):
    "A Neo4j Relationship."
    type: str = Field(description="The type of the relationship")
    start_node_label: str = Field(description="The label of the start node")
    end_node_label: str = Field(description="The label of the end node")
    key_property: Property | None = Field(default=None, description="The key property of the relationship, if any.")
    properties: list[Property] = Field(default_factory=list, description="The properties of the relationship")

    def add_property(self, prop: Property) -> None:
        "Add a new property to the relationship."
        if prop.name in [p.name for p in self.properties]:
            raise ValueError(f"Property {prop.name} already exists in relationship {self.type}")
        self.properties.append(prop)

    def remove_property(self, prop: Property) -> None:
        "Remove a property from the relationship."
        try:
            self.properties.remove(prop)
        except ValueError:
            pass
    
    def pattern(self) -> str:
        "Return the pattern of the relationship."
        return f"{self.start_node_label} -[:{self.type}]-> {self.end_node_label}"
    
    @property
    def all_properties_dict(self) -> dict[str, str]:
        "Return a dictionary of all properties of the relationship. {property_name: property_type}"

        props = {p.name: p.type for p in self.properties} if self.properties else {}
        if self.key_property:
            props.update({self.key_property.name: f"{self.key_property.type} | KEY"})
        return props

    def to_nvl(self) -> nvl.Relationship:
        return nvl.Relationship(source=self.start_node_label, target=self.end_node_label, caption=self.type, properties=self.all_properties_dict)

class DataModel(BaseModel):
    "A Neo4j Graph Data Model."
    nodes: list[Node] = Field(default_factory=list, description="The nodes of the data model")
    relationships: list[Relationship] = Field(default_factory=list, description="The relationships of the data model")

    def add_node(self, node: Node) -> None:
        "Add a new node to the data model."
        if node.label in [n.label for n in self.nodes]:
            raise ValueError(f"Node with label {node.label} already exists in data model")
        self.nodes.append(node)

    def add_relationship(self, relationship: Relationship) -> None:
        "Add a new relationship to the data model."
        if relationship.pattern() in [r.pattern() for r in self.relationships]:
            raise ValueError(f"Relationship {relationship.pattern()} already exists in data model")
        self.relationships.append(relationship)

    def remove_node(self, node_label: str) -> None:
        "Remove a node from the data model."
        try:
            [self.nodes.remove(x) for x in self.nodes if x.label == node_label]
        except ValueError:
            pass
    
    def remove_relationship(self, relationship_type: str, relationship_start_node_label: str, relationship_end_node_label: str) -> None:
        "Remove a relationship from the data model."
        pattern = f"(:{relationship_start_node_label})-[:{relationship_type}]->(:{relationship_end_node_label})"
        try:
            [self.relationships.remove(x) for x in self.relationships if x.pattern() == pattern]
        except ValueError:
            pass
    
    def to_nvl(self) -> nvl.VisualizationGraph:
        return nvl.VisualizationGraph(nodes=[n.to_nvl() for n in self.nodes], relationships=[r.to_nvl() for r in self.relationships])

    @field_validator("nodes")
    def validate_nodes(cls, nodes: list[Node]) -> list[Node]:
        "Validate the nodes."

        counts = Counter([n.label for n in nodes])
        for label, count in counts.items():
            if count > 1:
                raise ValueError(f"Node with label {label} appears {count} times in data model")
        return nodes
    
    @field_validator("relationships")
    def validate_relationships(cls, relationships: list[Relationship]) -> list[Relationship]:
        "Validate the relationships."

        counts = Counter([r.pattern() for r in relationships])
        for pattern, count in counts.items():
            if count > 1:
                raise ValueError(f"Relationship with pattern {pattern} appears {count} times in data model")
        return relationships
    

