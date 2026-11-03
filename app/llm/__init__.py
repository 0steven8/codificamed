from __future__ import annotations

from .base import ErrorConexionLLM, ErrorLLM, ProveedorLLM
from .claude import ProveedorClaude
from .gemini import ProveedorGemini
from .ollama import ProveedorOllama
from .openai_llm import ProveedorOpenAI


def obtener_proveedor(
    nombre: str,
    api_key: str | None = None,
    modelo: str | None = None,
    host: str | None = None,
) -> ProveedorLLM:
    # Instancia el conector LLM segun el proveedor
    nombre_limpio = (nombre or "ollama").strip().lower()

    if nombre_limpio == "ollama":
        return ProveedorOllama(modelo=modelo, host=host)
    elif nombre_limpio in ("gemini", "google"):
        return ProveedorGemini(api_key=api_key, modelo=modelo)
    elif nombre_limpio == "openai":
        return ProveedorOpenAI(api_key=api_key, modelo=modelo)
    elif nombre_limpio in ("claude", "anthropic"):
        return ProveedorClaude(api_key=api_key, modelo=modelo)
    else:
        return ProveedorOllama(modelo=modelo, host=host)
