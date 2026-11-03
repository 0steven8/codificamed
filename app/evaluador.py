from __future__ import annotations

import json
from pathlib import Path
from .config import settings
from .pipeline.orquestador import OrquestadorCodificacion


class EvaluadorCalidad:
    def __init__(self, ruta_casos: Path | None = None) -> None:
        self.ruta_casos = ruta_casos or settings.casos_eval_path
        self.casos: list[dict] = []
        self._cargar_casos()
        self.orquestador = OrquestadorCodificacion()

    def _cargar_casos(self) -> None:
        # Carga casos clinicos desde archivo JSON
        if self.ruta_casos.exists():
            with open(self.ruta_casos, "r", encoding="utf-8") as f:
                self.casos = json.load(f)
        else:
            self.casos = []

    def evaluar_proveedor(
        self,
        proveedor_nombre: str,
        api_key: str | None = None,
        modelo_nombre: str | None = None,
        limite_casos: int | None = None,
    ) -> dict:
        # Evalua precision, recall, F1 y asercion
        casos_a_evaluar = self.casos[:limite_casos] if limite_casos else self.casos
        if not casos_a_evaluar:
            return {"error": "Dataset de evaluacion vacio."}

        tp_total = 0
        fp_total = 0
        fn_total = 0
        aciertos_asercion = 0
        total_aserciones = 0
        duraciones = []
        detalle_casos = []

        for caso in casos_a_evaluar:
            esperados = caso["codigos_esperados"]
            mapa_esperados = {e["codigo"].upper(): e["estado"].upper() for e in esperados}

            resultado = self.orquestador.procesar_nota(
                texto_nota=caso["texto"],
                proveedor_nombre=proveedor_nombre,
                api_key=api_key,
                modelo_nombre=modelo_nombre,
            )

            duracion = resultado["tiempos"].get("duracion_total_s", 0.0)
            duraciones.append(duracion)

            predichos = resultado["diagnosticos"]
            mapa_predichos = {p["codigo"].upper(): p["estado"].upper() for p in predichos}

            tp_caso = 0
            fp_caso = 0
            fn_caso = 0

            # Comparacion de codigos predichos contra esperados
            for cod_pred, est_pred in mapa_predichos.items():
                if cod_pred in mapa_esperados:
                    tp_caso += 1
                    total_aserciones += 1
                    if est_pred == mapa_esperados[cod_pred]:
                        aciertos_asercion += 1
                else:
                    fp_caso += 1

            for cod_esp in mapa_esperados:
                if cod_esp not in mapa_predichos:
                    fn_caso += 1

            tp_total += tp_caso
            fp_total += fp_caso
            fn_total += fn_caso

            p_caso = tp_caso / (tp_caso + fp_caso) if (tp_caso + fp_caso) > 0 else 0.0
            r_caso = tp_caso / (tp_caso + fn_caso) if (tp_caso + fn_caso) > 0 else 0.0
            f1_caso = (2 * p_caso * r_caso / (p_caso + r_caso)) if (p_caso + r_caso) > 0 else 0.0

            detalle_casos.append({
                "id": caso["id"],
                "titulo": caso["titulo"],
                "tp": tp_caso,
                "fp": fp_caso,
                "fn": fn_caso,
                "precision": round(p_caso, 4),
                "recall": round(r_caso, 4),
                "f1": round(f1_caso, 4),
                "duracion_s": duracion,
                "esperados": list(mapa_esperados.keys()),
                "predichos": list(mapa_predichos.keys()),
            })

        # Calculo de metricas globales
        precision_global = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0.0
        recall_global = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0.0
        f1_global = (
            (2 * precision_global * recall_global / (precision_global + recall_global))
            if (precision_global + recall_global) > 0
            else 0.0
        )
        asercion_acc = (aciertos_asercion / total_aserciones) if total_aserciones > 0 else 0.0
        tiempo_promedio = sum(duraciones) / len(duraciones) if duraciones else 0.0

        return {
            "proveedor": proveedor_nombre,
            "modelo": modelo_nombre or "por defecto",
            "casos_evaluados": len(casos_a_evaluar),
            "metricas_globales": {
                "precision": round(precision_global, 4),
                "recall": round(recall_global, 4),
                "f1_score": round(f1_global, 4),
                "exactitud_asercion": round(asercion_acc, 4),
                "tiempo_promedio_s": round(tiempo_promedio, 3),
                "tiempo_total_s": round(sum(duraciones), 3),
                "total_tp": tp_total,
                "total_fp": fp_total,
                "total_fn": fn_total,
            },
            "detalles": detalle_casos,
        }
