from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import settings
from .evaluador import EvaluadorCalidad
from .llm import ErrorConexionLLM, ErrorLLM, obtener_proveedor
from .pipeline.buscador_cie10 import BuscadorCIE10
from .pipeline.orquestador import OrquestadorCodificacion

app = FastAPI(title="CodificaMed", version="1.0.0")

# Bloqueo de concurrencia para proteger GPU local
_inferencia_lock = threading.Lock()

# Habilitar CORS para peticiones locales
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Inicializacion de servicios del pipeline
orquestador = OrquestadorCodificacion()
evaluador = EvaluadorCalidad()
buscador = BuscadorCIE10()


# Modelos Pydantic para validacion de entradas
class SolicitudCodificacion(BaseModel):
    texto: str = Field(..., min_length=5)
    proveedor: str = Field(default="ollama")
    api_key: str | None = Field(default=None)
    modelo: str | None = Field(default=None)


class SolicitudComparacion(BaseModel):
    texto: str = Field(..., min_length=5)
    proveedor_local: str = Field(default="ollama")
    modelo_local: str | None = Field(default=None)
    proveedor_api: str = Field(default="gemini")
    modelo_api: str | None = Field(default=None)
    api_key_api: str | None = Field(default=None)


class SolicitudEvaluacion(BaseModel):
    proveedor: str = Field(default="ollama")
    api_key: str | None = Field(default=None)
    modelo: str | None = Field(default=None)
    limite_casos: int | None = Field(default=None)


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    # Retorna el icono oficial en formato ICO
    return FileResponse(STATIC_DIR / "img" / "favicon.ico", media_type="image/x-icon")


@app.get("/favicon.png", include_in_schema=False)
def favicon_png() -> FileResponse:
    # Retorna el icono en formato PNG
    return FileResponse(STATIC_DIR / "img" / "favicon.png", media_type="image/png")


@app.get("/", response_class=HTMLResponse)
def index() -> FileResponse:
    # Retorna la interfaz web principal
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/config")
def obtener_configuracion() -> dict[str, Any]:
    # Consulta estado de proveedores configurados
    prov_ollama = obtener_proveedor("ollama")
    return {
        "proveedor_defecto": settings.llm_provider,
        "ollama": prov_ollama.estado(),
        "gemini": {
            "configurado": bool(settings.gemini_api_key),
            "modelo": settings.gemini_model,
        },
        "openai": {
            "configurado": bool(settings.openai_api_key),
            "modelo": settings.openai_model,
        },
        "claude": {
            "configurado": bool(settings.anthropic_api_key),
            "modelo": settings.claude_model,
        },
        "total_codigos_cie10": len(buscador.catalogo),
        "total_casos_evaluacion": len(evaluador.casos),
    }


@app.post("/api/codificar")
def codificar_nota(req: SolicitudCodificacion) -> dict[str, Any]:
    # Procesa nota medica con pipeline de PLN
    if not _inferencia_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="El motor de inferencia local se encuentra ocupado. Espera a que termine la tarea en curso para no sobrecargar la GPU."
        )
    try:
        return orquestador.procesar_nota(
            texto_nota=req.texto,
            proveedor_nombre=req.proveedor,
            api_key=req.api_key,
            modelo_nombre=req.modelo,
        )
    except ErrorConexionLLM as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ErrorLLM as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        _inferencia_lock.release()


@app.post("/api/comparar")
def comparar_modelos(req: SolicitudComparacion) -> dict[str, Any]:
    # Ejecuta la nota en local y API simultaneamente
    if not _inferencia_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="El motor de inferencia local se encuentra ocupado. Espera a que termine la tarea en curso para no sobrecargar la GPU."
        )
    try:
        try:
            res_local = orquestador.procesar_nota(
                texto_nota=req.texto,
                proveedor_nombre=req.proveedor_local,
                modelo_nombre=req.modelo_local,
            )
        except Exception as e:
            res_local = {"error": f"Fallo en modelo local: {str(e)}", "diagnosticos": []}

        try:
            res_api = orquestador.procesar_nota(
                texto_nota=req.texto,
                proveedor_nombre=req.proveedor_api,
                api_key=req.api_key_api,
                modelo_nombre=req.modelo_api,
            )
        except Exception as e:
            res_api = {"error": f"Fallo en API externa: {str(e)}", "diagnosticos": []}

        return {"local": res_local, "api": res_api}
    finally:
        _inferencia_lock.release()


@app.post("/api/evaluar")
def evaluar_modelo(req: SolicitudEvaluacion) -> dict[str, Any]:
    # Ejecuta suite de evaluacion con metricas formales
    if not _inferencia_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="El motor de inferencia local se encuentra ocupado. Espera a que termine la tarea en curso para no sobrecargar la GPU."
        )
    try:
        return evaluador.evaluar_proveedor(
            proveedor_nombre=req.proveedor,
            api_key=req.api_key,
            modelo_nombre=req.modelo,
            limite_casos=req.limite_casos,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en evaluacion: {str(e)}")
    finally:
        _inferencia_lock.release()


@app.get("/api/catalogo")
def consultar_catalogo(q: str | None = None) -> list[dict]:
    # Retorna catalogo CIE-10 filtrado o completo
    if not q:
        return buscador.catalogo
    return buscador.buscar_candidatos(q, top_k=25)


@app.get("/api/casos-ejemplo")
def obtener_casos_ejemplo() -> list[dict]:
    # Retorna casos clinicos de prueba predefinidos
    return [
        {
            "id": c["id"],
            "titulo": c["titulo"],
            "texto": c["texto"],
            "total_esperados": len(c["codigos_esperados"]),
        }
        for c in evaluador.casos
    ]
