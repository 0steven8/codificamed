from __future__ import annotations

import re
import unicodedata

# Abreviaturas medicas frecuentes en notas clinicas
ABREVIATURAS_CLINICAS: dict[str, str] = {
    "hta": "hipertensión arterial",
    "dm2": "diabetes mellitus tipo 2",
    "dbt2": "diabetes mellitus tipo 2",
    "dm1": "diabetes mellitus tipo 1",
    "dbt1": "diabetes mellitus tipo 1",
    "dm": "diabetes mellitus",
    "dolor abd": "dolor abdominal",
    "itu": "infección de vías urinarias",
    "ivu": "infección de vías urinarias",
    "epoc": "enfermedad pulmonar obstructiva crónica",
    "acv": "accidente cerebrovascular",
    "ecv": "evento cerebrovascular",
    "iam": "infarto agudo de miocardio",
    "icc": "insuficiencia cardíaca congestiva",
    "fa": "fibrilación auricular",
    "gea": "gastroenteritis aguda",
    "erc": "enfermedad renal crónica",
    "irc": "insuficiencia renal crónica",
    "tce": "traumatismo craneoencefálico",
    "hbp": "hiperplasia prostática benigna",
    "erge": "enfermedad por reflujo gastroesofágico",
    "nac": "neumonía adquirida en la comunidad",
    "fid": "fosa ilíaca derecha",
    "fii": "fosa ilíaca izquierda",
    "pa": "presión arterial",
    "fc": "frecuencia cardíaca",
    "fr": "frecuencia respiratoria",
    "sat": "saturación de oxígeno",
}


def quitar_tildes(texto: str) -> str:
    # Remueve acentos diacriticos para busquedas normalizadas
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def expandir_abreviaturas(texto: str) -> str:
    # Expande siglas clinicas a su forma completa
    resultado = texto
    for abrev, expansion in ABREVIATURAS_CLINICAS.items():
        patron = re.compile(rf"\b{re.escape(abrev)}\b", re.IGNORECASE)
        resultado = patron.sub(f"{abrev.upper()} ({expansion})", resultado)
    return resultado


def segmentar_oraciones(texto: str) -> list[str]:
    # Divide texto en oraciones para delimitar alcance
    partes = re.split(r"(?<=[.!?;\n])\s+", texto.strip())
    oraciones = [p.strip() for p in partes if len(p.strip()) > 3]
    return oraciones if oraciones else [texto.strip()]


def limpiar_texto(texto: str) -> str:
    # Normaliza espacios multiples y saltos
    return re.sub(r"\s+", " ", texto).strip()


def preprocesar_nota(texto: str) -> dict:
    # Ejecuta preprocesamiento y estructuracion inicial
    limpio = limpiar_texto(texto)
    expandido = expandir_abreviaturas(limpio)
    oraciones = segmentar_oraciones(limpio)
    return {
        "texto_original": texto,
        "texto_limpio": limpio,
        "texto_expandido": expandido,
        "oraciones": oraciones,
        "total_oraciones": len(oraciones),
        "total_palabras": len(limpio.split()),
    }
