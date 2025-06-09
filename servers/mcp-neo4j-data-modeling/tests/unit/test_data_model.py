import pytest
from pydantic import ValidationError
from typing import Any

from mcp_neo4j_data_modeling.data_model import DataModel, Node, Relationship, Property


def test_node_add_property_new():
    """Test adding a new property to a node."""
    key_prop = Property(name="id", type="string", description="Unique identifier")
    node = Node(
        label="Person",
        key_property=key_prop,
        properties=[Property(name="name", type="string", description="Full name")]
    )
    
    new_prop = Property(name="age", type="integer", description="Age in years")
    node.add_property(new_prop)
    
    assert len(node.properties) == 2
    assert any(p.name == "age" for p in node.properties)


def test_node_add_property_existing():
    """Test adding an existing property to a node should raise an error."""
    key_prop = Property(name="id", type="string", description="Unique identifier")
    node = Node(
        label="Person",
        key_property=key_prop,
        properties=[Property(name="name", type="string", description="Full name")]
    )
    
    duplicate_prop = Property(name="name", type="string", description="Another name")
    
    with pytest.raises(ValueError, match="Property name already exists"):
        node.add_property(duplicate_prop)


def test_node_remove_property():
    """Test removing a property from a node."""
    key_prop = Property(name="id", type="string", description="Unique identifier")
    name_prop = Property(name="name", type="string", description="Full name")
    age_prop = Property(name="age", type="integer", description="Age in years")
    
    node = Node(
        label="Person",
        key_property=key_prop,
        properties=[name_prop, age_prop]
    )
    
    node.remove_property(name_prop)
    
    assert len(node.properties) == 1
    assert not any(p.name == "name" for p in node.properties)

def test_node_validate_properties_key_prop_in_properties_list():
    """Test validating properties of a node when key property is in properties list."""
    key_prop = Property(name="id", type="string", description="Unique identifier")
    node = Node(
        label="Person",
        key_property=key_prop,
        properties=[Property(name="name", type="string", description="Full name"), Property(name="id", type="string", description="Unique identifier")]
    )
    
    assert len(node.properties) == 1
    assert not any(p.name == "id" for p in node.properties)

def test_node_validate_properties_dupe_property_names():
    """Test validating properties of a node when there are duplicate property names."""
    with pytest.raises(ValidationError, match="Property name appears 2 times in node Person"):
        Node(
            label="Person",
            key_property=Property(name="id", type="string", description="Unique identifier"),
            properties=[Property(name="name", type="string", description="Full name"), Property(name="name", type="string", description="Another name")]
        )
    

def test_relationship_add_property_new():
    """Test adding a new property to a relationship."""
    key_prop = Property(name="since", type="date", description="Start date")
    relationship = Relationship(
        type="KNOWS",
        start_node_label="Person",
        end_node_label="Person",
        key_property=key_prop,
        properties=[Property(name="weight", type="float", description="Relationship strength")]
    )
    
    new_prop = Property(name="context", type="string", description="How they met")
    relationship.add_property(new_prop)
    
    assert len(relationship.properties) == 2
    assert any(p.name == "context" for p in relationship.properties)


def test_relationship_add_property_existing():
    """Test adding an existing property to a relationship should raise an error."""
    relationship = Relationship(
        type="KNOWS",
        start_node_label="Person",
        end_node_label="Person",
        properties=[Property(name="weight", type="float", description="Relationship strength")]
    )
    
    duplicate_prop = Property(name="weight", type="float", description="Another weight")
    
    with pytest.raises(ValueError, match="Property weight already exists"):
        relationship.add_property(duplicate_prop)


def test_relationship_remove_property():
    """Test removing a property from a relationship."""
    weight_prop = Property(name="weight", type="float", description="Relationship strength")
    context_prop = Property(name="context", type="string", description="How they met")
    
    relationship = Relationship(
        type="KNOWS",
        start_node_label="Person",
        end_node_label="Person",
        properties=[weight_prop, context_prop]
    )
    
    relationship.remove_property(weight_prop)
    
    assert len(relationship.properties) == 1
    assert not any(p.name == "weight" for p in relationship.properties)


def test_generate_relationship_pattern():
    """Test generating relationship pattern string."""
    relationship = Relationship(
        type="KNOWS",
        start_node_label="Person",
        end_node_label="Person",
        properties=[]
    )
    
    expected_pattern = "(:Person)-[:KNOWS]->(:Person)"
    assert relationship.pattern == expected_pattern


def test_relationship_validate_properties_key_prop_in_properties_list():
    """Test validating properties of a relationship when key property is in properties list."""
    key_prop = Property(name="id", type="string", description="Unique identifier")
    relationship = Relationship(
        start_node_label="Person",
        end_node_label="Person",
        type="KNOWS",
        key_property=key_prop,
        properties=[Property(name="name", type="string", description="Full name"), Property(name="id", type="string", description="Unique identifier")]
    )
    
    assert len(relationship.properties) == 1
    assert not any(p.name == "id" for p in relationship.properties)

