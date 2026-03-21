"""Reasoning helpers for prompt templates and validation hooks."""

from __future__ import annotations

from dataclasses import dataclass
from string import Formatter
from typing import Any, Dict, Iterable


def _extract_template_fields(template: str) -> set[str]:
    fields: set[str] = set()
    formatter = Formatter()
    for _, field_name, _, _ in formatter.parse(template):
        if field_name:
            # "user.name" -> "user", "items[0]" -> "items"
            head = field_name.split(".", 1)[0].split("[", 1)[0].strip()
            if head:
                fields.add(head)
    return fields


@dataclass
class PromptTemplate:
    name: str
    template: str
    required_vars: tuple[str, ...] = ()


class PromptRegistry:
    def __init__(self) -> None:
        self._templates: Dict[str, PromptTemplate] = {}

    def register(
        self,
        name: str,
        template: str,
        required_vars: Iterable[str] | None = None,
    ) -> None:
        inferred = tuple(sorted(_extract_template_fields(template)))
        declared = tuple(required_vars or inferred)
        self._templates[name] = PromptTemplate(
            name=name,
            template=template,
            required_vars=declared,
        )

    def render(self, name: str, **kwargs: str) -> str:
        if name not in self._templates:
            raise KeyError(f"Prompt template not found: {name}")

        prompt = self._templates[name]
        missing = [key for key in prompt.required_vars if key not in kwargs]
        if missing:
            raise ValueError(
                f"Missing prompt variables for '{name}': {', '.join(missing)}"
            )
        return prompt.template.format(**kwargs)

    def list_templates(self) -> list[str]:
        return sorted(self._templates.keys())

    def has_template(self, name: str) -> bool:
        return name in self._templates


def validate_non_empty(text: str, field_name: str) -> None:
    if not text or not text.strip():
        raise ValueError(f"{field_name} must not be empty")


def validate_dict_payload(payload: Any, field_name: str) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{field_name} must be a dict")
    return payload


def validate_confidence(value: float, field_name: str = "confidence") -> float:
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")
    return value

