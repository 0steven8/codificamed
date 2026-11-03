from __future__ import annotations

import sys
import subprocess
import webbrowser
from pathlib import Path
import uvicorn

# Agrega directorio raiz al path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.config import settings
from app.main import app


def liberar_puerto(puerto: int) -> None:
    # Libera el puerto si un proceso previo sigue activo
    try:
        cmd = f"netstat -ano | findstr :{puerto} | findstr LISTENING"
        salida = subprocess.check_output(cmd, shell=True, text=True)
        for linea in salida.strip().splitlines():
            partes = linea.split()
            if partes:
                pid = partes[-1]
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
    except Exception:
        pass


if __name__ == "__main__":
    puerto = settings.puerto
    host = settings.host
    url = f"http://localhost:{puerto}"

    # Asegura disponibilidad del puerto
    liberar_puerto(puerto)

    print("=" * 65)
    print(" CodificaMed v1.0 - Codificacion Automatica CIE-10 con PLN")
    print(" Base de Conocimiento - ESPOCH - FIE")
    print(f" Servidor iniciado en: {url}")
    print(" Presiona Ctrl+C para detener el servidor.")
    print("=" * 65)

    try:
        webbrowser.open(url)
    except Exception:
        pass

    uvicorn.run("app.main:app", host=host, port=puerto, reload=False)
