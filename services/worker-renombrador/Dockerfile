# services/worker-renombrador/Dockerfile

# Usa una imagen base de Python oficial
FROM python:3.11-slim

# Instalar dependencias del sistema para pdf2image (soporte OCR)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    git \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo en /app
WORKDIR /app

# Primero instalar el core package desde GitHub (temporal para build)
# En producción, esto debería venir de un registry privado
# context: project root (.)

# Copiar requirements del servicio especifico
COPY services/worker-renombrador/requirements.txt .

# Copiar paquete core compartido e instalarlo
COPY packages ./packages
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir ./packages/core-renombrador

# Copiar código del worker (desde la raiz)
COPY services/worker-renombrador/src ./src
COPY services/worker-renombrador/config ./config
COPY services/worker-renombrador/data ./data

# Crea un usuario no-root y cambia la propiedad del directorio de trabajo
RUN adduser --system --group appuser
RUN chown -R appuser:appuser /app

# Cambia al usuario no-root
USER appuser

# Expone el puerto que la aplicación escuchará
EXPOSE 8080

# Comando para ejecutar la aplicación con Uvicorn (servidor ASGI para FastAPI)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
