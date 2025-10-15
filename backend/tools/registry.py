"""
Tool Registry - Clean Registration Pattern (No __init__.py)

Provides a tool registry without relying on __init__.py.
Tools are registered via decorator and can be discovered automatically.

Usage:
    from backend.tools.registry import tool
    
    @tool(name="my_tool", description="...", parameters={...})
    async def my_tool_function(param: str) -> dict:
        return {"success": True, "data": "result"}
"""

from typing import Callable, Dict, Any, List
from functools import wraps


class ToolRegistry:
    """Global registry for all tools - singleton pattern."""
    
    _instance = None
    _tools: Dict[str, Callable] = {}
    _schemas: List[Dict[str, Any]] = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any]
    ) -> Callable:
        """
        Decorator to register a tool.
        
        Args:
            name: Tool name for OpenAI function calling
            description: What the tool does
            parameters: OpenAI function parameters schema
        """
        def decorator(func: Callable) -> Callable:
            # Register the function
            self._tools[name] = func
            
            # Create OpenAI function schema
            schema = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            }
            self._schemas.append(schema)
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                """Wrapper with error handling."""
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "tool_name": name,
                        "data": ""
                    }
            
            return wrapper
        
        return decorator
    
    def get_tool(self, name: str) -> Callable:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas for OpenAI."""
        return self._schemas
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())


# Singleton instance
registry = ToolRegistry()


def tool(name: str, description: str, parameters: Dict[str, Any]) -> Callable:
    """
    Decorator for registering tools.
    
    Example:
        @tool(
            name="web_search",
            description="Search the web",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        )
        async def web_search(query: str) -> dict:
            return {"success": True, "data": "results"}
    """
    return registry.register(name, description, parameters)


# Export functions
get_tool = registry.get_tool
get_all_tools = registry.get_all_schemas
list_tools = registry.list_tools
