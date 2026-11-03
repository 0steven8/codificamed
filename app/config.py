from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Carga variables de entorno del proyecto
load_dotenv(BASE_DIR / ".env")


class Settings:
    def __init__(self) -> None:
        # Proveedor LLM activo por defecto
        self.llm_provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

        # Configuracion de Ollama local
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:latest")
        self.ollama_num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "2048"))
        self.ollama_timeout = float(os.getenv("OLLAMA_TIMEOUT", "600"))

        # Configuracion de embeddings
        self.embeddings_provider = os.getenv("EMBEDDINGS_PROVIDER", "ollama").strip().lower()
        self.embeddings_model = os.getenv("EMBEDDINGS_MODEL", "bge-m3")

        # Credenciales de APIs en la nube
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-6.1-sol").strip()

        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.claude_model = os.getenv("CLAUDE_MODEL", "opus-5.5").strip()

        # Rutas de datos
        self.datos_dir = BASE_DIR / "datos"
        self.catalogo_path = self.datos_dir / "catalogo_cie10.json"
        self.casos_eval_path = self.datos_dir / "casos_evaluacion.json"

        # Parametros del servidor web
        self.puerto = int(os.getenv("PUERTO", "8000"))
        self.host = os.getenv("HOST", "0.0.0.0")


settings = Settings()
