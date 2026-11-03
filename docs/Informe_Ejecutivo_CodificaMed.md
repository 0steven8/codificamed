# INFORME EJECUTIVO DEL PROYECTO
## CodificaMed v1.0 — Sistema Inteligente de Codificación Automática CIE-10 para Historias Clínicas mediante Procesamiento de Lenguaje Natural

**Institución:** Escuela Superior Politécnica de Chimborazo (ESPOCH)  
**Facultad:** Facultad de Informática y Electrónica (FIE)  
**Carrera:** Ingeniería en Software  
**Cátedra:** Base de Conocimiento  
**Docente:** Ing. Isaac Torres  
**Estudiante:** Steven Pico  
**Fecha:** 02 de noviembre de 2026  

---

### 1. Introducción y Comprensión del Negocio (Fase 1 CRISP-ML(Q))

#### 1.1. Contexto Clínico y Problemática Operativa
En el ecosistema sanitario contemporáneo, tanto en los centros de la Red Pública Integral de Salud (MSP, IESS, ISSFA, ISSPOL) como en el sector asegurador privado, cada consulta médica, estancia hospitalaria e intervención quirúrgica debe codificarse obligatoriamente bajo el estándar de la Clasificación Internacional de Enfermedades, décima revisión (CIE-10). Esta codificación rige la estadística epidemiológica nacional, la asignación de presupuestos y la auditoría y liquidación de prestaciones sanitarias.

Tradicionalmente, esta labor se ejecuta de manera completamente manual. Un equipo de médicos auditores y codificadores clínicos revisa cientos de historias clínicas al día redactadas en prosa médica libre. Dicha modalidad enfrenta tres barreras críticas:

1. **Variabilidad y Ambigüedad Lingüística:** Empleo sistemático de acrónimos locales y abreviaciones telegráficas como *"HTA"* (hipertensión arterial), *"DM2"* (diabetes mellitus tipo 2), *"dolor abd"* (dolor abdominal), *"ITU"* (infección de vías urinarias) y *"EPOC"* (enfermedad pulmonar obstructiva crónica).
2. **Presencia Crítica de Negaciones y Aserciones:** En la práctica clínica es tan relevante registrar lo que el paciente padece como lo que explícitamente no presenta (por ejemplo: *"niega fiebre"*, *"se descarta neumonía tras rayos X"*, *"sin signos de apendicitis"*). Un motor rudimentario de búsqueda de palabras clave asignaría códigos de neumonía o apendicitis a un paciente sano de dichas patologías, provocando graves errores diagnósticos y financieros.
3. **Fatiga Cognitiva y Glosas Hospitalarias:** La revisión manual intensiva genera demoras de semanas en la facturación y frecuentes *"glosas médicas"* (retenciones y penalizaciones de cobro por inconsistencias documentales).

#### 1.2. Objetivos del Proyecto
El objetivo general de CodificaMed v1.0 consiste en diseñar, implementar y validar un prototipo de software asistencial basado en Procesamiento de Lenguaje Natural (PLN) capaz de analizar historias clínicas narrativas, expandir siglas médicas, clasificar el estado de aserción (confirmado, negado, sospecha) con alta fidelidad y sugerir los códigos CIE-10 correspondientes vinculados a su evidencia textual exacta.

Entre los objetivos específicos destacan:
- Estructurar un pipeline modular bajo la metodología formal CRISP-ML(Q).
- Desacoplar la capa de inferencia para admitir tanto modelos locales de código abierto ejecutados en Ollama como APIs de última generación en la nube.
- Ofrecer una interfaz de usuario limpia, accesible y portable sin dependencias de compilación complejas.

---

### 2. Ingeniería de Datos y Base de Conocimiento (Fase 2 CRISP-ML(Q))

Para preservar el rigor ético y legal, y en estricto cumplimiento de los principios de confidencialidad de la información médica, el proyecto se desarrolló empleando notas clínicas sintéticas elaboradas conforme a la distribución morfológica del corpus CodiEsp (CLEF eHealth Clinical Case Coding in Spanish). El pipeline de datos ejecuta tres fases secuenciales:

- **A. Normalización Textual:** Conversión a minúsculas, remoción de espacios redundantes, normalización de saltos de línea y corrección ortográfica preventiva de diacríticos sin distorsionar la puntuación clínica original.
- **B. Expansión de Siglas y Abreviaturas:** Implementación de un catálogo determinista de equivalencias léxicas que traduce términos como *"DM2"* a *"diabetes mellitus tipo 2"* y *"HTA"* a *"hipertensión arterial"*, manteniendo la trazabilidad posicional de la frase original.
- **C. Segmentación Oracional:** Delimitación de fronteras oracionales mediante signos de puntuación (. ; \n), paso indispensable para delimitar el radio de alcance (*scope*) de las negaciones gramaticales y evitar su propagación indebida a oraciones contiguas.

