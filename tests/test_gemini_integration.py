
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregamos paths
sys.path.append(os.path.abspath("packages/core-renombrador/src"))
# Agregamos src directamente para importar models
sys.path.append(os.path.abspath("services/worker-renombrador/src"))

# Importamos AgentFactory
from core_renombrador.agent_factory import AgentFactory
# Importamos models directamente ya que 'src' esta en el path
from models import FileAnalysis

def run_test():
    print("=" * 80)
    print(" TEST DE INTEGRACIÓN LOCAL DE GEMINI (VERTEX AI)")
    print("=" * 80)

    # 1. Configurar Entorno (Simular Cloud Run)
    os.environ["GCP_PROJECT"] = "cloud-functions-474716"
    os.environ["GCP_LOCATION"] = "us-central1"
    # No necesitamos API KEY si tenemos credenciales de gcloud
    
    print(f" Configuracion:")
    print(f"  Project: {os.environ['GCP_PROJECT']}")
    print(f"  Location: {os.environ['GCP_LOCATION']}")
    
    # 2. Cargar Job Config (Simulado o real)
    # Cargamos el archivo jobs.json real para usar la misma config que produccion
    try:
        with open("services/worker-renombrador/data/jobs.json", "r", encoding="utf-8") as f:
            jobs = json.load(f)
            job_config = next((j for j in jobs if j["id"] == "job-manual-generic"), None)
            
        if not job_config:
            print(" Error: No se encontró 'job-manual-generic' en jobs.json")
            return
            
        print(f" Job Config cargado: {job_config['id']}")
        print(f"  Model: {job_config['agent_config']['model']['name']}")
        
    except Exception as e:
        print(f" Error cargando jobs.json: {e}")
        return

    # 3. Crear Agente
    try:
        factory = AgentFactory() # No necesitamos DB manager para este test simple
        agent = factory.create_agent_from_job_config(job_config)
        print(" Agente creado exitosamente.")
    except Exception as e:
        print(f" Error creando agente: {e}")
        return

    # 4. Definir Prompt de Prueba (Simulando un archivo extraído)
    test_content = """
    ESTUDIO JURIDICO CUTIGNOLA
    FACTURA A  N° 0001-00001234
    FECHA: 27/05/2024
    CLIENTE: BANCO GALICIA
    CONCEPTO: HONORARIOS PROFESIONALES JUICIO EJECUTIVO
    TOTAL: $ 150.000,00
    CAE: 71234567890123
    """
    
    test_filename = "documento_desconocido.pdf"
    
    # Formatear el prompt usando el template del job
    prompt_template = job_config["agent_config"]["prompt_template"]
    full_prompt = prompt_template.format(
        original_filename=test_filename,
        file_content=test_content
    )
    
    print("\n Enviando Prompt a Gemini (Vertex AI)...")
    print("-" * 40)
    print(full_prompt[:500] + "...")
    print("-" * 40)

    # 5. Ejecutar Agente
    try:
        response = agent.run(full_prompt)
        
        print("\n Respuesta de Gemini:")
        print("=" * 80)
        
        # Parsear respuesta (simulando lógica del Worker)
        if hasattr(response, 'content'):
             # Verificar si es un modelo Pydantic
            if hasattr(response.content, 'model_dump'):
                data = response.content.model_dump()
                print(f" Respuesta Estructurada (Pydantic):\n{json.dumps(data, indent=2)}")
            else:
                 print(f" Respuesta Raw (No Pydantic):\n{response.content}")
        else:
             print(f" Respuesta extraña:\n{response}")
             
        print("=" * 80)
        
    except Exception as e:
        print(f" Error ejecutando agente: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
