import argparse
import asyncio

from . import server


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description="Neo4j Data Modeling MCP Server")
    parser.add_argument("--transport", default="stdio", help="Transport type")

    args = parser.parse_args()
    asyncio.run(
        server.main(
            args.transport,
        )
    )


__all__ = ["main", "server"]
