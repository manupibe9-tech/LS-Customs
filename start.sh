#!/bin/bash
# Activar entorno virtual de Render
source /opt/render/project/src/.venv/bin/activate

# Instalar librerías (por si no están)
pip install --upgrade pip
pip install -r requirements.txt

# Ejecutar bot
python3 bot.py
