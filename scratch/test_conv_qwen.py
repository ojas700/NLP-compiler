import json
import requests
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from ai.validator import validate_intent, intent_to_il
from compiler.runner import run_compiler_pipeline

current_intent = {
    "instructions": [
        {"action": "declare", "type": "INT", "name": "num1"},
        {"action": "read", "name": "num1"},
        {"action": "declare", "type": "INT", "name": "num2"},
        {"action": "read", "name": "num2"},
        {"action": "declare", "type": "INT", "name": "sum"},
        {"action": "assign", "name": "sum", "value": "num1 + num2"},
        {"action": "print", "value": "sum"}
    ]
}

system_prompt = """You are the Conversational Program Modifier for the NLP Compiler.
The user wants to modify an existing program.

Current Program Structured Intent:
""" + json.dumps(current_intent, indent=2) + """

Rules:
1. Preserve all existing variables, reads, and computations unless the user explicitly asks to remove or change them.
2. Output ONLY a JSON object with:
   - "action_type": "update" | "clarify" | "unsupported"
   - "explanation": "<short summary of change or clarification message>"
   - "instructions": [<complete updated list of instructions using the allowed schema>]
3. Allowed actions: declare, read, assign, print, if, else, end_if, while, end_while, for, end_for.
4. If the request is ambiguous (e.g. "make it better"), set action_type to "clarify" and empty instructions.
5. If the request is outside basic C programming (e.g. databases, network), set action_type to "unsupported".
6. Never output markdown commentary. Output ONLY pure JSON.
"""

payload = {
    "model": "qwen2.5:3b",
    "format": "json",
    "stream": False,
    "options": {
        "temperature": 0.0,
        "num_predict": 300
    },
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Also print their difference"}
    ]
}

res = requests.post("http://127.0.0.1:11434/api/chat", json=payload, timeout=60)
print("Status:", res.status_code)
content = res.json().get("message", {}).get("content", "")
print("Model Output:\n", content)

parsed = json.loads(content)
ok, cleaned = validate_intent({"instructions": parsed.get("instructions", [])})
print("Validation OK:", ok)
if ok:
    il = intent_to_il(cleaned)
    print("IL Code:\n", il)
    comp = run_compiler_pipeline(il, session_id="test_conv_run")
    print("Compilation Success:", comp["success"])
    if comp["success"]:
        print("Generated C:\n", comp["c_code"])
    else:
        print("Compile Error:\n", comp["error"])
