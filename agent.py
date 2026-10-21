import json
import re
import logging
from typing import Callable, Awaitable, Dict, Any, List
from config import MAX_ITER, MAX_HISTORY, TOOL_STATUS
from llm import LLMClient
from mcp_client import MCPManager

logger = logging.getLogger("mcp-backend")

class Agent:
    """
    Agente historiador que procesa los mensajes del usuario.
    Cumple con el principio de Inversión de Dependencias (D):
    - Recibe el cliente LLM (abstraído por el protocolo LLMClient) mediante inyección en el constructor.
    - Recibe el MCPManager mediante inyección en el constructor.
    - Desacoplado de FastAPI / WebSocket mediante una función de notificación (callback 'notify').
    """
    def __init__(self, llm: LLMClient, mcp_manager: MCPManager):
        self.llm = llm
        self.mcp_manager = mcp_manager

    @staticmethod
    def extraer_tool_calls(message: Dict[str, Any]) -> List[Dict[str, Any]]:
        tool_calls = message.get("tool_calls") or []
        content = message.get("content") or ""
        if not tool_calls and '"name"' in content:
            try:
                m = re.search(r"\{.*\}", content, re.DOTALL)
                if m:
                    j = json.loads(m.group())
                    if isinstance(j, dict) and "name" in j:
                        tool_calls = [{"function": j}]
            except json.JSONDecodeError:
                pass
        return tool_calls

    @staticmethod
    def recortar_historial(messages: List[Dict[str, Any]]) -> None:
        resto = messages[1:][-MAX_HISTORY:]
        while resto and resto[0].get("role") != "user":
            resto.pop(0)
        messages[:] = [messages[0]] + resto

    async def responder(
        self,
        messages: List[Dict[str, Any]],
        user_text: str,
        notify: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Procesa el mensaje del usuario utilizando el callback 'notify' para enviar respuestas o estados.
        Esto permite enviar datos a un WebSocket, consola o test runner sin acoplar el agente a FastAPI.
        """
        messages.append({"role": "user", "content": user_text})
        tools = self.mcp_manager.get_ollama_tools()

        for _ in range(MAX_ITER):
            # Notificación de estado mediante callback
            await notify({"type": "status", "message": "Pensando..."})
            message = await self.llm.achat(messages, tools)
            tool_calls = self.extraer_tool_calls(message)

            if not tool_calls:
                content = message.get("content") or ""
                messages.append({"role": "assistant", "content": content})
                await notify({"type": "response", "content": content})
                return

            messages.append(message)
            for tc in tool_calls:
                name = tc.get("function", tc).get("name", "")
                await notify({"type": "status", "message": TOOL_STATUS.get(name, "Consultando herramienta...")})
                name, text = await self.mcp_manager.execute_tool(tc)
                messages.append({"role": "tool", "content": text, "tool_name": name})

        await notify({
            "type": "response",
            "content": "No pude completar la consulta en el límite de pasos. Intenta reformular la pregunta.",
        })
