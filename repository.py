import os
import json
import re
import unicodedata
from functools import lru_cache

class FundacionRepository:
    """Repositorio unificado para el acceso a la base de datos histórica (fundacion.json)."""

    def __init__(self, data_file: str = None):
        if data_file is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_file = os.path.join(base_dir, "fundacion.json")
        else:
            self.data_file = data_file

    @lru_cache(maxsize=1)
    def cargar_datos(self) -> list:
        if not os.path.exists(self.data_file):
            return []
        with open(self.data_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_all(self) -> list:
        return self.cargar_datos()

    def get_full_text(self) -> str:
        data = self.get_all()
        return "\n\n".join(f"## {d['titulo']}\n{d['contenido']}" for d in data)

    @staticmethod
    def norm(s: str) -> str:
        """Minúsculas y sin tildes, para búsquedas tolerantes."""
        s = unicodedata.normalize("NFD", s.lower())
        return "".join(c for c in s if unicodedata.category(c) != "Mn")

    @staticmethod
    def formatear(docs: list) -> str:
        out = ""
        for d in docs:
            out += (f"DOCUMENTO [{d['id']}]: {d['titulo']}\n"
                    f"Criterio: {d['metadata'].get('criterio', '-')}\n"
                    f"{d['contenido']}\n\n---\n\n")
        return out
