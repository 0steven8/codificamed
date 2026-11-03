from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
import httpx

from ..config import settings
from .base import ErrorConexionLLM, ErrorLLM, ProveedorLLM, extraer_json


def _detectar_specs_hardware() -> dict[str, str | float]:
    # Detecta memoria RAM total del sistema
    ram_gb = 8.0
    try:
        if sys.platform == "win32":
            class _MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = _MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            ram_gb = round(stat.ullTotalPhys / (1024 ** 3), 1)
        elif hasattr(os, "sysconf"):
            paginas = os.sysconf("SC_PHYS_PAGES")
            tamano = os.sysconf("SC_PAGE_SIZE")
            ram_gb = round((paginas * tamano) / (1024 ** 3), 1)
    except Exception:
        ram_gb = 8.0

    # Detecta aceleracion grafica y VRAM
    vram_gb = 0.0
    gpu_nombre = "Sin GPU dedicada"
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            timeout=1.5,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        if out:
            partes = out.split("\n")[0].split(",")
            gpu_nombre = partes[0].strip()
            vram_gb = round(float(partes[1].strip()) / 1024, 1)
    except Exception:
        pass

    # Regla de recomendacion segun hardware
    if vram_gb >= 5.5 or ram_gb >= 14.0:
        modelo = "llama3.1:latest"
        motivo = "Hardware optimo para Llama 3.1 8B"
    elif vram_gb >= 3.5 or ram_gb >= 10.0:
        modelo = "mistral:latest"
        motivo = "Hardware intermedio optimo para Mistral 7B"
    else:
        modelo = "qwen2.5-coder:latest"
        motivo = "Hardware ligero optimo para Qwen 2.5"

    return {
        "ram_gb": ram_gb,
        "vram_gb": vram_gb,
        "gpu": gpu_nombre,
        "modelo_sugerido": modelo,
        "motivo": motivo,
    }


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

    # Modelos oficiales por orden jerarquico
    preferencias = (
        "llama3.1",
        "mistral",
        "qwen2.5-coder",
        "qwen2.5",
    )
    for pref in preferencias:
        for m in generativos:
            if pref in m.lower():
                return m

    # Si ninguno coincide, usar primer generativo
    return generativos[0]


class ProveedorOllama(ProveedorLLM):
    nombre = "ollama"

    def __init__(self, modelo: str | None = None, host: str | None = None) -> None:
        self.host = host or settings.ollama_host
        self.modelo = modelo or settings.ollama_model

    def descargar_modelo(self, modelo: str | None = None) -> bool:
        # Descarga modelo via API de Ollama
        objetivo = modelo or self.modelo
        try:
            r = httpx.post(
                f"{self.host}/api/pull",
                json={"name": objetivo, "stream": False},
                timeout=600.0,
            )
            return r.status_code == 200
        except Exception:
            return False

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
                    else:
                        specs = _detectar_specs_hardware()
                        sug = specs["modelo_sugerido"]
                        raise ErrorConexionLLM(
                            f"Ollama sin modelos descargados. Hardware ({specs['ram_gb']}GB RAM): "
                            f"ejecuta 'ollama pull {sug}' en tu terminal."
                        )
            except ErrorConexionLLM:
                raise
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
                # Reintento con formato json simple
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
                specs = _detectar_specs_hardware()
                sug = specs["modelo_sugerido"]
                return {
                    "disponible": False,
                    "modelo": self.modelo,
                    "host": self.host,
                    "modelos_instalados": [],
                    "mensaje": f"Ollama sin modelos. Ejecuta 'ollama pull {sug}'",
                    "diagnostico_hardware": specs,
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
