from __future__ import annotations

import json
import httpx

from ..config import settings
from .base import ErrorConexionLLM, ErrorLLM, ProveedorLLM, extraer_json


class ProveedorOpenAI(ProveedorLLM):
    nombre = "openai"

    def __init__(self, api_key: str | None = None, modelo: str | None = None) -> None:
        self.api_key = api_key or settings.openai_api_key
        self.modelo = modelo or settings.openai_model or "gpt-6.1-terra"

    def _obtener_candidatos(self) -> list[str]:
        # Genera lista de alias segun familia solicitada
        m = self.modelo.lower()
        if "luna" in m:
            return [self.modelo, "gpt-6-luna", "gpt-6.1-terra"]
        elif "sol" in m:
            return [self.modelo, "gpt-6.1-sol", "gpt-6-sol", "gpt-6.1-terra"]
        elif "astra" in m:
            return [self.modelo, "gpt-6-astra", "gpt-6.1-sol"]
        else:
            return [self.modelo, "gpt-6.1-terra", "gpt-6-luna", "gpt-6.1-sol", "gpt-6-astra"]

    def codificar(self, prompt_sistema: str, prompt_usuario: str, esquema: dict) -> dict:
        # Envia solicitud structured outputs a OpenAI
        if not self.api_key:
            raise ErrorConexionLLM("OPENAI_API_KEY no configurada")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        candidatos = self._obtener_candidatos()
        ultimo_error = None

        for mod in candidatos:
            cuerpo = {
                "model": mod,
                "messages": [
                    {"role": "system", "content": f"{prompt_sistema}\n\nResponde en JSON con este esquema:\n{json.dumps(esquema, ensure_ascii=False)}"},
                    {"role": "user", "content": prompt_usuario},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
            }

            try:
                r = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers, json=cuerpo, timeout=60.0)
            except httpx.ConnectError as e:
                raise ErrorConexionLLM("Error de conexion con OpenAI") from e
            except httpx.TimeoutException as e:
                raise ErrorLLM("Tiempo de espera agotado en OpenAI") from e

            # Reintenta con modelo alternativo ante fallos
            if r.status_code == 404 or (r.status_code == 400 and "model" in r.text.lower()):
                ultimo_error = r.text[:200]
                continue

            if r.status_code >= 400:
                raise ErrorLLM(f"Error HTTP {r.status_code} desde OpenAI: {r.text[:200]}")

            data = r.json()
            contenido = data["choices"][0]["message"]["content"]
            return extraer_json(contenido)

        raise ErrorLLM(f"No se encontro modelo OpenAI compatible: {ultimo_error}")

    def estado(self) -> dict:
        # Comprueba presencia de clave OpenAI
        tiene_key = bool(self.api_key and len(self.api_key) > 10)
        return {
            "disponible": tiene_key,
            "modelo": self.modelo,
            "mensaje": "Activo" if tiene_key else "Requiere OPENAI_API_KEY",
        }
