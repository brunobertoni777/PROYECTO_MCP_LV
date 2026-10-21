import asyncio
from typing import Protocol, List, Dict, Any, runtime_checkable
import requests

@runtime_checkable
class LLMClient(Protocol):
    """Contrato formal para clientes de LLM (Modelos de Lenguaje)."""

    async def achat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Envia mensajes y herramientas al LLM de forma asíncrona y devuelve la respuesta del asistente."""
        ...


class OllamaClient:
    """Implementación concreta del cliente LLM para Ollama."""

    def __init__(self, url: str, model: str, timeout: int = 300):
        self.url = url
        self.model = model
        self.timeout = timeout

    def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "stream": False,
        }
        resp = requests.post(self.url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["message"]

    async def achat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        return await asyncio.to_thread(self.chat, messages, tools)
