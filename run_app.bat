@echo off
setlocal
cd /d "%~dp0"

title CodificaMed v1.0 - Codificacion Automatica CIE-10

echo =====================================================================
echo           CodificaMed v1.0 - Instalacion y Ejecucion
echo   Codificacion Automatica CIE-10 de Historias Clinicas con PLN
echo                 Base de Conocimiento - ESPOCH
echo =====================================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        if exist ".venv\Scripts\python.exe" (
            set PYTHON_EXE=.venv\Scripts\python.exe
        ) else (
            echo [ERROR] No se encontro Python en el PATH del sistema.
            echo Por favor instala Python 3.10 o superior y marca "Add python.exe to PATH".
            echo.
            pause
            exit /b 1
        )
    ) else (
        set PYTHON_EXE=py -3
    )
) else (
    set PYTHON_EXE=python
)

if not exist ".venv" (
    echo [*] Creando entorno virtual .venv...
    %PYTHON_EXE% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el ejecutable de Python en .venv.
    pause
    exit /b 1
)

if not exist ".venv\installed.flag" (
    echo [*] Instalando dependencias de requirements.txt...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo [ERROR] Fallo la instalacion de dependencias.
        pause
        exit /b 1
    )
    echo instalado > ".venv\installed.flag"
)

if not exist ".env" (
    if exist ".env.example" (
        echo [*] Creando archivo .env desde plantilla...
        copy /y ".env.example" ".env" >nul
    )
)

echo [*] Comprobando disponibilidad del servicio local Ollama...
where ollama >nul 2>nul
if errorlevel 1 (
    echo [AVISO] Ollama no detectado en PATH.
    echo         Se utilizaran las claves de API configuradas.
) else (
    curl.exe -s -m 2 http://localhost:11434/api/tags >nul 2>nul
    if errorlevel 1 (
        echo [AVISO] Ollama esta instalado pero no esta en ejecucion.
        echo         Puedes usar API en la nube o iniciar Ollama en segundo plano.
    ) else (
        echo [OK] Ollama detectado y activo en http://localhost:11434
    )
)

echo.
echo =====================================================================
echo  Iniciando aplicacion en http://localhost:8000
echo  El navegador se abrira automaticamente. Presiona Ctrl+C para salir.
echo =====================================================================
echo.

".venv\Scripts\python.exe" main.py

echo.
echo [INFO] Servidor detenido.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
