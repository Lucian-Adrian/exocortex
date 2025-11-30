"""
Script to generate OpenAPI specification from FastAPI app.

Usage:
    python scripts/generate_openapi.py

Outputs:
    docs/api/openapi.json
"""

import json
from pathlib import Path

from exo.api.app import app


def main() -> None:
    """Generate OpenAPI specification."""
    # Get OpenAPI schema from FastAPI
    openapi_schema = app.openapi()
    
    # Update metadata
    openapi_schema["info"]["title"] = "Exo API"
    openapi_schema["info"]["description"] = """
    Executive OS - Personal Knowledge Memory System API.
    
    ## Features
    
    - **Memories**: Ingest and retrieve knowledge
    - **Query**: Semantic search with AI-generated answers
    - **Commitments**: Track promises and obligations
    - **Webhooks**: n8n-compatible endpoints for automation
    
    ## Authentication
    
    All endpoints (except /health) require the `X-API-Key` header.
    
    ```bash
    curl -H "X-API-Key: your-key" http://localhost:8000/api/memories
    ```
    """
    openapi_schema["info"]["version"] = "1.0.0"
    openapi_schema["info"]["contact"] = {
        "name": "Exo Team",
        "url": "https://github.com/lucian-adrian/exocortex",
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
    
    # Add security scheme
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication",
        }
    }
    
    # Apply security globally (except health)
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    
    # Output path
    output_path = Path(__file__).parent.parent / "docs" / "api" / "openapi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"✅ OpenAPI spec written to {output_path}")
    print(f"   {len(openapi_schema.get('paths', {}))} endpoints documented")


if __name__ == "__main__":
    main()
