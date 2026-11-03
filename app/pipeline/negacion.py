from __future__ import annotations

import re
from .preprocesamiento import quitar_tildes

# Disparadores de negacion que preceden al concepto
DISPARADORES_PRE_NEGACION = [
    r"\bniega\b",
    r"\bno refiere\b",
    r"\bno presenta\b",
    r"\bno se evidencia\b",
    r"\bno hay\b",
    r"\bno se observa\b",
    r"\bsin signos de\b",
    r"\bsin evidencia de\b",
    r"\bsin\b",
    r"\bse descarta\b",
    r"\bdescartado\b",
    r"\bdescartada\b",
    r"\bausencia de\b",
    r"\bnegativo para\b",
    r"\bnegativa para\b",
    r"\basintomatico para\b",
    r"\basintomatica para\b",
    r"\blibre de\b",
    r"\brechaza\b",
]

# Disparadores de negacion que siguen al concepto
DISPARADORES_POST_NEGACION = [
    r"\bnegativo\b",
    r"\bnegativa\b",
    r"\bdescartado\b",
    r"\bdescartada\b",
    r"\bno observado\b",
    r"\bno observada\b",
]

# Disparadores de sospecha clinica
DISPARADORES_SOSPECHA = [
    r"\bprobable\b",
    r"\bprobabilidad de\b",
    r"\bsospecha de\b",
    r"\bposible\b",
    r"\ba descartar\b",
    r"\bpor descartar\b",
    r"\binterrogado\b",
    r"\bduda diagnostica\b",
]

# Expresiones que cancelan una negacion falsa
PSEUDO_NEGACIONES = [
    r"\bno solo\b",
    r"\bsin cambios\b",
    r"\bno obstante\b",
    r"\bsin duda\b",
]


def detectar_asercion(oracion: str, termino: str) -> dict:
    # Determina si una entidad clinica esta confirmada o negada
    oracion_norm = quitar_tildes(oracion.lower())
    termino_norm = quitar_tildes(termino.lower())

    match_termino = re.search(rf"\b{re.escape(termino_norm)}\b", oracion_norm)
    if not match_termino:
        pos_inicio = oracion_norm.find(termino_norm)
        if pos_inicio == -1:
            return {"estado": "CONFIRMADO", "disparador": None, "evidencia": oracion}
        pos_fin = pos_inicio + len(termino_norm)
    else:
        pos_inicio, pos_fin = match_termino.span()

    texto_previo = oracion_norm[:pos_inicio]
    texto_posterior = oracion_norm[pos_fin:]

    # Ventana de contexto previa y posterior
    ventana_previa = " ".join(texto_previo.split()[-6:])
    ventana_posterior = " ".join(texto_posterior.split()[:4])

    # Validacion de pseudo-negaciones
    for pseudo in PSEUDO_NEGACIONES:
        if re.search(pseudo, ventana_previa):
            return {"estado": "CONFIRMADO", "disparador": "pseudo_negacion", "evidencia": oracion.strip()}

    # Validacion de sospecha diagnostica
    for d_sosp in DISPARADORES_SOSPECHA:
        m = re.search(d_sosp, ventana_previa)
        if m:
            return {"estado": "SOSPECHA", "disparador": m.group(0), "evidencia": oracion.strip()}

    # Validacion de disparadores de negacion previos
    for d_neg in DISPARADORES_PRE_NEGACION:
        m = re.search(d_neg, ventana_previa)
        if m:
            return {"estado": "NEGADO", "disparador": m.group(0), "evidencia": oracion.strip()}

    # Validacion de disparadores de negacion posteriores
    for d_post in DISPARADORES_POST_NEGACION:
        m = re.search(d_post, ventana_posterior)
        if m:
            return {"estado": "NEGADO", "disparador": m.group(0), "evidencia": oracion.strip()}

    return {"estado": "CONFIRMADO", "disparador": "mencion_directa", "evidencia": oracion.strip()}
