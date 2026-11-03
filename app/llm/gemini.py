from __future__ import annotations

import json
import httpx

from ..config import settings
from .base import ErrorConexionLLM, ErrorLLM, ProveedorLLM, extraer_json


class ProveedorGemini(ProveedorLLM):
    nombre = "gemini"

    def __init__(self, api_key: str | None = None, modelo: str | None = None) -> None:
        self.api_key = api_key or settings.gemini_api_key
        self.modelo = modelo or settings.gemini_model or "gemini-3.8-flash"

    def _obtener_candidatos(self) -> list[str]:
        # Orden de prioridad de modelos segun solicitud
        m = self.modelo.lower()
        if "argon" in m or "4" in m:
            return [self.modelo, "gemini-4-argon", "gemini-3.8-flash"]
        elif "lite" in m or "3.5" in m:
            return [self.modelo, "gemini-3.5-flash-lite", "gemini-3.8-flash"]
        else:
            return [self.modelo, "gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-4-argon"]

    def codificar(self, prompt_sistema: str, prompt_usuario: str, esquema: dict) -> dict:
        # Envia peticion a Google Generative Language API
        if not self.api_key:
            raise ErrorConexionLLM("GEMINI_API_KEY no configurada")

        cuerpo = {
            "system_instruction": {
                "parts": [{"text": f"{prompt_sistema}\n\nResponde en JSON con este esquema:\n{json.dumps(esquema, ensure_ascii=False)}"}]
            },
            "contents": [{"role": "user", "parts": [{"text": prompt_usuario}]}],
            "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"},
        }

        ultimo_error = None
        candidatos = self._obtener_candidatos()

        for mod in candidatos:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={self.api_key}"
            try:
                r = httpx.post(url, json=cuerpo, timeout=60.0)
            except httpx.ConnectError as e:
                raise ErrorConexionLLM("Error de conexion con Gemini") from e
            except httpx.TimeoutException as e:
                raise ErrorLLM("Tiempo de espera agotado en Gemini") from e

            # Reintenta con modelo alternativo ante fallos
            if r.status_code in (404, 400) and ("not found" in r.text.lower() or "unsupported" in r.text.lower()):
                ultimo_error = r.text[:200]
                continue

            if r.status_code >= 400:
                raise ErrorLLM(f"Error HTTP {r.status_code} desde Gemini: {r.text[:200]}")

            data = r.json()
            try:
                texto = data["candidates"][0]["content"]["parts"][0]["text"]
                return extraer_json(texto)
            except (KeyError, IndexError) as e:
                raise ErrorLLM("Respuesta invalida recibida de Gemini") from e

        raise ErrorLLM(f"No se pudo conectar a los modelos Gemini: {ultimo_error}")

    def estado(self) -> dict:
        # Verifica existencia de clave de API
        tiene_key = bool(self.api_key and len(self.api_key) > 10)
        return {
            "disponible": tiene_key,
            "modelo": self.modelo,
            "mensaje": "Activo" if tiene_key else "Requiere GEMINI_API_KEY",
        }
