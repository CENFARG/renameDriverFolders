#!/usr/bin/env python3
"""Verifica que contiene un folder de Drive"""

import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

load_dotenv()

# Usar el access token de los logs (necesitamos uno nuevo)
# Por ahora vamos a pedirlo al usuario

print("=" * 60)
print("VERIFICAR CONTENIDO DE CARPETA DRIVE")
print("=" * 60)
print()
print("Para verificar que contiene la carpeta 1JD-53D0ONkRvyqW9TbquA9Z15Z8WyKLH,")
print("necesitamos un OAuth token válido.")
print()
print("Opciones:")
print("1. Abre Drive UI: https://drive.google.com/drive/u/0/folders/1JD-53D0ONkRvyqW9TbquA9Z15Z8WyKLH")
print("   - ¿Ves archivos directamente?")
print("   - ¿O solo subcarpetas?")
print()
print("2. Ejecuta esto en la consola del browser después de hacer login en la UI:")
print("   localStorage.getItem('oauth_token')")
print()
