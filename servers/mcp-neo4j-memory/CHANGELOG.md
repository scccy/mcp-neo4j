## Next

### Fixed
* Fix bug in `search_nodes` method where query arg wasn't passed properly
* Fix bug where stdio transport was always selected

### Changed
* Implement FastMCP with function decorators to simplify server code
* Add HTTP transport option
* Migrate to FastMCP v2.x

### Added
* Add compatibility for NEO4J_URI and NEO4J_URL env variables

## v0.1.5

### Fixed
* Remove use of dynamic node labels and relationship types to be compatible with Neo4j versions < 5.26

## v0.1.4

* Create, Read, Update and Delete semantic memories