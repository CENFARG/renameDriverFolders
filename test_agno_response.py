"""
Test script to verify Agno agent configuration and Gemini response.

This script tests if DocumentClassification schema is being used correctly.
"""

import os
import sys

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'core-renombrador', 'src'))

from agno.agent import Agent
from agno.models.google import Gemini
from core_renombrador.schemas import DocumentClassification
from core_renombrador.agent_factory import AgentFactory

# Test 1: Verify DocumentClassification exists
print("="*80)
print("TEST 1: Verify DocumentClassification import")
print("="*80)
print(f"✅ DocumentClassification: {DocumentClassification}")
print(f"✅ Fields: {DocumentClassification.model_fields.keys()}")
print()

# Test 2: Create AgentFactory and verify it can load DocumentClassification
print("="*80)
print("TEST 2: Create AgentFactory")
print("="*80)
factory = AgentFactory()
print(f"✅ AgentFactory created: {factory}")
print()

# Test 3: Create sample job config
print("="*80)
print("TEST 3: Sample job config")
print("="*80)
job_config = {
    "id": "job-manual-auto-classify",
    "name": "Document Classifier",
    "description": "Test classifier",
    "agent_config": {
        "model": {"name": "gemini-1.5-flash"},
        "instructions": "Classify this document",
        "output_schema": {
            "algorithm_id": "string",
            "date": "string"
        },
        "output": {"markdown": False}
    }
}
print(f"Job config: {job_config['id']}")
print()

# Test 4: Create agent with DocumentClassification
print("="*80)
print("TEST 4: Create agent with job config")
print("="*80)
try:
    agent = factory.create_agent_from_job_config(job_config)
    print(f"✅ Agent created: {agent}")
    print(f"✅ Agent name: {agent.name}")
    print(f"✅ Agent model: {agent.model}")

    if hasattr(agent, 'output_schema'):
        print(f"✅ Agent has output_schema: {agent.output_schema}")
    else:
        print("❌ Agent does NOT have output_schema")

except Exception as e:
    print(f"❌ Error creating agent: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 5: Run agent with simple prompt
print("="*80)
print("TEST 5: Run agent with test prompt")
print("="*80)
try:
    response = agent.run("Classify this document: Invoice #123 from ACME Corp dated 2024-03-15")
    print(f"✅ Response type: {type(response)}")
    print(f"✅ Response: {response}")

    if hasattr(response, 'content'):
        print(f"✅ Response.content type: {type(response.content)}")
        print(f"✅ Response.content: {response.content}")

        # Check if it's a DocumentClassification
        if isinstance(response.content, DocumentClassification):
            print("✅ Response.content IS a DocumentClassification!")
            print(f"✅ algorithm_id: {response.content.algorithm_id}")
            print(f"✅ date: {response.content.date}")
        elif isinstance(response.content, dict):
            print("⚠️  Response.content is a dict:")
            print(f"   {response.content}")
        else:
            print(f"⚠️  Response.content is: {type(response.content)}")

except Exception as e:
    print(f"❌ Error running agent: {e}")
    import traceback
    traceback.print_exc()
print()

print("="*80)
print("TESTS COMPLETED")
print("="*80)