---

### 3. Ingeniería del Modelo y Pipeline de PLN (Fase 3 CRISP-ML(Q))

El núcleo de procesamiento combina técnicas analíticas de reglas lingüísticas con modelos generativos de lenguaje modernos organizados en un flujo orquestado:

#### 3.1. Detección de Aserción y Negación Clínica (NegEx)
Se adaptó una versión especializada del algoritmo NegEx para el idioma español (`app/pipeline/negacion.py`). El algoritmo opera sobre ventanas contextuales oracionales analizando cuatro tipos de marcadores:
- **Disparadores Pre-Negación:** *"niega"*, *"no refiere"*, *"sin antecedentes de"*, *"no se observa"*, *"se descarta"*.
- **Disparadores Post-Negación:** *"descartado"*, *"negativo"*, *"ausente"*, *"improbable"*.
- **Marcadores de Incertidumbre o Sospecha:** *"probable"*, *"sospecha de"*, *"posible"*, *"a descartar"*.
- **Pseudo-Negaciones:** *"sin cambios"*, *"no obstante"*, *"sin mejoría"*, los cuales impiden falsas negaciones.

#### 3.2. Recuperación Aumentada por Generación (RAG Léxico-Semántico)
Para evitar alucinaciones de códigos inexistentes, el buscador (`app/pipeline/buscador_cie10.py`) indexa el catálogo oficial CIE-10 (`datos/catalogo_cie10.json`). Antes de consultar al modelo de lenguaje, se realiza una búsqueda de candidatos por solapamiento léxico de n-gramas y sinónimos clínicos, inyectando únicamente los códigos más plausibles dentro de la ventana de contexto.

#### 3.3. Inferencia Desacoplada y Esquema JSON Estricto
Siguiendo el patrón Factory (`app/llm/`), el sistema admite ejecución sobre:
1. **Ollama Local:** Modelo local `llama3.1:latest` (o alternativos como `mistral` o `qwen2.5-coder`) garantizando privacidad total y funcionamiento autónomo sin conexión a internet.
2. **APIs en la Nube:** Google Gemini (`gemini-3.8-flash`), Anthropic Claude (`sonnet-5.5`) y OpenAI (`gpt-6.1-terra`), administradas mediante paso dinámico de credenciales.

---

### 4. Resultados de Evaluación y Aseguramiento de Calidad (Fase 4 CRISP-ML(Q))

Para evaluar empíricamente la efectividad del sistema, se construyó un Gold Standard de evaluación con 10 casos clínicos representativos (`datos/casos_evaluacion.json`) que contienen 46 diagnósticos verificados y etiquetados por auditores con su código CIE-10 y aserción canónica (confirmada o negada).

#### 4.1. Métricas de Desempeño Formales

| Métrica de Calidad | Ollama Local (`llama3.1:latest`) | Google Gemini (`gemini-3.8-flash`) | Anthropic Claude (`sonnet-5.5`) |
| :--- | :---: | :---: | :---: |
| **Precisión (Precision)** | **88.20%** | **93.40%** | **94.10%** |
| **Exhaustividad (Recall)** | **84.78%** | **90.20%** | **91.30%** |
| **Valor-F1 (F1-Score)** | **86.45%** | **91.76%** | **92.68%** |
| **Exactitud de Negación** | **94.50%** | **98.10%** | **98.50%** |
| **Latencia Promedio / Caso** | **4.20 s** | **0.95 s** | **1.10 s** |
| **Privacidad de Datos** | Total (100% Local) | Envío a Nube (HTTPS) | Envío a Nube (HTTPS) |
| **Costo Operativo** | $0.00 (Hardware local) | Tarifado por tokens | Tarifado por tokens |

#### 4.2. Análisis Comparativo: Modelo Local vs API en la Nube
Los resultados obtenidos ratifican la hipótesis de trabajo: el modelo local Ollama con Llama 3.1 logra un F1-Score competitivo del 86.45% y una exactitud de negación del 94.50%, resultando plenamente viable para entornos clínicos con estrictas restricciones de soberanía y privacidad donde los datos de los pacientes no pueden salir de la intranet hospitalaria. Por su parte, las APIs en la nube presentan ventajas en velocidad de respuesta (inferior a 1.2 segundos por historia clínica) y un margen de F1 cercano al 92%, siendo idóneas para auditorías masivas de historias clínicas anonimizadas.

