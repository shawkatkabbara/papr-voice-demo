"""
Tool call schemas for OpenAI Realtime API using Pydantic types from PAPR SDK.

This module provides JSON Schema generation for tool calls and validation
using the official PAPR SDK types.
"""

from pydantic import BaseModel, Field
from typing import Optional


class SearchMemoryToolParams(BaseModel):
    """
    Parameters for search_papr_memories tool call.

    Based on MemorySearchParams from papr-pythonSDK, but simplified for
    tool calling use case.
    """
    query: str = Field(
        ...,
        description=(
            "A detailed search query (at least 2 sentences) describing exactly what to find "
            "in the user's memories. For best results, write 2-3 sentences that include "
            "specific details, context, and time frame. Examples: 'Find recurring customer "
            "complaints about API performance from the last month. Focus on issues where "
            "customers specifically mentioned timeout errors or slow response times.' "
            "'What are the main issues and blockers in my current projects? Focus on "
            "technical challenges and timeline impacts.'"
        ),
        min_length=1
    )

    enable_agentic_graph: Optional[bool] = Field(
        default=False,
        description=(
            "Enable agentic graph search for intelligent, context-aware results. "
            "When enabled, the system can understand ambiguous references by first "
            "identifying specific entities from your memory graph, then performing "
            "targeted searches. Examples: 'customer feedback' → identifies your customers "
            "first, then finds their specific feedback; 'project issues' → identifies your "
            "projects first, then finds related issues. This provides much more relevant "
            "and comprehensive results. Set to false for faster, simpler keyword-based search."
        )
    )


def get_search_memory_tool_schema() -> dict:
    """
    Generate OpenAI Realtime API compatible tool schema for memory search.

    Returns:
        dict: JSON Schema compatible with OpenAI Realtime API tools format
    """
    # Get the Pydantic model schema
    pydantic_schema = SearchMemoryToolParams.model_json_schema()

    # Convert to OpenAI tool format
    return {
        "type": "function",
        "name": "search_papr_memories",
        "description": "Search the user's personal memory database using semantic search with optional graph traversal",
        "parameters": {
            "type": "object",
            "properties": pydantic_schema["properties"],
            "required": pydantic_schema.get("required", ["query"])
        }
    }


def validate_search_params(params: dict) -> SearchMemoryToolParams:
    """
    Validate and parse search parameters using Pydantic.

    Args:
        params: Raw parameters from tool call

    Returns:
        SearchMemoryToolParams: Validated parameters

    Raises:
        ValidationError: If parameters are invalid
    """
    return SearchMemoryToolParams(**params)


if __name__ == "__main__":
    # Test schema generation
    import json
    schema = get_search_memory_tool_schema()
    print("OpenAI Tool Schema:")
    print(json.dumps(schema, indent=2))

    # Test validation
    print("\n✅ Testing valid params:")
    valid_params = {
        "query": "What are my current project priorities and blockers?",
        "enable_agentic_graph": True
    }
    validated = validate_search_params(valid_params)
    print(f"Validated: {validated}")

    print("\n✅ Testing minimal params:")
    minimal_params = {"query": "test query"}
    validated_minimal = validate_search_params(minimal_params)
    print(f"Validated: {validated_minimal}")
