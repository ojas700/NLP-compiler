import json
import re

ALLOWED_ACTIONS = {"declare", "assign", "read", "print", "if", "else", "end_if", "while", "end_while", "for", "end_for"}
ALLOWED_TYPES = {"INT", "FLOAT", "CHAR"}

def validate_intent(intent_data):
    """
    Validates the structured JSON produced by Qwen or cache.
    Returns (True, cleaned_instructions) or (False, error_message).
    """
    if not isinstance(intent_data, dict):
        return False, "Root JSON must be an object with an 'instructions' list."
    
    instructions = intent_data.get("instructions")
    if not isinstance(instructions, list):
        return False, "'instructions' must be a list."
    
    cleaned = []
    for idx, item in enumerate(instructions):
        if not isinstance(item, dict):
            return False, f"Instruction #{idx+1} is not an object."
        
        action = str(item.get("action", "")).strip().lower()
        if action not in ALLOWED_ACTIONS:
            return False, f"Instruction #{idx+1} has invalid action '{action}'."
        
        c_item = {"action": action}
        
        if action == "declare":
            var_type = str(item.get("type", "INT")).strip().upper()
            var_name = str(item.get("name", "")).strip()
            if var_type not in ALLOWED_TYPES:
                return False, f"Instruction #{idx+1}: invalid type '{var_type}'."
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
                return False, f"Instruction #{idx+1}: invalid variable name '{var_name}'."
            c_item["type"] = var_type
            c_item["name"] = var_name
            
        elif action == "assign":
            var_name = str(item.get("name", "")).strip()
            expr = str(item.get("value", "")).strip()
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
                return False, f"Instruction #{idx+1}: invalid assignment target '{var_name}'."
            if not expr:
                return False, f"Instruction #{idx+1}: empty assignment value."
            c_item["name"] = var_name
            c_item["value"] = expr
            
        elif action == "read":
            var_name = str(item.get("name", "")).strip()
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
                return False, f"Instruction #{idx+1}: invalid read target '{var_name}'."
            c_item["name"] = var_name
            
        elif action == "print":
            val = str(item.get("value", "")).strip()
            if not val:
                return False, f"Instruction #{idx+1}: empty print target."
            c_item["value"] = val
            
        elif action in ("if", "while"):
            cond = str(item.get("condition", "")).strip()
            if not cond:
                return False, f"Instruction #{idx+1}: empty condition for {action}."
            c_item["condition"] = cond
            
        elif action == "for":
            var_name = str(item.get("variable", "")).strip()
            start = str(item.get("start", "1")).strip()
            end = str(item.get("end", "")).strip()
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
                return False, f"Instruction #{idx+1}: invalid loop variable '{var_name}'."
            if not end:
                return False, f"Instruction #{idx+1}: empty loop end boundary."
            c_item["variable"] = var_name
            c_item["start"] = start
            c_item["end"] = end
            
        cleaned.append(c_item)
        
    return True, cleaned

def intent_to_il(instructions):
    """
    Converts validated structured intent instructions into standard Intermediate Language lines.
    Ensures that any variable referenced in read or assign has a declaration.
    """
    declared = set()
    for item in instructions:
        if item["action"] == "declare":
            declared.add(item["name"])

    # Identify any variables used in assign/read that were not declared
    needed_declarations = []
    for item in instructions:
        action = item["action"]
        if action in ("read", "assign") and item.get("name") not in declared:
            name = item.get("name")
            if name and name not in needed_declarations:
                needed_declarations.append(name)
                declared.add(name)

    il_lines = []
    for var in needed_declarations:
        il_lines.append(f"DECLARE INT {var}")

    for item in instructions:
        action = item["action"]
        if action == "declare":
            il_lines.append(f"DECLARE {item['type']} {item['name']}")
        elif action == "assign":
            il_lines.append(f"ASSIGN {item['name']} {item['value']}")
        elif action == "read":
            il_lines.append(f"READ {item['name']}")
        elif action == "print":
            il_lines.append(f"PRINT {item['value']}")
        elif action == "if":
            il_lines.append(f"IF {item['condition']}")
        elif action == "else":
            il_lines.append("ELSE")
        elif action == "end_if":
            il_lines.append("END_IF")
        elif action == "while":
            il_lines.append(f"WHILE {item['condition']}")
        elif action == "end_while":
            il_lines.append("END_WHILE")
        elif action == "for":
            il_lines.append(f"FOR {item['variable']} {item['start']} {item['end']}")
        elif action == "end_for":
            il_lines.append("END_FOR")
            
    return "\n".join(il_lines)