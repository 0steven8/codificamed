from __future__ import annotations

import httpx

from ..config import settings
from .base import ErrorConexionLLM, ErrorLLM, ProveedorLLM, extraer_json


class ProveedorClaude(ProveedorLLM):
    nombre = "claude"

    def __init__(self, api_key: str | None = None, modelo: str | None = None) -> None:
        self.api_key = api_key or settings.anthropic_api_key
        self.modelo = modelo or settings.claude_model or "sonnet-5.5"

    def _obtener_candidatos(self) -> list[str]:
        # Modelos Claude: Opus 5.5, Sonnet 5.5, Haiku 5.5
        m = self.modelo.lower()
        if "sonnet" in m:
            return ["sonnet-5.5", "claude-sonnet-5.5", "opus-5.5", "haiku-5.5"]
        elif "haiku" in m:
            return ["haiku-5.5", "claude-haiku-5.5", "sonnet-5.5", "opus-5.5"]
        else:
            return ["opus-5.5", "claude-opus-5.5", "sonnet-5.5", "haiku-5.5"]

    def codificar(self, prompt_sistema: str, prompt_usuario: str, esquema: dict) -> dict:
        # Envia peticion con especificacion Anthropic 2026-10-21
        if not self.api_key:
            raise ErrorConexionLLM("ANTHROPIC_API_KEY no configurada")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2026-10-21",
            "content-type": "application/json",
        }
        herramienta = {
            "name": "emitir_diagnosticos_cie10",
            "description": "Retorna listado estructurado de codigos CIE-10",
            "input_schema": esquema,
        }

        candidatos = self._obtener_candidatos()
        ultimo_error = None

        for mod in candidatos:
            # En version 2026-10-21 no se envian temperature ni top_p
            cuerpo = {
                "model": mod,
                "max_tokens": 2048,
                "system": prompt_sistema,
                "messages": [{"role": "user", "content": prompt_usuario}],
                "tools": [herramienta],
                "tool_choice": {"type": "tool", "name": "emitir_diagnosticos_cie10"},
            }

            try:
                r = httpx.post("https://api.anthropic.com/v1/messages", headers=headers, json=cuerpo, timeout=60.0)
            except httpx.ConnectError as e:
                raise ErrorConexionLLM("Error de conexion con Anthropic") from e
            except httpx.TimeoutException as e:
                raise ErrorLLM("Tiempo de espera agotado en Anthropic") from e

            # Si el modelo no existe, probar siguiente
            if r.status_code == 404 or (r.status_code == 400 and "model" in r.text.lower()):
                ultimo_error = r.text[:200]
                continue

            if r.status_code >= 400:
                raise ErrorLLM(f"Error HTTP {r.status_code} desde Anthropic: {r.text[:200]}")

            data = r.json()
            for bloque in data.get("content", []):
                if bloque.get("type") == "tool_use" and bloque.get("name") == "emitir_diagnosticos_cie10":
                    return bloque.get("input", {})

            textos = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
            return extraer_json("".join(textos))

        raise ErrorLLM(f"No se encontro modelo Claude compatible: {ultimo_error}")

    def estado(self) -> dict:
        # Comprueba presencia de clave de Claude
        tiene_key = bool(self.api_key and len(self.api_key) > 10)
        return {
            "disponible": tiene_key,
            "modelo": self.modelo,
            "mensaje": "Activo" if tiene_key else "Requiere ANTHROPIC_API_KEY",
        }
