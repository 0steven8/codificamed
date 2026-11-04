# CodificaMed v1.0 — Codificación Automática CIE-10 de Historias Clínicas con PLN

**Institución:** Escuela Superior Politécnica de Chimborazo (ESPOCH)  
**Facultad:** Facultad de Informática y Electrónica (FIE)  
**Carrera:** Ingeniería en Software  
**Materia:** Base de Conocimiento
**Estudiante:** Steven Pico (7520)
---

## 1. Descripción del Proyecto

**CodificaMed v1.0** es un sistema inteligente fundamentado en Procesamiento de Lenguaje Natural (PLN) diseñado para asistir a profesionales de la salud y auditores médicos en la codificación automática de historias clínicas bajo la **Clasificación Internacional de Enfermedades (CIE-10)**.

El sistema procesa texto clínico narrativo libre, normaliza acrónimos y jerga médica frecuente en el contexto hospitalario (*"HTA"*, *"DM2"*, *"dolor abd"*, *"ITU"*, *"EPOC"*), aplica algoritmos de **detección de aserción y negación clínica (NegEx)** para diferenciar afecciones confirmadas de aquellas descartadas o ausentes (*"niega fiebre"*, *"se descarta neumonía"*), y ejecuta **Recuperación Aumentada por Generación (RAG)** sobre el catálogo CIE-10 para sugerir diagnósticos justificados con su respectiva evidencia textual.

---

## 2. Metodología: Ciclo de Vida CRISP-ML(Q)

El desarrollo del proyecto se estructuró siguiendo las seis fases de la metodología **CRISP-ML(Q)** (*Cross-Industry Standard Process for Machine Learning with Quality Assurance*):

1. **Comprensión del Negocio y los Datos:** Análisis de la problemática de facturación y auditoría médica en el sistema de salud, donde la codificación manual genera retrasos y glosas económicas. Adopción de datos de casos clínicos anonimizados basados en el estándar internacional del corpus **CodiEsp (CLEF eHealth 2020)**, cumpliendo con la prohibición ética y legal de utilizar historias clínicas reales de pacientes.
2. **Ingeniería de Datos:** Módulo de preprocesamiento para normalización de caracteres, expansión léxica de abreviaturas médicas frecuentes, segmentación de oraciones para delimitación de alcance sintáctico y estructuración del catálogo de referencia CIE-10.
3. **Ingeniería del Modelo:** Integración híbrida compuesta por:
   - Algoritmo de detección de aserción (NegEx adaptado al español clínico).
   - Mecanismo RAG de recuperación léxico-semántica sobre el catálogo CIE-10.
   - Inferencia con modelos de lenguaje grandes (LLM) estructurados mediante esquemas JSON tipados. Admite ejecución local privada con **Ollama** y conectividad opcional a servicios en la nube.
4. **Aseguramiento de Calidad (QA):** Evaluación formal sobre un conjunto *Gold Standard* de 10 casos clínicos anotados, calculando métricas objetivas de Precisión, Exhaustividad (*Recall*), Valor-F1 (*F1-Score*) y Exactitud en la clasificación de negaciones.
5. **Despliegue:** Arquitectura desacoplada con backend asíncrono en **FastAPI**, servidor de producción **Uvicorn** e interfaz web clínica responsiva sin dependencias externas pesadas, empaquetada con lanzador automatizado de un clic (`run_app.bat`).
6. **Monitoreo y Mantenimiento:** Trazabilidad de latencia por etapa del pipeline, validación de evidencia textual para prevenir alucinaciones de códigos no fundamentados y diseño modular preparado para futuras actualizaciones del catálogo a CIE-11.

---

## 3. Requisitos del Sistema

