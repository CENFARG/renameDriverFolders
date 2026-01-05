import sys
import os
import pytest
from dotenv import load_dotenv

# Add package source to path
sys.path.append(os.path.abspath("packages/core-renombrador/src"))

from core_renombrador.agent_factory import AgentFactory
from core_renombrador.models import FileAnalysis

# Simulation of Diego Cutignola's document content (excerpt)
SAMPLE_CONTENT = """
1. Síntesis Ejecutiva (El Mensaje Real)
La Máscara (Lo que intentaron decir): “La AGI llegará en 2028...”
El Rostro (Lo que realmente informaron): Los actores tecnológicos están acelerando...

2. Deconstrucción: Narrativa vs. Datos Duros
Dispositivo Narrativo (El Relato)	Realidad Pragmática (El Dato Duro)
“Estamos a las puertas de la AGI en 2028.”	Proyección de desarrollo...

3. Radar de Ambigüedad Estratégica ("Hacerse el Boludo")
Racionalización Retrospectiva: Presentan la aceleración hacia AGI...
"""

def test_category_extraction():
    """Test that the agent extracts a valid category from consulting content."""
    load_dotenv()
    
    if not os.getenv("GEMINI_API_KEY"):
        print("Skipping test: GEMINI_API_KEY not set")
        return

    if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY").strip('"').strip("'")

    print("\n--- Initializing Agent ---")
    factory = AgentFactory()
    
    # Updated to a known available model from the list
    agent_config = {
        "model_id": "gemini-2.0-flash",
        "temperature": 0.0,
        "prompt_template": "Analyze this content and extract structured data:\n\n{file_content}"
    }
    
    agent = factory.create_agent_with_defaults(
        instructions=agent_config["prompt_template"],
        model_id=agent_config["model_id"],
        output_schema=FileAnalysis
    )
    
    print("--- Running Analysis on Sample Content ---")
    response = agent.run(agent_config["prompt_template"].format(file_content=SAMPLE_CONTENT))
    
    print("\n--- Raw Response Content ---")
    print(str(response.content))
    
    assert hasattr(response, 'content'), "Response must have content"
    
    analysis = response.content
    print(f"\n--- Analysis Object Type: {type(analysis)} ---")
    
    if hasattr(analysis, 'category'):
        print(f"Category Extracted: {analysis.category}")
        assert analysis.category in ["Informe Estratégico", "Análisis de Discurso", "Síntesis Ejecutiva", "Varios", "Reporte", "Consultoría"], f"Unexpected category: {analysis.category}"
    else:
        # Fallback if it returns dict or raw string
        print("category field not found directly in response object. Checking parsing fallback...")
        import json
        try:
            data = None
            if isinstance(analysis, str):
                 raw_json = analysis
                 if "```json" in raw_json:
                     raw_json = raw_json.split("```json")[1].split("```")[0]
                 elif "```" in raw_json:
                     raw_json = raw_json.split("```")[1].split("```")[0]
                 data = json.loads(raw_json.strip())
            elif isinstance(analysis, dict):
                 data = analysis
            
            if data:
                 print(f"Parsed Data: {data}")
                 assert "category" in data, "Parsed data must have 'category'"
            else:
                 print("Could not extract data from response.")
                 raise ValueError("Empty or unparseable analysis")
        except Exception as e:
             print(f"Parsing failed: {e}")
             raise

if __name__ == "__main__":
    test_category_extraction()
