from __future__ import annotations

import json
from pathlib import Path
from ..config import settings
from .preprocesamiento import quitar_tildes


class BuscadorCIE10:
    def __init__(self, ruta_catalogo: Path | None = None) -> None:
        self.ruta_catalogo = ruta_catalogo or settings.catalogo_path
        self.catalogo: list[dict] = []
        self._cargar_catalogo()

    def _cargar_catalogo(self) -> None:
        # Carga catalogo CIE-10 desde archivo JSON
        if self.ruta_catalogo.exists():
            with open(self.ruta_catalogo, "r", encoding="utf-8") as f:
                self.catalogo = json.load(f)
        else:
            self.catalogo = []

    def buscar_candidatos(self, consulta: str, top_k: int = 4) -> list[dict]:
        # Recupera codigos CIE-10 mas afines a la consulta
        if not self.catalogo:
            return []

        c_norm = quitar_tildes(consulta.lower()).strip()
        tokens_consulta = set(c_norm.split())
        resultados = []

        for entrada in self.catalogo:
            puntaje = 0.0

            # Coincidencia exacta de codigo
            if entrada["codigo"].lower() == c_norm:
                puntaje += 10.0

            # Coincidencia con sinonimos clinicos
            for sin in entrada.get("sinonimos", []):
                sin_norm = quitar_tildes(sin.lower())
                if sin_norm == c_norm:
                    puntaje += 8.0
                elif sin_norm in c_norm or c_norm in sin_norm:
                    puntaje += 5.0
                else:
                    tokens_sin = set(sin_norm.split())
                    inter = tokens_consulta.intersection(tokens_sin)
                    if inter:
                        puntaje += len(inter) * 1.5

            # Coincidencia con descripcion oficial
            desc_norm = quitar_tildes(entrada["descripcion"].lower())
            if desc_norm in c_norm or c_norm in desc_norm:
                puntaje += 4.0
            else:
                tokens_desc = set(desc_norm.split())
                inter_desc = tokens_consulta.intersection(tokens_desc)
                if inter_desc:
                    puntaje += len(inter_desc) * 1.2

            if puntaje > 0.5:
                resultados.append({
                    "codigo": entrada["codigo"],
                    "descripcion": entrada["descripcion"],
                    "capitulo": entrada["capitulo"],
                    "puntaje": round(puntaje, 2),
                })

        # Ordenar por mayor puntaje
        resultados.sort(key=lambda x: x["puntaje"], reverse=True)
        return resultados[:top_k]

    def obtener_resumen_catalogo(self) -> str:
        # Genera texto del catalogo para contexto RAG
        lineas = []
        for e in self.catalogo:
            sinonimos_str = ", ".join(e.get("sinonimos", [])[:4])
            lineas.append(f"- [{e['codigo']}] {e['descripcion']} (Sinonimos: {sinonimos_str})")
        return "\n".join(lineas)
