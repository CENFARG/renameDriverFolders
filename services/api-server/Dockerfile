# services/api-server/Dockerfile

# Usa una imagen base de Python oficial
FROM python:3.11-slim

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia los archivos de requerimientos e instálalos
COPY services/api-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código del microservicio
COPY services/api-server/src ./src
# También copia el paquete core-renombrador
COPY packages/core-renombrador /app/packages/core-renombrador
# Y luego instalarlo en modo editable para que pueda ser encontrado por los otros servicios
RUN pip install -e /app/packages/core-renombrador


# Crea un usuario no-root y cambia la propiedad del directorio de trabajo
RUN adduser --system --group appuser
RUN chown -R appuser:appuser /app

# Cambia al usuario no-root
USER appuser

# Expone el puerto que la aplicación escuchará
EXPOSE 8080

# Comando para ejecutar la aplicación con Uvicorn (servidor ASGI para FastAPI)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
