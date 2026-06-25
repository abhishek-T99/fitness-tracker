"""Tool registry.

Each tool is a Python callable that takes ``(user, **kwargs)`` and returns a
JSON-serialisable result. The ``@tool`` decorator records its schema so the
runner can advertise it to Claude and dispatch tool_use blocks by name.

The ``user`` parameter is always injected from the request — handlers never
trust the model for identity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[..., Any]
    kind: str = "read"  # "read" | "write" — write tools must validate via serializers

    def to_anthropic(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class _Registry:
    tools: Dict[str, Tool] = field(default_factory=dict)

    def register(self, tool_obj: Tool) -> None:
        if tool_obj.name in self.tools:
            raise ValueError(f"Tool already registered: {tool_obj.name}")
        self.tools[tool_obj.name] = tool_obj

    def get(self, name: str) -> Tool:
        if name not in self.tools:
            raise KeyError(f"Unknown tool: {name}")
        return self.tools[name]

    def schemas(self, names: List[str]) -> List[Dict[str, Any]]:
        return [self.get(name).to_anthropic() for name in names]

    def clear(self) -> None:
        """Test-only — wipe the registry between tests if needed."""
        self.tools.clear()


REGISTRY = _Registry()


def tool(
    *,
    name: str,
    description: str,
    schema: Dict[str, Any],
    kind: str = "read",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator: register a function as a tool the agent can call.

    Schemas must be valid JSON Schema. ``kind="write"`` flags tools that
    mutate user data — they must validate input through DRF serializers.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        REGISTRY.register(
            Tool(
                name=name,
                description=description,
                input_schema=schema,
                handler=func,
                kind=kind,
            )
        )
        return func

    return decorator
