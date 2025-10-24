# Usa una imagen base de Python oficial
FROM python:3.9-slim

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia los archivos de requerimientos e instálalos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación
COPY . .

# Crea un usuario no-root y cambia la propiedad del directorio de trabajo
RUN adduser --system --group appuser
RUN chown -R appuser:appuser /app

# Cambia al usuario no-root
USER appuser

# Expone el puerto que la aplicación escuchará
EXPOSE 8080

# Comando para ejecutar la aplicación usando Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]