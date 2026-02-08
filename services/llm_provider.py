"""
LLM Provider - Interfaz agnóstica de proveedor LLM

Permite cambiar de Claude a OpenAI, Mistral, etc. sin modificar la lógica del agente.
Para añadir un nuevo proveedor, crear una clase que herede de LLMProvider e implemente chat().
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json


@dataclass
class ToolCall:
    """Representa una llamada a herramienta solicitada por el LLM"""
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    """Respuesta estandarizada de cualquier proveedor LLM"""
    text: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """
    Interfaz abstracta para proveedores LLM.

    Para soportar un nuevo LLM, implementar:
    - chat(system_prompt, messages, tools) -> LLMResponse
    """

    @abstractmethod
    def chat(
        self,
        system_prompt: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
    ) -> LLMResponse:
        """
        Envía mensajes al LLM y obtiene respuesta.

        Args:
            system_prompt: Instrucciones del sistema
            messages: Lista de mensajes [{"role": "user"|"assistant"|"tool", "content": ...}]
            tools: Definiciones de tools en formato estándar (opcional)

        Returns:
            LLMResponse con texto y/o tool_calls
        """
        pass


class AnthropicProvider(LLMProvider):
    """
    Implementación para Claude (Anthropic API).
    Traduce el formato estándar de tools al formato tool_use de Claude.
    """

    def __init__(
        self,
        model: str = "claude-3-5-haiku-20241022",
        max_tokens: int = 1024,
    ):
        import anthropic
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
        self.max_tokens = max_tokens

    def chat(
        self,
        system_prompt: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
    ) -> LLMResponse:
        # Convertir tools al formato Anthropic
        anthropic_tools = None
        if tools:
            anthropic_tools = [self._to_anthropic_tool(t) for t in tools]

        # Convertir mensajes al formato Anthropic
        anthropic_messages = self._to_anthropic_messages(messages)

        # Llamar a la API
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_prompt,
            "messages": anthropic_messages,
        }
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        response = self.client.messages.create(**kwargs)

        return self._parse_response(response)

    def _to_anthropic_tool(self, tool: Dict) -> Dict:
        """Convierte definición estándar de tool al formato Anthropic"""
        return {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["parameters"],
        }

    def _to_anthropic_messages(self, messages: List[Dict]) -> List[Dict]:
        """Convierte mensajes al formato Anthropic"""
        result = []
        for msg in messages:
            if msg["role"] == "tool":
                # Anthropic usa tool_result dentro de un mensaje user
                result.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg["tool_call_id"],
                        "content": msg["content"],
                    }],
                })
            else:
                result.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })
        return result

    def _parse_response(self, response) -> LLMResponse:
        """Parsea respuesta de Anthropic a formato estándar"""
        text = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input,
                ))

        return LLMResponse(text=text, tool_calls=tool_calls)
