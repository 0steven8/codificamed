from __future__ import annotations

import json
import httpx

from ..config import settings
from .base import ErrorConexionLLM, ErrorLLM, ProveedorLLM, extraer_json


def _es_modelo_generativo(nombre: str) -> bool:
    # Excluye modelos de embeddings u OCR
    descartar = ("bge-", "embed", "minilm", "nomic", "bert", "ocr")
    return not any(d in nombre.lower() for d in descartar)


def _seleccionar_mejor_modelo(solicitado: str, instalados: list[str]) -> str:
    # Si el solicitado esta instalado, usarlo
    for m in instalados:
        if solicitado == m or f"{solicitado}:latest" == m or solicitado.split(":")[0] == m.split(":")[0]:
            return m

    # Filtrar solo modelos generativos de chat
    generativos = [m for m in instalados if _es_modelo_generativo(m)]
    if not generativos:
        return solicitado

    # Familias de modelos preferidas para tareas clinicas
    preferencias = (
        "llama3.1",
        "mistral",
        "qwen2.5",
        "llama3",
        "deepseek-r1",
        "gemma",
        "phi4",
        "phi3",
        "hermes",
        "dolphin",
    )
    for pref in preferencias:
        for m in generativos:
            if pref in m.lower():
                return m

    # Si ninguno coincide con preferencias, usar primer generativo
    return generativos[0]


class ProveedorOllama(ProveedorLLM):
    nombre = "ollama"

    def __init__(self, modelo: str | None = None, host: str | None = None) -> None:
        self.host = host or settings.ollama_host
        self.modelo = modelo or settings.ollama_model

    def codificar(self, prompt_sistema: str, prompt_usuario: str, esquema: dict) -> dict:
        # Resuelve modelo disponible si falta definir
        if not getattr(self, "_modelo_verificado", False):
            try:
                r_tags = httpx.get(f"{self.host}/api/tags", timeout=2.0)
                if r_tags.status_code == 200:
                    instalados = [m["name"] for m in r_tags.json().get("models", [])]
                    if instalados:
                        self.modelo = _seleccionar_mejor_modelo(self.modelo, instalados)
                        self._modelo_verificado = True
            except Exception:
                pass

        # Envia peticion estructurada a Ollama
        cuerpo = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            "stream": False,
            "format": esquema,
            "options": {"temperature": 0.1, "num_ctx": settings.ollama_num_ctx},
            "keep_alive": "30m",
        }

        try:
            r = httpx.post(f"{self.host}/api/chat", json=cuerpo, timeout=settings.ollama_timeout)
            if r.status_code == 400:
                # Reintento con formato json simple si version antigua
                cuerpo["format"] = "json"
                cuerpo["messages"][0]["content"] += f"\n\nResponde en JSON:\n{json.dumps(esquema, ensure_ascii=False)}"
                r = httpx.post(f"{self.host}/api/chat", json=cuerpo, timeout=settings.ollama_timeout)
        except httpx.ConnectError as e:
            raise ErrorConexionLLM(f"Ollama no disponible en {self.host}") from e
        except httpx.TimeoutException as e:
            raise ErrorLLM("Tiempo de espera agotado en Ollama") from e

        if r.status_code == 404:
            raise ErrorConexionLLM(f"Modelo '{self.modelo}' no instalado en Ollama")
        if r.status_code >= 400:
            raise ErrorLLM(f"Error HTTP {r.status_code} desde Ollama")

        contenido = r.json().get("message", {}).get("content", "")
        return extraer_json(contenido)

    def estado(self) -> dict:
        # Consulta modelos descargados y conectividad local
        try:
            r = httpx.get(f"{self.host}/api/tags", timeout=3.0)
            if r.status_code == 200:
                instalados = [m["name"] for m in r.json().get("models", [])]
                if instalados:
                    modelo_activo = _seleccionar_mejor_modelo(self.modelo, instalados)
                    return {
                        "disponible": True,
                        "modelo": modelo_activo,
                        "host": self.host,
                        "modelos_instalados": instalados,
                        "mensaje": "Activo",
                    }
                return {
                    "disponible": False,
                    "modelo": self.modelo,
                    "host": self.host,
                    "modelos_instalados": [],
                    "mensaje": "Ollama activo pero sin modelos instalados",
                }
        except Exception:
            pass

        return {
            "disponible": False,
            "modelo": self.modelo,
            "host": self.host,
            "modelos_instalados": [],
            "mensaje": "Ollama no detectado",
        }
