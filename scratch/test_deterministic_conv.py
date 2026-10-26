import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from ai.validator import validate_intent, intent_to_il
from compiler.runner import run_compiler_pipeline

def test_program_creation():
    initial_instructions = [
        {"action": "declare", "type": "INT", "name": "num1"},
        {"action": "read", "name": "num1"},
        {"action": "declare", "type": "INT", "name": "num2"},
        {"action": "read", "name": "num2"},
        {"action": "declare", "type": "INT", "name": "sum"},
        {"action": "assign", "name": "sum", "value": "num1 + num2"},
        {"action": "print", "value": "sum"}
    ]
    
    ok, cleaned = validate_intent({"instructions": initial_instructions})
    assert ok
    il = intent_to_il(cleaned)
    comp = run_compiler_pipeline(il, session_id="test_stage1")
    assert comp["success"]
    print("Scenario 1 (Initial Program): SUCCESS")
    print(comp["c_code"])
    return cleaned, comp["c_code"]

cleaned_1, c_code_1 = test_program_creation()
