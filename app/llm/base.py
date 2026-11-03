from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod


class ErrorLLM(Exception):
    # Error generico en procesamiento con LLM
    pass


class ErrorConexionLLM(ErrorLLM):
    # Error de red o servicio no disponible
    pass


def extraer_json(texto: str) -> dict:
    # Extrae y valida estructura JSON de respuestas textuales
    texto = texto.strip()

    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass

    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", texto)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    inicio = texto.find("{")
    fin = texto.rfind("}")
    if inicio != -1 and fin != -1 and fin > inicio:
        try:
            return json.loads(texto[inicio : fin + 1])
        except json.JSONDecodeError:
            pass

    raise ErrorLLM(f"Respuesta no valida como JSON: {texto[:200]}")


class ProveedorLLM(ABC):
    nombre: str = "base"

    @abstractmethod
    def codificar(self, prompt_sistema: str, prompt_usuario: str, esquema: dict) -> dict:
        # Envia prompt y retorna diccionario con diagnosticos
        raise NotImplementedError

    @abstractmethod
    def estado(self) -> dict:
        # Verifica disponibilidad del proveedor
        raise NotImplementedError