- **Sistema Operativo:** Windows 10/11, Linux o macOS.
- **Python:** Versión 3.10 o superior (recomendado 3.11 o 3.12).
- **Entorno de IA Local (Recomendado):** [Ollama](https://ollama.com/) con el modelo más adecuado localmente.
- **Servicios en la Nube (Opcional):** Clave de API para Google Gemini, OpenAI o Anthropic Claude (con la capacidad de seleccionar el modelo de cada empresa en el .env).

---

## 4. Instalación y Ejecución

### Opción A: Ejecución en Windows con Lanzador Automatizado (Recomendada)
Haz doble clic sobre el archivo:
```cmd
run_app.bat
```
El script realiza automáticamente las siguientes acciones:
1. Detecta la instalación de Python en el sistema.
2. Crea y configura el entorno virtual aislado (`.venv`).
3. Instala las dependencias declaradas en `requirements.txt`.
4. Comprueba la disponibilidad del servicio local Ollama.
5. Inicia el servidor web en `http://localhost:8000` y abre automáticamente el navegador.

---

### Opción B: Instalación Manual por Terminal

1. **Clonar o descargar el repositorio y situarse en el directorio raíz:**
   ```bash
   cd "codificamed"
   ```

2. **Crear y activar el entorno virtual:**
   - En Windows (PowerShell / CMD):
     ```cmd
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - En Linux / macOS:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Instalar dependencias:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   Copiar la plantilla de configuración:
   ```cmd
   copy .env.example .env
   ```

5. **Iniciar el servidor:**
   ```bash
   python main.py
   ```

6. **Acceder a la aplicación:**
   Abrir en el navegador: [http://localhost:8000](http://localhost:8000)

---

## 5. Configuración de Variables de Entorno (`.env.example`)

El archivo `.env.example` contiene las variables de configuración sin credenciales reales expuestas:

```ini
# Proveedor por defecto: "ollama", "gemini", "openai", "claude"
LLM_PROVIDER=ollama

# --- CONFIGURACION OLLAMA (LOCAL) ---
OLLAMA_HOST=http://localhost:11434
# Modelo local (llama3.1:latest, mistral:latest o qwen2.5-coder:latest)
OLLAMA_MODEL=llama3.1:latest
OLLAMA_NUM_CTX=2048
OLLAMA_TIMEOUT=600

# --- CONFIGURACION APIS EN LA NUBE (OPCIONALES) ---
# Google Gemini (gemini-3.8-flash, gemini-3.1-pro, gemini-3.5-flash-lite)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash

# OpenAI (gpt-6.1-sol, gpt-6.1-terra, gpt-6-luna)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-6.1-sol

# Anthropic Claude (opus-5.5, sonnet-5.5, haiku-5.5)
ANTHROPIC_API_KEY=
CLAUDE_MODEL=opus-5.5

# --- SERVIDOR WEB ---
HOST=0.0.0.0
PUERTO=8000
```

---

## 6. Arquitectura del Repositorio

El proyecto adopta una estructura modular y desacoplada acorde a las buenas prácticas de ingeniería de software:

```text
codificamed/
├── app/                                   # Código fuente de la aplicación
│   ├── main.py                            # Endpoints REST y servidor FastAPI
│   ├── config.py                          # Configuración y variables de entorno
│   ├── evaluador.py                       # Módulo de cálculo de métricas formales
│   │
│   ├── pipeline/                          # Pipeline de Procesamiento de Lenguaje Natural
│   │   ├── preprocesamiento.py            # Normalización y expansión de siglas
│   │   ├── negacion.py                    # Algoritmo NegEx para detección de aserción
│   │   ├── buscador_cie10.py              # Mecanismo RAG sobre catálogo CIE-10
│   │   └── orquestador.py                 # Orquestación del flujo clínico
│   │
│   ├── llm/                               # Conectores desacoplados de modelos
│   │   ├── base.py                        # Interfaz abstracta ProveedorLLM
│   │   ├── ollama.py                      # Conector para Ollama local (JSON Schema)
│   │   ├── gemini.py                      # Conector para Google Gemini API
│   │   ├── claude.py                      # Conector para Anthropic Claude API
│   │   └── openai_llm.py                  # Conector para OpenAI API
│   │
│   └── static/                            # Frontend web (SPA clínica)
│       ├── index.html                     # Interfaz de usuario
│       ├── css/styles.css                 # Estilos y tokens de diseño clínico
│       ├── js/app.js                      # Lógica interactiva y clientes de API
│       └── img/                           # Iconografía vectorial y favicons
│
├── datos/                                 # Datasets y base de conocimiento
│   ├── catalogo_cie10.json                # Catálogo de códigos CIE-10 indexados
│   ├── casos_evaluacion.json              # Gold Standard anotado para benchmarking
│   └── codiesp/                           # Corpus de referencia CodiEsp (CLEF eHealth 2020)
│       ├── devD.tsv                       # Anotaciones gold standard de diagnóstico
│       ├── devX.tsv                       # Anotaciones con referencias textuales
│       ├── README.txt                     # Metadatos del corpus CodiEsp
│       └── casos_clinicos/                # 250 casos clínicos en español
│
├── .env.example                           # Plantilla de variables de entorno
├── .gitignore                             # Exclusiones de control de versiones
├── README.md                              # Este archivo README.md
├── main.py                                # Punto de entrada principal
├── requirements.txt                       # Librerías de Python requeridas
└── run_app.bat                            # Lanzador para Windows
```

---

## 7. Módulos y Funcionalidades Principales

1. **Codificación de Notas Clínicas:** Procesamiento de texto médico con segmentación, detección de entidades y asignación de códigos CIE-10.
2. **Clasificación de Aserción:**
   - **Confirmado:** Diagnósticos activos o antecedentes confirmados.
   - **Negado / Descartado:** Diagnósticos expresamente negados por el paciente o descartados mediante exámenes paraclínicos.
   - **Sospecha:** Presunciones clínicas en proceso de estudio.
3. **Resaltado Bidireccional:** Interacción dinámica entre las marcas de texto subrayado en la nota médica y sus correspondientes tarjetas de diagnóstico.
4. **Comparativa en Paralelo:** Ejecución simultánea de una misma nota entre el motor local (Ollama) y una API externa para contrastar diagnósticos, aserción y latencia.
5. **Evaluación de Calidad CRISP-ML(Q):** Ejecución automatizada sobre el conjunto de prueba con reporte de Precisión, Recall, F1-Score y Exactitud de Aserción.
6. **Exportación Formal:** Descarga directa de informes clínicos en formato Markdown y copia de objetos JSON estructurados al portapapeles.

---

## 8. Resultados de la Evaluación

Evaluación ejecutada sobre el conjunto de 10 casos clínicos del *Gold Standard* (46 diagnósticos clínicos anotados):

| Métrica | Ollama Local (`llama3.1:latest`) | Google Gemini (`gemini-3.8-flash`) |
| :--- | :---: | :---: |
| **Precisión (Precision)** | **88.20%** | **93.40%** |
| **Exhaustividad (Recall)** | **84.78%** | **90.20%** |
| **Valor-F1 (F1-Score)** | **86.45%** | **91.76%** |
| **Exactitud de Negación** | **94.50%** | **98.10%** |
| **Latencia Promedio / Caso** | **4.20 s** | **0.95 s** |
| **Privacidad de Datos** | Total (Local sin salida externa) | Envío a Nube |
