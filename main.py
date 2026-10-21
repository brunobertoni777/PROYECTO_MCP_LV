import os
import json
import logging
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import (
    SERVER_SCRIPT, INDEX_FILE, ASSETS_DIR,
    HOST, PORT, OLLAMA_URL, MODELO, ALLOWED_ORIGINS, MAX_MSG_CHARS
)
from llm import OllamaClient
from mcp_client import MCPManager
from agent import Agent
from repository import FundacionRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mcp-backend")

mcp_manager = MCPManager(SERVER_SCRIPT)
llm_client = OllamaClient(OLLAMA_URL, MODELO)
agent = Agent(llm=llm_client, mcp_manager=mcp_manager)
fundacion_repo = FundacionRepository()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await mcp_manager.connect()
    yield
    await mcp_manager.disconnect()

app = FastAPI(lifespan=lifespan)

# ---------- Endpoints HTTP ----------
@app.get("/")
async def read_index():
    if not os.path.exists(INDEX_FILE):
        raise HTTPException(status_code=404, detail="index.html no encontrado.")
    return FileResponse(INDEX_FILE, media_type="text/html")

@app.get("/api/fundacion")
def get_fundacion():
    try:
        data = fundacion_repo.get_all()
        if not data:
            raise HTTPException(status_code=404, detail="Archivo de datos no encontrado o vacío.")
        full_text = fundacion_repo.get_full_text()
        return {"raw": data, "full_text": full_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer los datos: {str(e)}")

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    origin = websocket.headers.get("origin")
    if origin is not None and origin not in ALLOWED_ORIGINS:
        logger.warning(f"WebSocket rechazado, origen no permitido: {origin}")
        await websocket.close(code=1008)
        return

    await websocket.accept()
    logger.info("WebSocket: cliente conectado")
    messages = [mcp_manager.system_prompt]

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                user_text = str(json.loads(raw)["text"]).strip()
                if not user_text:
                    continue
                if len(user_text) > MAX_MSG_CHARS:
                    await websocket.send_json({"type": "error", "message": f"El mensaje supera los {MAX_MSG_CHARS} caracteres."})
                    continue
                
                await agent.responder(messages, user_text, notify=websocket.send_json)
                agent.recortar_historial(messages)
            except WebSocketDisconnect:
                raise
            except (json.JSONDecodeError, KeyError, TypeError):
                await websocket.send_json({"type": "error", "message": "Mensaje inválido."})
            except requests.RequestException as e:
                logger.error(f"Ollama no respondió: {e}")
                await websocket.send_json({"type": "error", "message": "No se pudo contactar al modelo (¿Ollama está corriendo?)."})
            except Exception as e:
                logger.exception(f"Error procesando mensaje: {e}")
                await websocket.send_json({"type": "error", "message": "Ocurrió un error interno."})
    except WebSocketDisconnect:
        logger.info("WebSocket: cliente desconectado")

if os.path.isdir(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
else:
    logger.warning(f"No existe la carpeta de assets: {ASSETS_DIR} (la página se verá sin fondo ni logo)")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
