"""Reasoning helpers for prompt templates and validation hooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class PromptTemplate:
	name: str
	template: str


class PromptRegistry:
	def __init__(self) -> None:
		self._templates: Dict[str, PromptTemplate] = {}

	def register(self, name: str, template: str) -> None:
		self._templates[name] = PromptTemplate(name=name, template=template)

	def render(self, name: str, **kwargs: str) -> str:
		if name not in self._templates:
			raise KeyError(f"Prompt template not found: {name}")
		return self._templates[name].template.format(**kwargs)


def validate_non_empty(text: str, field_name: str) -> None:
	if not text or not text.strip():
		raise ValueError(f"{field_name} must not be empty")

