import sys
import logging
from typing import List, Dict, Any, Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger("mcp-backend")

class MCPManager:
    def __init__(self, server_script: str):
        self.server_script = server_script
        self.session: Optional[ClientSession] = None
        self.tools: list = []
        self.system_prompt: dict = {}
        self._exit_stack: Optional[AsyncExitStack] = None

    async def connect(self):
        logger.info(f"Conectando con el servidor MCP en: {self.server_script}...")
        self._exit_stack = AsyncExitStack()
        params = StdioServerParameters(command=sys.executable, args=[self.server_script])
        read, write = await self._exit_stack.enter_async_context(stdio_client(params))
        self.session = await self._exit_stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()
        self.tools = (await self.session.list_tools()).tools

        index = await self.session.call_tool("listar_indice", arguments={})
        self.system_prompt = {
            "role": "system",
            "content": (
                "Eres un historiador experto en la ciudad de Las Varillas. Responde siempre en español.\n"
                "El índice es solo un resumen. Si el usuario pregunta por algo específico (personas, "
                "fechas, teorías), DEBES llamar a la herramienta buscar_fundacion con el término o ID "
                "como parámetro 'tema'. Si la herramienta no encuentra nada, dilo con honestidad y no "
                "inventes datos.\n"
                f"ÍNDICE RESUMIDO:\n{index.content[0].text}"
            ),
        }
        logger.info("MCP conectado y listo.")

    async def disconnect(self):
        if self._exit_stack:
            await self._exit_stack.aclose()
            logger.info("MCP desconectado.")

    def get_ollama_tools(self) -> List[Dict[str, Any]]:
        return [{
            "type": "function",
            "function": {"name": t.name, "description": t.description, "parameters": t.inputSchema},
        } for t in self.tools]

    async def execute_tool(self, tool_call: dict) -> tuple[str, str]:
        fn = tool_call.get("function", tool_call)
        name = fn.get("name", "")
        try:
            import json
            args = fn.get("arguments", fn.get("parameters", {})) or {}
            if isinstance(args, str):
                args = json.loads(args)
            if name not in {t.name for t in self.tools}:
                return name, f"Error: la herramienta '{name}' no existe."
            logger.info(f"[Herramienta MCP] {name} con {args}")
            result = await self.session.call_tool(name, arguments=args)
            text = result.content[0].text if result.content else ""
            return name, (f"Error de la herramienta: {text}" if result.isError else text)
        except Exception as e:
            logger.error(f"Fallo al ejecutar herramienta {name}: {e}")
            return name, "Error: no se pudo ejecutar la herramienta."
