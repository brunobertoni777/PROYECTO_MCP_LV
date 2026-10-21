import os
import re
from mcp.server.fastmcp import FastMCP
from repository import FundacionRepository

mcp = FastMCP("HistoriaVarillas")
repo = FundacionRepository()
MAX_RESULTADOS = 3

STOPWORDS = {"de", "la", "el", "los", "las", "un", "una", "que", "en", "y", "a",
             "del", "con", "por", "para", "al", "es", "se", "su", "sus", "lo",
             "quien", "quién", "cual", "cuál", "cuando", "cuándo", "como", "cómo"}

@mcp.tool()
def listar_indice() -> str:
    """Lista el índice de la biblioteca histórica de Las Varillas: ID, título y tags
    de cada documento. No trae el contenido completo."""
    try:
        data = repo.get_all()
    except (OSError, json.JSONDecodeError) as e:
        return f"Error al leer la base histórica: {type(e).__name__}"
    out = "ÍNDICE DEL ARCHIVO HISTÓRICO:\n\n"
    for d in data:
        out += f"- ID: {d['id']} | Título: {d['titulo']}\n  Tags: {', '.join(d['tags'])}\n"
    return out

@mcp.tool()
def buscar_fundacion(tema: str) -> str:
    """Busca en la biblioteca histórica de Las Varillas y devuelve el texto completo
    de los documentos que coinciden. 'tema' puede ser un ID exacto (por ejemplo
    'teoria_1903', 'teoria_1900', 'teoria_1904', 'fecha_oficial') o palabras clave
    (por ejemplo 'ferrocarril', 'Dabbene', 'Parada KM 81')."""
    tema = (tema or "").strip()
    if not tema:
        return "Indica un tema o ID para buscar. Usa listar_indice para ver los documentos disponibles."
    try:
        data = repo.get_all()
    except (OSError, json.JSONDecodeError) as e:
        return f"Error al leer la base histórica: {type(e).__name__}"

    for d in data:
        if repo.norm(tema) == repo.norm(d["id"]):
            return repo.formatear([d])

    palabras = [p for p in re.findall(r"\w+", repo.norm(tema)) if p not in STOPWORDS and len(p) > 1]
    puntuados = []
    for d in data:
        texto = repo.norm(d["titulo"] + " " + d["contenido"] + " " + " ".join(d["tags"]))
        score = sum(1 for p in palabras if p in texto)
        if score:
            puntuados.append((score, d))

    if not puntuados:
        return f"No se encontró información para '{tema}'. Prueba con otra palabra clave o consulta el índice."

    puntuados.sort(key=lambda x: -x[0])
    return repo.formatear([d for _, d in puntuados[:MAX_RESULTADOS]])

if __name__ == "__main__":
    mcp.run()