def test_relationship_validate_properties_dupe_property_names():
    """Test validating properties of a relationship when there are duplicate property names."""
    with pytest.raises(ValidationError, match=r"Property name appears 2 times in relationship \(:Person\)-\[:KNOWS\]->\(:Person\)"):
        Relationship(
            start_node_label="Person",
            end_node_label="Person",
            type="KNOWS",
            key_property=Property(name="id", type="string", description="Unique identifier"),
            properties=[Property(name="name", type="string", description="Full name"), Property(name="name", type="string", description="Another name")]
        )

def test_data_model_validate_nodes_valid():
    """Test data model validation with valid nodes."""
    key_prop1 = Property(name="id", type="string", description="Unique identifier")
    key_prop2 = Property(name="code", type="string", description="Company code")
    
    nodes = [
        Node(label="Person", key_property=key_prop1, properties=[]),
        Node(label="Company", key_property=key_prop2, properties=[])
    ]
    
    data_model = DataModel(nodes=nodes, relationships=[])
    
    # Should not raise an exception
    assert len(data_model.nodes) == 2


def test_data_model_validate_nodes_invalid_dupe_labels():
    """Test data model validation with duplicate node labels."""
    key_prop = Property(name="id", type="string", description="Unique identifier")
    
    nodes = [
        Node(label="Person", key_property=key_prop, properties=[]),
        Node(label="Person", key_property=key_prop, properties=[])
    ]
    
    with pytest.raises(ValidationError, match="Node with label Person appears 2 times in data model"):
        DataModel(nodes=nodes, relationships=[])


def test_data_model_validate_relationships_valid():
    """Test data model validation with valid relationships."""
    nodes = [
        Node(label="Person", key_property=Property(name="id", type="STRING", description="Unique identifier"), properties=[]),
        Node(label="Company", key_property=Property(name="id", type="STRING", description="Unique identifier"), properties=[])
    ]
    relationships = [
        Relationship(type="KNOWS", start_node_label="Person", end_node_label="Person", properties=[]),
        Relationship(type="WORKS_FOR", start_node_label="Person", end_node_label="Company", properties=[])
    ]
    
    data_model = DataModel(nodes=nodes, relationships=relationships)
    
    # Should not raise an exception
    assert len(data_model.relationships) == 2


def test_data_model_validate_relationships_invalid_dupe_patterns():
    """Test data model validation with duplicate relationship patterns."""
    relationships = [
        Relationship(type="KNOWS", start_node_label="Person", end_node_label="Person", properties=[]),
        Relationship(type="KNOWS", start_node_label="Person", end_node_label="Person", properties=[])
    ]
    with pytest.raises(ValidationError, match=r"Relationship with pattern \(:Person\)-\[:KNOWS\]->\(:Person\) appears 2 times in data model"):
        DataModel(nodes=[], relationships=relationships)

def test_data_model_validate_relationships_invalid_start_node_does_not_exist():
    """Test data model validation with a start node that does not exist."""
    nodes = [Node(
        label="Pet",
        key_property=Property(name="id", type="string", description="Unique identifier"),
    ),
    Node(
        label="Place",
        key_property=Property(name="id", type="string", description="Unique identifier"),
    )
    ]
    relationships = [
        Relationship(type="KNOWS", start_node_label="Person", end_node_label="Pet", properties=[])
    ]
    with pytest.raises(ValidationError, match=r"Relationship \(:Person\)-\[:KNOWS\]->\(:Pet\) has a start node that does not exist in data model"):
        DataModel(nodes=[], relationships=relationships)

def test_data_model_validate_relationships_invalid_end_node_does_not_exist():
    """Test data model validation with an end node that does not exist."""
    nodes = [Node(
        label="Person",
        key_property=Property(name="id", type="string", description="Unique identifier"),
    ),
    Node(
        label="Place",
        key_property=Property(name="id", type="string", description="Unique identifier"),
    )
    ]


    relationships = [
        Relationship(type="KNOWS", start_node_label="Person", end_node_label="Pet", properties=[])
    ]
    with pytest.raises(ValidationError, match=r"Relationship \(:Person\)-\[:KNOWS\]->\(:Pet\) has an end node that does not exist in data model"):
        DataModel(nodes=nodes, relationships=relationships)

def test_data_model_from_arrows(arrows_data_model_dict: dict[str, Any]):
    """Test converting an Arrows Data Model to a Data Model."""
    data_model = DataModel.from_arrows(arrows_data_model_dict)
    assert len(data_model.nodes) == 4
    assert len(data_model.relationships) == 4
    assert data_model.nodes[0].label == "Person"
    assert data_model.nodes[0].key_property.name == "name"
    assert data_model.nodes[0].key_property.type == "STRING"
    assert len(data_model.nodes[0].properties) == 1
    assert data_model.nodes[0].properties[0].name == "age"
    assert data_model.nodes[0].properties[0].type == "INTEGER"
    assert data_model.nodes[0].properties[0].description is None
    assert data_model.nodes[1].label == "Address"
    assert data_model.nodes[1].key_property.name == "fullAddress"
    assert data_model.nodes[1].key_property.type == "STRING"
    assert {"Person", "Address", "Pet", "Toy"} == {n.label for n in data_model.nodes}
    assert {"KNOWS", "HAS_ADDRESS", "HAS_PET", "PLAYS_WITH"} == {r.type for r in data_model.relationships}
