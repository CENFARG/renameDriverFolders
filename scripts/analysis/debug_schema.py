import sys
import os
sys.path.append(os.path.abspath("packages/core-renombrador/src"))

from core_renombrador.models import FileAnalysis
from core_renombrador.agent_factory import AgentFactory
import json

def debug_schema():
    print("--- FileAnalysis Schema ---")
    schema = FileAnalysis.model_json_schema()
    print(json.dumps(schema, indent=2))
    
    print("\n--- Dynamic Model Schema ---")
    factory = AgentFactory()
    dynamic_model = factory._create_pydantic_model({
        "date": "str",
        "keywords": "list"
    })
    print(json.dumps(dynamic_model.model_json_schema(), indent=2))

if __name__ == "__main__":
    debug_schema()
