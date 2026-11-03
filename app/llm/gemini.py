from __future__ import annotations

import json
import os
import httpx

from ..config import settings
from .base import ErrorConexionLLM, ErrorLLM, ProveedorLLM, extraer_json


class ProveedorGemini(ProveedorLLM):
    nombre = "gemini"

    def __init__(self, api_key: str | None = None, modelo: str | None = None) -> None:
        self.api_key = api_key or settings.gemini_api_key
        self.modelo = modelo or settings.gemini_model or "gemini-3.8-flash"

    def _obtener_candidatos(self) -> list[str]:
        # Modelos Gemini: 3.8 Flash, 3.5 Flash-Lite, 3.1 Pro
        m = (self.modelo or "").lower()
        if "lite" in m or "3.5" in m:
            return ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.1-pro-preview"]
        elif "pro" in m or "3.1" in m:
            return ["gemini-3.1-pro-preview", "gemini-3.8-flash", "gemini-3.5-flash-lite"]
        else:
            return ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-pro-preview"]

    def codificar(self, prompt_sistema: str, prompt_usuario: str, esquema: dict) -> dict:
        if not self.api_key:
            raise ErrorConexionLLM("GEMINI_API_KEY no configurada")

        prompt_con_esquema = (
            f"{prompt_sistema}\n\n"
            f"Responde en formato JSON estrictamente bajo este esquema:\n"
            f"{json.dumps(esquema, ensure_ascii=False)}"
        )

        candidatos = self._obtener_candidatos()
        ultimo_error = None

        # 1. Intento principal con SDK oficial google-genai
        try:
            from google import genai
            from google.genai import types

            if self.api_key.startswith("AQ."):
                project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0004192654")
                client = genai.Client(
                    api_key=self.api_key,
                    vertexai=True,
                    project=project_id,
                    location="global",
                )
            else:
                client = genai.Client(api_key=self.api_key)

            config = types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
                system_instruction=prompt_con_esquema,
            )

            for mod in candidatos:
                try:
                    res = client.models.generate_content(
                        model=mod,
                        contents=prompt_usuario,
                        config=config,
                    )
                    if res and res.text:
                        return extraer_json(res.text)
                except Exception as e:
                    ultimo_error = str(e)
                    continue
        except ImportError:
            pass
        except Exception as e:
            ultimo_error = str(e)

        # 2. Fallback mediante HTTP REST directo
        cuerpo = {
            "system_instruction": {"parts": [{"text": prompt_con_esquema}]},
            "contents": [{"role": "user", "parts": [{"text": prompt_usuario}]}],
            "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"},
        }

        for mod in candidatos:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={self.api_key}"
            try:
                r = httpx.post(url, json=cuerpo, timeout=45.0)
                if r.status_code == 200:
                    data = r.json()
                    texto = data["candidates"][0]["content"]["parts"][0]["text"]
                    return extraer_json(texto)
                else:
                    ultimo_error = f"HTTP {r.status_code}: {r.text[:150]}"
            except Exception as e:
                ultimo_error = str(e)
                continue

        raise ErrorLLM(f"No se pudo completar la inferencia con Gemini: {ultimo_error}")

    def estado(self) -> dict:
        tiene_key = bool(self.api_key and len(self.api_key) > 10)
        return {
            "disponible": tiene_key,
            "modelo": self.modelo,
            "mensaje": "Activo" if tiene_key else "Requiere GEMINI_API_KEY",
        }