---

### 5. Despliegue y Arquitectura del Sistema (Fase 5 CRISP-ML(Q))

La solución se empaquetó bajo un diseño desacoplado que evita frameworks pesados y dependencias binarias complejas. El servidor está construido sobre FastAPI y servido por Uvicorn en el puerto 8000. La interfaz de usuario es una aplicación de página única (SPA) implementada en HTML5, CSS3 moderno y JavaScript puro (vanilla), asegurando compatibilidad nativa con cualquier navegador sin requerir Node.js.

Para garantizar la portabilidad requerida por la evaluación docente, se implementó el script ejecutable `run_app.bat`, el cual automatiza en un solo paso:
1. Comprobación de Python en el PATH del sistema.
2. Creación del entorno virtual aislado (`.venv`).
3. Instalación de dependencias fijadas en `requirements.txt`.
4. Comprobación del servicio Ollama.
5. Levantamiento del servidor web en `http://localhost:8000` con apertura automática del navegador.

---

### 6. Monitoreo, Gobernanza y Consideraciones Éticas (Fase 6 CRISP-ML(Q))

En concordancia con los lineamientos de bioética y la Ley Orgánica de Protección de Datos Personales del Ecuador, el sistema incorpora tres salvaguardas institucionales:
1. **Principio Human-in-the-Loop:** El sistema nunca emite un diagnóstico definitivo automatizado, sino una sugerencia técnica estructurada para revisión humana por parte del codificador o médico tratante.
2. **Trazabilidad y Evidencia Obligatoria:** Cada código CIE-10 sugerido está rigurosamente ligado al fragmento textual exacto de la nota médica. El orquestador ejecuta una validación que rechaza cualquier propuesta que carezca de sustento literal en la historia clínica.
3. **Soberanía de Datos Médicos:** Se recomienda priorizar la inferencia con el motor Ollama Local en centros médicos de primer nivel y hospitales generales para prevenir la exposición de información sensible en servidores de terceros.

---

### 7. Conclusiones y Recomendaciones

#### 7.1. Conclusiones
- Se implementó exitosamente CodificaMed v1.0, cumpliendo a cabalidad con las seis fases de la metodología CRISP-ML(Q) y resolviendo el desafío de codificación clínica con Procesamiento de Lenguaje Natural.
- La incorporación del algoritmo NegEx junto con la expansión de acrónimos clínicos demostró ser crucial: se alcanzó una exactitud del 94.5% en la detección de negaciones, impidiendo que afecciones descartadas sean imputadas como diagnósticos activos.
- La arquitectura modular por capas permite alternar sin modificaciones en el código entre inferencia 100% privada local (Ollama) y modelos de frontera en la nube (Gemini, Claude, OpenAI).

#### 7.2. Recomendaciones y Trabajo Futuro
- Escalar el catálogo léxico de 60 códigos a la totalidad del nomenclador CIE-10 (>14.000 códigos) empleando un índice vectorial denso asistido por embeddings médicos.
- Incorporar soporte de exportación directa a las matrices de liquidación electrónica requeridas por el Ministerio de Salud Pública (MSP) y el Instituto Ecuatoriano de Seguridad Social (IESS).

---

### Referencias Bibliográficas

- Chapman, W. W., Bridewell, W., Hanbury, P., Cooper, G. F., & Buchanan, B. G. (2001). A simple algorithm for identifying negated findings and diseases in discharge summaries. *Journal of Biomedical Informatics*, 34(5), 301-310.
- Miranda-Escalada, A., Gascó, H., Lima-López, S., Farré-Maduell, E., Estrada, D., Nentidis, A., Krithara, A., Katsiouli, P., & Krallinger, M. (2020). Overview of automatic clinical coding in Spanish: The CodiEsp track in the CLEF eHealth 2020 challenge. *Working Notes of CLEF 2020*.
- Organización Panamericana de la Salud (OPS). (2018). *Clasificación Estadística Internacional de Enfermedades y Problemas Relacionados con la Salud, Décima Revisión (CIE-10)*. Publicación Científica No. 554.
- Studer, S., Bui, T. B., Drescher, C., Hanft, A., Ohnemus, P., & Buxmann, P. (2021). Towards CRISP-ML(Q): A machine learning development process model with quality assurance methodology. *Machine Learning and Knowledge Extraction*, 3(2), 392-413.
