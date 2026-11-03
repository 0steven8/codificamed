from __future__ import annotations

import time

from ..config import settings
from ..llm import obtener_proveedor
from .buscador_cie10 import BuscadorCIE10
from .negacion import detectar_asercion
from .preprocesamiento import preprocesar_nota, quitar_tildes

# Esquema JSON para salidas estructuradas del modelo
ESQUEMA_CODIFICACION = {
    "type": "object",
    "properties": {
        "resumen_clinico": {"type": "string"},
        "diagnosticos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "codigo": {"type": "string"},
                    "descripcion": {"type": "string"},
                    "capitulo": {"type": "string"},
                    "estado": {"type": "string", "enum": ["CONFIRMADO", "NEGADO", "SOSPECHA"]},
                    "evidencia": {"type": "string"},
                    "justificacion": {"type": "string"},
                    "confianza": {"type": "number"},
                },
                "required": ["codigo", "descripcion", "estado", "evidencia", "justificacion"],
            },
        },
    },
    "required": ["resumen_clinico", "diagnosticos"],
}

PROMPT_SISTEMA = """Eres CodificaMed, especialista en codificacion CIE-10 para historias clinicas en espanol.
Analiza la nota medica, identifica afecciones y asigna codigos CIE-10 validos.

REGLAS OBLIGATORIAS:
1. DISTINCION DE NEGACION:
   - Si dice "niega fiebre", "se descarta neumonia" o "sin ITU", marca estado "NEGADO".
   - Si confirma diagnostico o sintoma presente, marca "CONFIRMADO".
   - Si expresa duda o probabilidad ("posible", "sospecha"), marca "SOSPECHA".
2. TRAZABILIDAD: "evidencia" debe ser la frase textual exacta donde aparece.
3. FORMATO: Emite exclusivamente un JSON valido con el esquema solicitado."""


class OrquestadorCodificacion:
    def __init__(self, buscador: BuscadorCIE10 | None = None) -> None:
        self.buscador = buscador or BuscadorCIE10()

    def procesar_nota(
        self,
        texto_nota: str,
        proveedor_nombre: str | None = None,
        api_key: str | None = None,
        modelo_nombre: str | None = None,
    ) -> dict:
        # Orquesta las fases del pipeline CRISP-ML(Q)
        inicio_total = time.time()
        tiempos = {}

        # Preprocesamiento y expansion de abreviaturas
        t0 = time.time()
        prep = preprocesar_nota(texto_nota)
        tiempos["preprocesamiento_s"] = round(time.time() - t0, 4)

        # Recuperacion RAG sobre catalogo CIE-10
        t0 = time.time()
        candidatos_rag = self.buscador.buscar_candidatos(prep["texto_expandido"], top_k=15)
        if candidatos_rag:
            resumen_catalogo = "\n".join([f"- [{c['codigo']}] {c['descripcion']}" for c in candidatos_rag])
        else:
            resumen_catalogo = self.buscador.obtener_resumen_catalogo()
        tiempos["recuperacion_rag_s"] = round(time.time() - t0, 4)

        # Construccion del prompt contextualizado
        prompt_usuario = f"""NOTA CLINICA:
\"\"\"
{prep['texto_original']}
\"\"\"

TEXTO NORMALIZADO CON ABREVIATURAS EXPANDIDAS:
\"\"\"
{prep['texto_expandido']}
\"\"\"

CATALOGO CIE-10 RELEVANTE (RAG):
{resumen_catalogo}

Codifica afecciones indicando estado (CONFIRMADO, NEGADO o SOSPECHA) y evidencia textual."""

        # Inferencia con el proveedor LLM seleccionado
        t0 = time.time()
        proveedor = obtener_proveedor(
            nombre=proveedor_nombre or settings.llm_provider,
            api_key=api_key,
            modelo=modelo_nombre,
        )
        resultado_llm = proveedor.codificar(PROMPT_SISTEMA, prompt_usuario, ESQUEMA_CODIFICACION)
        proveedor_efectivo = proveedor.nombre
        tiempos["inferencia_llm_s"] = round(time.time() - t0, 4)

        # Aseguramiento de calidad y trazabilidad
        t0 = time.time()
        diagnosticos_validados = []
        for diag in resultado_llm.get("diagnosticos", []):
            codigo = diag.get("codigo", "").strip().upper()
            evidencia = diag.get("evidencia", "").strip()

            # Verificacion de evidencia en texto original
            evidencia_presente = (
                quitar_tildes(evidencia.lower()) in quitar_tildes(texto_nota.lower())
                if evidencia else False
            )

            estado = diag.get("estado", "CONFIRMADO").upper()
            if estado not in ("CONFIRMADO", "NEGADO", "SOSPECHA"):
                estado = "CONFIRMADO"

            # Correccion de negacion basada en reglas
            asercion_regla = detectar_asercion(evidencia or texto_nota, diag.get("descripcion", ""))
            if asercion_regla["estado"] == "NEGADO" and estado == "CONFIRMADO":
                estado = "NEGADO"

            # Enriquecimiento con descripcion oficial del catalogo
            entrada_cat = next((e for e in self.buscador.catalogo if e["codigo"] == codigo), None)
            desc_oficial = entrada_cat["descripcion"] if entrada_cat else diag.get("descripcion", "")
            capitulo = entrada_cat["capitulo"] if entrada_cat else diag.get("capitulo", "Otros")

            diagnosticos_validados.append({
                "codigo": codigo,
                "descripcion": desc_oficial,
                "capitulo": capitulo,
                "estado": estado,
                "evidencia": evidencia,
                "evidencia_verificada": evidencia_presente,
                "justificacion": diag.get("justificacion", ""),
                "confianza": float(diag.get("confianza", 0.90)),
            })

        tiempos["aseguramiento_calidad_s"] = round(time.time() - t0, 4)
        tiempos["duracion_total_s"] = round(time.time() - inicio_total, 4)

        # Estimacion de tokens procesados
        tokens_est = int(len(texto_nota.split()) * 1.35) + 120

        # Conteo estadistico de hallazgos
        total_diag = len(diagnosticos_validados)
        confirmados = sum(1 for d in diagnosticos_validados if d["estado"] == "CONFIRMADO")
        negados = sum(1 for d in diagnosticos_validados if d["estado"] == "NEGADO")
        sospechas = sum(1 for d in diagnosticos_validados if d["estado"] == "SOSPECHA")

        return {
            "proveedor_usado": proveedor_efectivo,
            "modelo_usado": getattr(proveedor, "modelo", "motor_reglas"),
            "tiempos": tiempos,
            "tokens_estimados": tokens_est,
            "texto_original": texto_nota,
            "metricas_analisis": {
                "total_diagnosticos": total_diag,
                "confirmados": confirmados,
                "negados": negados,
                "sospechas": sospechas,
                "tokens_estimados": tokens_est,
                "oraciones_analizadas": prep["total_oraciones"],
                "evidencias_verificadas": sum(1 for d in diagnosticos_validados if d["evidencia_verificada"]),
            },
            "resumen_clinico": resultado_llm.get("resumen_clinico", ""),
            "diagnosticos": diagnosticos_validados,
        }
