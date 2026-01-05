# main.py

# Este archivo es el punto de entrada original del proyecto monolítico.
# Su contenido ha sido refactorizado y movido a la nueva arquitectura de microservicios.
# Por favor, consulta los nuevos servicios en `services/` y el paquete de lógica compartida en `packages/core-renombrador/`.

import logging
from flask import Flask

logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route("/")
def hello_world():
    logger.info("El servicio monolítico ha sido invocado. Por favor, utiliza los nuevos microservicios.")
    return "Hello from the old monolithic service. Please refer to the new microservices architecture.", 200

if __name__ == "__main__":
    # Esta parte solo es relevante para el desarrollo local del monolito original.
    # En la nueva arquitectura, los servicios se ejecutarán de forma independiente.
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Iniciando servicio monolítico en http://0.0.0.0:{port}")
    app.run(debug=True, host="0.0.0.0", port=port)