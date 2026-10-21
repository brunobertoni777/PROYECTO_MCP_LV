import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_SCRIPT = os.path.join(BASE_DIR, "server.py")
DATA_FILE = os.path.join(BASE_DIR, "fundacion.json")
INDEX_FILE = os.path.join(BASE_DIR, "index.html")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODELO = os.getenv("OLLAMA_MODEL", "llama3.2")
ALLOWED_ORIGINS = {o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS", f"http://127.0.0.1:{PORT},http://localhost:{PORT}").split(",")}

MAX_ITER = 5
MAX_MSG_CHARS = 2000
MAX_HISTORY = 20

TOOL_STATUS = {
    "buscar_fundacion": "Consultando base histórica...",
    "listar_indice": "Revisando el índice...",
}
