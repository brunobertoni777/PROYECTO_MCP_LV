# Las Varillas Digital: MCP + FastAPI + Ollama

Chat histórico sobre el origen de Las Varillas. Un servidor MCP (`server.py`) expone
la base `fundacion.json`; el backend FastAPI (`main.py`) conecta el modelo local de
Ollama con esa herramienta y sirve la interfaz (`index.html`) por WebSocket.

## Estructura

```
├── main.py            # backend FastAPI + agente (sirve también index.html en "/")
├── server.py          # servidor MCP: listar_indice y buscar_fundacion
├── fundacion.json     # documentos históricos
├── index.html         # interfaz (sin build, sin Node)
├── assets/            # SVG del fondo, logo y engranaje
└── requirements.txt
```

## Puesta en marcha

1. Ollama con el modelo:
   ```bash
   ollama pull llama3.2
   ```
2. Entorno e instalación:
   ```bash
   python -m venv venv
   # Windows: .\venv\Scripts\activate      Mac/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Iniciar:
   ```bash
   python main.py
   ```
4. Abrir http://127.0.0.1:8000

## Configuración opcional (variables de entorno)

| Variable | Por defecto |
|---|---|
| `HOST` | `127.0.0.1` (no exponer a la red: no hay autenticación) |
| `PORT` | `8000` |
| `OLLAMA_URL` | `http://localhost:11434/api/chat` |
| `OLLAMA_MODEL` | `llama3.2` |
| `ALLOWED_ORIGINS` | `http://127.0.0.1:8000,http://localhost:8000` |

## Preguntas de prueba

- "¿A qué postura suscribe Valter Dabbene?" → 1903
- "¿Qué dice el Centro de Estudios Parada KM 81?" → 1900
- "¿Cuándo llegó el tren?" → 1904
- "Dame un resumen de las tres teorías."
