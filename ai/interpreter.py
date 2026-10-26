import requests
import json
import re
from pathlib import Path
try:
    from ai.validator import validate_intent, intent_to_il
except ImportError:
    from validator import validate_intent, intent_to_il

PROMPT_FILE = Path(__file__).parent / "prompt.txt"
with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# Query Cache for token efficiency & instant repeated executions
_QUERY_CACHE = {}

def extract_json(raw_text):
    """Safely extracts JSON object from model output."""
    raw_text = raw_text.strip()
    # Check if wrapped in markdown code blocks
    code_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text)
    if code_match:
        raw_text = code_match.group(1).strip()
    
    # Try finding outermost { }
    start = raw_text.find('{')
    end = raw_text.rfind('}')
    if start != -1 and end != -1 and end > start:
        candidate = raw_text[start:end+1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
    
    return json.loads(raw_text)

# Deterministic semantic patterns for common unambiguous natural language requests
def parse_deterministic_nl(text: str):
    """
    Safely parses common, unambiguous programming requests locally in ~0.5ms.
    Returns structured instructions list or None if ambiguous/unrecognized.
    """
    t_clean = re.sub(r'[\.\,\;]+$', '', text.strip()).strip()
    
    # 1. Two numbers operations (add, subtract, multiply, divide, modulo, conditions, loops)
    if re.search(r'(?:ask.*(?:user.*for.*)?two numbers|take.*two numbers|accept.*two numbers|input.*two numbers|two numbers)', t_clean, re.I):
        has_add = bool(re.search(r'\b(?:add|sum|plus)\b', t_clean, re.I))
        has_diff = bool(re.search(r'\b(?:diff|difference|subtract|minus)\b', t_clean, re.I))
        has_mult = bool(re.search(r'\b(?:mult|multiply|product|times)\b', t_clean, re.I))
        has_div = bool(re.search(r'\b(?:div|divide|quotient)\b', t_clean, re.I))
        has_rem = bool(re.search(r'\b(?:mod|modulo|remainder)\b', t_clean, re.I))
        
        # Default to add if none explicitly specified
        if not (has_add or has_diff or has_mult or has_div or has_rem):
            has_add = True

        var_num1 = "num1"
        var_num2 = "num2"
        sum_var = "sum"

        # Check for rename instructions in natural language
        # Examples: rename "result" to "sum", rename result to total, rename sum to total, rename num1 to a
        for rm in re.finditer(r'rename\s+(?:the\s+)?(?:variable\s+)?["\']?([a-zA-Z_]\w*)["\']?\s+to\s+["\']?([a-zA-Z_]\w*)["\']?', t_clean, re.I):
            src, dst = rm.group(1).lower(), rm.group(2)
            if src in ("num1", "first", "n1", "x"):
                var_num1 = dst
            elif src in ("num2", "second", "n2", "y"):
                var_num2 = dst
            elif src in ("result", "sum", "res", "total", "add", "ans"):
                sum_var = dst

        # Check for change/name variable to ...
        m_change_to = re.search(r'(?:change\s+(?:the\s+)?variable(?:\s+name)?|name\s+(?:the\s+)?variable)\s+(?:from\s+["\']?\w+["\']?\s+)?to\s+["\']?([a-zA-Z_]\w*)["\']?', t_clean, re.I)
        if m_change_to:
            sum_var = m_change_to.group(1)
        elif re.search(r'\b(?:total)\b', t_clean, re.I) and sum_var == "sum" and not re.search(r'to\s+["\']?sum["\']?', t_clean, re.I):
            sum_var = "total"

        instructions = [
            {"action": "declare", "type": "INT", "name": var_num1},
            {"action": "read", "name": var_num1},
            {"action": "declare", "type": "INT", "name": var_num2},
            {"action": "read", "name": var_num2}
        ]

        if has_add:
            instructions.extend([
                {"action": "declare", "type": "INT", "name": sum_var},
                {"action": "assign", "name": sum_var, "value": f"{var_num1} + {var_num2}"},
                {"action": "print", "value": sum_var}
            ])
        if has_diff:
            instructions.extend([
                {"action": "declare", "type": "INT", "name": "diff"},
                {"action": "assign", "name": "diff", "value": f"{var_num1} - {var_num2}"},
                {"action": "print", "value": "diff"}
            ])
        if has_mult:
            instructions.extend([
                {"action": "declare", "type": "INT", "name": "prod"},
                {"action": "assign", "name": "prod", "value": f"{var_num1} * {var_num2}"},
                {"action": "print", "value": "prod"}
            ])
        if has_div:
            instructions.extend([
                {"action": "declare", "type": "INT", "name": "quot"},
                {"action": "assign", "name": "quot", "value": f"{var_num1} / {var_num2}"},
                {"action": "print", "value": "quot"}
            ])
        if has_rem:
            instructions.extend([
                {"action": "declare", "type": "INT", "name": "rem"},
                {"action": "assign", "name": "rem", "value": f"{var_num1} % {var_num2}"},
                {"action": "print", "value": "rem"}
            ])

        # Check for condition: positive
        if re.search(r'\b(?:positive|greater than 0)\b', t_clean, re.I):
            res_var = sum_var if has_add else (instructions[-3]["name"] if len(instructions) >= 3 else "num1")
            instructions.extend([
                {"action": "if", "condition": f"{res_var} > 0"},
                {"action": "print", "value": "1"},
                {"action": "else"},
                {"action": "print", "value": "0"},
                {"action": "end_if"}
            ])

        # Check for loop
        m_loop_times = re.search(r'\b(?:repeat|loop)\b.*?\b(\d+|three|four|five)\s*times', t_clean, re.I)
        if m_loop_times:
            cnt_raw = m_loop_times.group(1).lower()
            word_map = {"three": "3", "four": "4", "five": "5"}
            cnt = word_map.get(cnt_raw, cnt_raw)
            wrapped = [
                {"action": "declare", "type": "INT", "name": "i"},
                {"action": "for", "variable": "i", "start": "1", "end": cnt}
            ]
            wrapped.extend(instructions)
            wrapped.append({"action": "end_for"})
            instructions = wrapped

        return instructions

    # 2. Even or odd
    m_even = re.search(r'ask.*(?:user.*for.*a.*number|number).*if.*(?:number\s*%\s*2\s*==\s*0|\b(?:its|it is|is)\s*even\b).*print\s*(\w+).*else.*print\s*(\w+)', t_clean, re.I)
    if m_even:
        p1, p2 = m_even.group(1), m_even.group(2)
        return [
            {"action": "declare", "type": "INT", "name": "num"},
            {"action": "read", "name": "num"},
            {"action": "if", "condition": "num % 2 == 0"},
            {"action": "print", "value": p1},
            {"action": "else"},
            {"action": "print", "value": p2},
            {"action": "end_if"}
        ]

    # 3. For loop summation: for <var> from <start> to <end>, set <target> to <expr>, print <res>
    m_loop = re.search(r'for\s+([a-zA-Z_]\w*)\s+from\s+(\d+)\s+to\s+(\d+).*set\s+([a-zA-Z_]\w*)\s+to\s+([^\,]+).*print\s+([a-zA-Z_]\w*)', t_clean, re.I)
    if m_loop:
        var, start, end, target, expr, pr = m_loop.groups()
        return [
            {"action": "declare", "type": "INT", "name": target},
            {"action": "declare", "type": "INT", "name": var},
            {"action": "for", "variable": var, "start": start, "end": end},
            {"action": "assign", "name": target, "value": expr.strip()},
            {"action": "end_for"},
            {"action": "print", "value": pr}
        ]

    # 4. Temperature / Linear expression conversion
    m_temp = re.search(r'ask.*user.*for\s+([a-zA-Z_]\w*).*set\s+([a-zA-Z_]\w*)\s+to\s+([^,]+).*print\s+([a-zA-Z_]\w*)', t_clean, re.I)
    if m_temp:
        in_var, out_var, expr, pr = m_temp.groups()
        return [
            {"action": "declare", "type": "INT", "name": in_var},
            {"action": "read", "name": in_var},
            {"action": "declare", "type": "INT", "name": out_var},
            {"action": "assign", "name": out_var, "value": expr.strip()},
            {"action": "print", "value": pr}
        ]

    return None

# Persistent session for connection reuse
_SESSION = requests.Session()

def interpret_natural_language(user_text, ollama_url="http://127.0.0.1:11434"):
    """
    Parses natural language into structured JSON intent and IL code.
    Checks query cache -> deterministic shortcut -> Qwen 2.5 3B fallback.
    Returns (success, structured_json, il_code, error_message).
    """
    clean_text = user_text.strip()
    if clean_text in _QUERY_CACHE:
        intent = _QUERY_CACHE[clean_text]
        ok, cleaned = validate_intent(intent)
        if ok:
            return True, {"instructions": cleaned}, intent_to_il(cleaned), None

    # Step 1: Check safe deterministic local shortcut (instant ~0.5ms)
    fast_instructions = parse_deterministic_nl(clean_text)
    if fast_instructions is not None:
        ok, cleaned = validate_intent({"instructions": fast_instructions})
        if ok:
            il_code = intent_to_il(cleaned)
            structured_res = {"instructions": cleaned}
            _QUERY_CACHE[clean_text] = structured_res
            return True, structured_res, il_code, None

    payload = {
        "model": "qwen2.5:3b",
        "format": "json",
        "stream": False,
        "keep_alive": -1,  # Keep model persistently loaded in VRAM/RAM between requests
        "options": {
            "temperature": 0.0,
            "top_p": 0.9,
            "num_predict": 256  # Compact generation limit to prevent runaway generation
        },
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": clean_text}
        ]
    }

    try:
        res = _SESSION.post(f"{ollama_url}/api/chat", json=payload, timeout=90)
        if res.status_code != 200:
            return False, None, None, f"Ollama HTTP error {res.status_code}: {res.text}"
        
        content = res.json().get("message", {}).get("content", "")
        intent_data = extract_json(content)
        
        ok, validated_or_err = validate_intent(intent_data)
        if not ok:
            return False, intent_data, None, f"Intent validation failed: {validated_or_err}"
        
        il_code = intent_to_il(validated_or_err)
        structured_res = {"instructions": validated_or_err}
        
        # Save to cache
        _QUERY_CACHE[clean_text] = structured_res
        
        return True, structured_res, il_code, None

    except requests.exceptions.ConnectionError:
        return False, None, None, "Could not connect to Ollama. Make sure 'ollama serve' is running."
    except json.JSONDecodeError as jde:
        return False, None, None, f"Failed to parse model response as JSON: {jde}"
    except Exception as e:
        return False, None, None, f"Interpretation error: {str(e)}"