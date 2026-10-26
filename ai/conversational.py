import json
import re
import time
from copy import deepcopy
from pathlib import Path
import requests

from ai.validator import validate_intent, intent_to_il
from compiler.runner import run_compiler_pipeline
from ai.explainer import explain_c_code

# Global in-memory storage of conversational programming sessions
_CONVERSATION_SESSIONS = {}

class ConversationSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history = []  # List of {"role": "user"|"assistant", "text": str, "timestamp": float, "diff": str, "success": bool}
        self.current_intent = None  # {"instructions": [...]}
        self.current_il = ""
        self.current_c_code = ""
        self.current_compiler_log = ""
        self.history_stack = []  # Snapshots for multi-level Undo

    def push_snapshot(self):
        """Saves a snapshot of current accepted state for Undo."""
        if self.current_intent:
            snapshot = {
                "intent": deepcopy(self.current_intent),
                "il": self.current_il,
                "c_code": self.current_c_code,
                "compiler_log": self.current_compiler_log,
                "history_len": len(self.history)
            }
            self.history_stack.append(snapshot)
            # Limit history stack depth
            if len(self.history_stack) > 20:
                self.history_stack.pop(0)

    def undo(self):
        """Reverts to the most recent previous accepted state."""
        if not self.history_stack:
            return False, "No previous state to undo to."
        
        prev = self.history_stack.pop()
        self.current_intent = prev["intent"]
        self.current_il = prev["il"]
        self.current_c_code = prev["c_code"]
        self.current_compiler_log = prev["compiler_log"]
        # Trim history to previous length
        target_len = prev.get("history_len", len(self.history))
        self.history = self.history[:target_len]
        
        self.history.append({
            "role": "assistant",
            "text": "Reverted program to previous accepted version.",
            "timestamp": time.time(),
            "diff": "Undo last change",
            "success": True
        })
        if self.current_il:
            try:
                run_compiler_pipeline(self.current_il, session_id=self.session_id)
            except Exception:
                pass
        return True, "Successfully reverted to previous program version."

def get_conversation_session(session_id: str) -> ConversationSession:
    if session_id not in _CONVERSATION_SESSIONS:
        _CONVERSATION_SESSIONS[session_id] = ConversationSession(session_id)
    return _CONVERSATION_SESSIONS[session_id]

def init_or_update_session(session_id: str, prompt: str, intent_data: dict, il_code: str, c_code: str, compiler_log: str):
    """Initializes or updates the accepted session state after initial compilation."""
    session = get_conversation_session(session_id)
    session.push_snapshot()
    session.current_intent = deepcopy(intent_data)
    session.current_il = il_code
    session.current_c_code = c_code
    session.current_compiler_log = compiler_log
    
    # Add initial user turn if history is empty
    if not session.history:
        session.history.append({
            "role": "user",
            "text": prompt,
            "timestamp": time.time(),
            "diff": "Initial Program",
            "success": True
        })
        session.history.append({
            "role": "assistant",
            "text": "Initial program synthesized and compiled successfully.",
            "timestamp": time.time(),
            "diff": "Created program structure",
            "success": True
        })
    return session

def reset_conversation_session(session_id: str) -> dict:
    """Completely resets conversation state for a new program."""
    if session_id in _CONVERSATION_SESSIONS:
        del _CONVERSATION_SESSIONS[session_id]
    return {
        "success": True,
        "message": "Conversation session reset. Ready for a new program.",
        "history": [],
        "c_code": "",
        "il_code": ""
    }

def undo_last_update(session_id: str) -> dict:
    """Restores the previous program version from history stack."""
    session = get_conversation_session(session_id)
    ok, msg = session.undo()
    if not ok:
        return {
            "success": False,
            "error": msg,
            "history": session.history
        }
    return {
        "success": True,
        "message": msg,
        "c_code": session.current_c_code,
        "il_code": session.current_il,
        "intent": session.current_intent,
        "compiler_log": session.current_compiler_log,
        "history": session.history
    }

# ==============================================================================
# DETERMINISTIC SEMANTIC TRANSFORMATION ENGINE
def _insert_in_body(current_instructions: list, new_items: list, is_condition: bool = False) -> list:
    """
    Inserts new_items at a structurally valid position in the instruction list.
    If the program is wrapped in a loop (ends with end_for or end_while),
    the new items are inserted INSIDE the loop (before end_for/end_while)
    so that variables scoped inside the loop remain valid and in-scope in C.
    """
    updated = deepcopy(current_instructions)
    if not updated:
        return new_items

    # If the program is enclosed in a loop (ends with end_for or end_while)
    if updated[-1].get("action") in ("end_for", "end_while"):
        idx = len(updated) - 1  # Position of end_for / end_while
        if is_condition:
            for offset, item in enumerate(new_items):
                updated.insert(idx + offset, item)
            return updated
        else:
            # Arithmetic computation: if there is an if block right before end_for, insert before the if block
            if idx > 0 and updated[idx - 1].get("action") == "end_if":
                depth = 0
                insert_pos = idx - 1
                for j in range(idx - 1, -1, -1):
                    if updated[j].get("action") == "end_if":
                        depth += 1
                    elif updated[j].get("action") == "if":
                        depth -= 1
                        if depth == 0:
                            insert_pos = j
                            break
                for offset, item in enumerate(new_items):
                    updated.insert(insert_pos + offset, item)
                return updated
            else:
                for offset, item in enumerate(new_items):
                    updated.insert(idx + offset, item)
                return updated

    # If not enclosed in a loop, but ends with an if block, and we are adding arithmetic
    if not is_condition and updated[-1].get("action") == "end_if":
        depth = 0
        insert_pos = len(updated) - 1
        for j in range(len(updated) - 1, -1, -1):
            if updated[j].get("action") == "end_if":
                depth += 1
            elif updated[j].get("action") == "if":
                depth -= 1
                if depth == 0:
                    insert_pos = j
                    break
        for offset, item in enumerate(new_items):
            updated.insert(insert_pos + offset, item)
        return updated

    # Default: append at the end
    updated.extend(new_items)
    return updated

def analyze_deterministic_update(current_instructions: list, user_text: str):
    """
    Analyzes follow-up natural language instructions against the current structured intent.
    Handles additions, removals, renamings, conditions, loops, clarfications, and unsupporteds.
    Returns dict:
      {"action": "update", "instructions": [...], "explanation": "..."}
      {"action": "clarify", "message": "..."}
      {"action": "unsupported", "message": "..."}
      {"action": "explain"}
      {"action": "undo"}
      {"action": "new_program"}
      or None if general language needs LLM interpretation.
    """
    text = user_text.strip()
    
    # 1. Undo / Revert
    if re.search(r'^\s*(?:undo|revert|go back|undo last change)\b', text, re.I):
        return {"action": "undo"}
        
    # 2. Reset / New Program
    if re.search(r'^\s*(?:start.*(?:completely.*)?new program|start over|reset(?: conversation)?|clear program)\b', text, re.I):
        return {"action": "new_program"}
        
    # 3. Explain Current Program
    if re.search(r'^\s*(?:explain(?: the)?(?: current)? program|what does this (?:code|program) do|describe program)\b', text, re.I):
        return {"action": "explain"}
        
    # 4. Unsupported requests check (databases, network, graphics, threading, OOP)
    if re.search(r'\b(?:database|sql|postgres|mysql|mongo|sqlite|socket|network|http|api|gui|window|graphics|canvas|thread|multiprocessing|class|object|import numpy|import pandas)\b', text, re.I):
        return {
            "action": "unsupported",
            "message": "The NLP Compiler target is a minimal deterministic C subset supporting arithmetic, variables, if/else branching, and loops. External libraries, databases, networking, and OOP are not supported."
        }

    # 5. Clarify Ambiguous Instructions (e.g. "make it faster", "do something", "improve it")
    if re.search(r'^\s*(?:make it (?:faster|better|cleaner)|optimize(?: it)?|improve(?: it)?|do something(?: else)?|fix it|change it|update it)\s*[\.\!\?]*$', text, re.I):
        return {
            "action": "clarify",
            "message": "Your instruction is ambiguous. Please clarify what specific calculation, variable, condition, or loop you would like to add, change, or remove."
        }

    # Extract input variables currently present in the program
    input_vars = []
    for it in current_instructions:
        if it.get("action") == "read" and it.get("name"):
            if it["name"] not in input_vars:
                input_vars.append(it["name"])

    # Fallback to declared variables if no reads
    if not input_vars:
        for it in current_instructions:
            if it.get("action") == "declare" and it.get("name"):
                if it["name"] not in input_vars:
                    input_vars.append(it["name"])

    # Primary operands for arithmetic (e.g. num1, num2)
    op1 = input_vars[0] if len(input_vars) > 0 else "num1"
    op2 = input_vars[1] if len(input_vars) > 1 else (input_vars[0] if input_vars else "num2")

    # 6. Rename Variable: "change the variable name to total", "rename sum to total", "rename 'result' to 'sum'"
    clean_text = re.sub(r'[\.\!\?]+$', '', text).strip()
    m_to_only = (
        re.search(r'^(?:change\s+(?:the\s+)?variable(?:\s+name)?|rename(?:\s+the\s+variable)?)\s+to\s+["\']?([a-zA-Z_]\w*)["\']?$', clean_text, re.I) or
        re.search(r'^rename\s+to\s+["\']?([a-zA-Z_]\w*)["\']?$', clean_text, re.I) or
        re.search(r'^change\s+to\s+["\']?([a-zA-Z_]\w*)["\']?$', clean_text, re.I)
    )
    m_both = (
        re.search(r'(?:change\s+(?:the\s+)?variable(?:\s+name)?\s+(?:from\s+)?["\']?([a-zA-Z_]\w*)["\']?\s+to\s+["\']?([a-zA-Z_]\w*)["\']?)', clean_text, re.I) or
        re.search(r'rename\s+["\']?([a-zA-Z_]\w*)["\']?\s+to\s+["\']?([a-zA-Z_]\w*)["\']?', clean_text, re.I)
    )

    if m_to_only or m_both:
        if m_to_only:
            old_var = None
            new_var = m_to_only.group(1)
        else:
            old_var = m_both.group(1)
            new_var = m_both.group(2)

        # Collect all declared variables in the program
        all_declared_vars = []
        for it in current_instructions:
            name = it.get("name")
            if it.get("action") == "declare" and name and name not in all_declared_vars:
                all_declared_vars.append(name)

        # Check all assigned or declared non-input variables
        assigned_vars = []
        for it in current_instructions:
            name = it.get("name")
            if it.get("action") in ("assign", "declare") and name and name not in input_vars:
                if name not in assigned_vars:
                    assigned_vars.append(name)

        # If old_var was specified, check if it exists in the program
        if old_var and old_var not in all_declared_vars:
            # If user said e.g. "result" or "res", but the actual variable in the program is "sum"
            if old_var.lower() in ("result", "res", "ans", "answer", "output"):
                if assigned_vars:
                    old_var = assigned_vars[0]

        if not old_var:
            # If renaming to 'total', prioritize variable assigned from addition, or named 'sum'
            if "total" in new_var.lower():
                for it in current_instructions:
                    if it.get("action") == "assign" and "+" in it.get("value", ""):
                        old_var = it.get("name")
                        break
                if not old_var and "sum" in assigned_vars:
                    old_var = "sum"

            # Fallback to first non-input variable
            if not old_var and assigned_vars:
                old_var = assigned_vars[0]
            if not old_var and len(input_vars) > 0:
                old_var = input_vars[-1]

        if old_var and new_var:
            if old_var == new_var:
                return {
                    "action": "update",
                    "instructions": [deepcopy(it) for it in current_instructions],
                    "explanation": f"Variable is already named '{new_var}'."
                }
            updated = []
            for item in current_instructions:
                it = deepcopy(item)
                if it.get("name") == old_var:
                    it["name"] = new_var
                if it.get("variable") == old_var:
                    it["variable"] = new_var
                if it.get("value") == old_var:
                    it["value"] = new_var
                elif "value" in it and isinstance(it["value"], str):
                    it["value"] = re.sub(rf'\b{re.escape(old_var)}\b', new_var, it["value"])
                if "condition" in it and isinstance(it["condition"], str):
                    it["condition"] = re.sub(rf'\b{re.escape(old_var)}\b', new_var, it["condition"])
                updated.append(it)
            return {
                "action": "update",
                "instructions": updated,
                "explanation": f"Renamed variable '{old_var}' to '{new_var}' across all definitions and expressions."
            }

    is_remove = bool(re.search(r'\b(?:remove|delete|drop|eliminate|cancel|clear|without)\b', text, re.I))

    # 7. Remove Operation: "remove the multiplication operation", "delete subtraction"
    m_remove = re.search(r'(?:remove|delete|drop|eliminate|cancel|clear).*(multiplication|subtraction|addition|division|product|difference|sum|quotient|diff|prod|total)', text, re.I)
    if m_remove:
        kw = m_remove.group(1).lower()
        symbol_map = {
            "multiplication": "*", "product": "*", "prod": "*",
            "subtraction": "-", "difference": "-", "diff": "-",
            "addition": "+", "sum": "+", "total": "+",
            "division": "/", "quotient": "/", "quot": "/"
        }
        var_patterns = {
            "multiplication": ["prod", "product", "mult"],
            "subtraction": ["diff", "difference"],
            "addition": ["sum", "total", "add"],
            "division": ["quot", "quotient", "div"]
        }
        sym = symbol_map.get(kw)
        cand_vars = var_patterns.get(kw, [kw])
        
        # Identify variables to remove
        vars_to_remove = set(cand_vars)
        for it in current_instructions:
            if it.get("action") == "assign" and sym and sym in it.get("value", ""):
                vars_to_remove.add(it.get("name"))

        # Identify remaining valid result variable to re-target any conditions
        remaining_assign_vars = [
            it.get("name") for it in current_instructions
            if it.get("action") == "assign" and it.get("name") not in vars_to_remove and it.get("name") not in input_vars
        ]
        fallback_res = remaining_assign_vars[0] if remaining_assign_vars else (input_vars[0] if input_vars else "total")

        updated = []
        for it in current_instructions:
            if it.get("name") in vars_to_remove or it.get("value") in vars_to_remove or (sym and sym in it.get("value", "")):
                continue
            item = deepcopy(it)
            if "condition" in item and isinstance(item["condition"], str):
                for v in vars_to_remove:
                    if re.search(rf'\b{re.escape(v)}\b', item["condition"]):
                        item["condition"] = re.sub(rf'\b{re.escape(v)}\b', fallback_res, item["condition"])
            updated.append(item)

        return {
            "action": "update",
            "instructions": updated,
            "explanation": f"Removed {kw} operation and its associated output."
        }

    # 8. Add Subtraction / Difference: "also print their difference", "also subtract", "subtract them", "print difference"
    if not is_remove and re.search(r'(?:(?:also|now|and)?.*(?:print|calculate|find|get|show)?.*difference|(?:also|now|and)?.*subtract|minus them|add subtraction)', text, re.I):
        target = "diff"
        existing_names = {it.get("name") for it in current_instructions}
        if target in existing_names:
            target = "difference"
        new_items = [
            {"action": "declare", "type": "INT", "name": target},
            {"action": "assign", "name": target, "value": f"{op1} - {op2}"},
            {"action": "print", "value": target}
        ]
        updated = _insert_in_body(current_instructions, new_items, is_condition=False)
        return {
            "action": "update",
            "instructions": updated,
            "explanation": f"Added subtraction operation: {target} = {op1} - {op2} and output."
        }

    # 9. Add Multiplication / Product: "also multiply the numbers", "multiply them", "print product"
    if not is_remove and re.search(r'(?:(?:also|now|and)?.*(?:print|calculate|find|get|show)?.*(?:product|multiplication)|(?:also|now|and)?.*multiply|times them|add multiplication)', text, re.I):
        target = "prod"
        existing_names = {it.get("name") for it in current_instructions}
        if target in existing_names:
            target = "product"
        new_items = [
            {"action": "declare", "type": "INT", "name": target},
            {"action": "assign", "name": target, "value": f"{op1} * {op2}"},
            {"action": "print", "value": target}
        ]
        updated = _insert_in_body(current_instructions, new_items, is_condition=False)
        return {
            "action": "update",
            "instructions": updated,
            "explanation": f"Added multiplication operation: {target} = {op1} * {op2} and output."
        }

    # 10. Add Division / Quotient: "also divide the numbers", "divide them", "print quotient"
    if not is_remove and re.search(r'(?:(?:also|now|and)?.*(?:print|calculate|find|get|show)?.*(?:quotient|division)|(?:also|now|and)?.*divide|add division)', text, re.I):
        target = "quot"
        existing_names = {it.get("name") for it in current_instructions}
        if target in existing_names:
            target = "quotient"
        new_items = [
            {"action": "declare", "type": "INT", "name": target},
            {"action": "assign", "name": target, "value": f"{op1} / {op2}"},
            {"action": "print", "value": target}
        ]
        updated = _insert_in_body(current_instructions, new_items, is_condition=False)
        return {
            "action": "update",
            "instructions": updated,
            "explanation": f"Added division operation: {target} = {op1} / {op2} and output."
        }

    # 11. Add Modulo / Remainder: "also calculate remainder", "find modulo"
    if not is_remove and re.search(r'(?:(?:also|now|and)?.*(?:print|calculate|find|get|show)?.*(?:remainder|modulo)|remainder of them|mod them)', text, re.I):
        target = "rem"
        existing_names = {it.get("name") for it in current_instructions}
        if target in existing_names:
            target = "remainder"
        new_items = [
            {"action": "declare", "type": "INT", "name": target},
            {"action": "assign", "name": target, "value": f"{op1} % {op2}"},
            {"action": "print", "value": target}
        ]
        updated = _insert_in_body(current_instructions, new_items, is_condition=False)
        return {
            "action": "update",
            "instructions": updated,
            "explanation": f"Added modulo operation: {target} = {op1} % {op2} and output."
        }

    # 12. Add Condition: "add a condition to check whether the result is positive"
    if not is_remove and re.search(r'(?:(?:check|add.*condition|verify|test).*(?:positive|greater than 0)|if.*(?:positive|greater than 0))', text, re.I):
        # Find result variable
        all_assigned = [it.get("name") for it in current_instructions if it.get("action") == "assign" and it.get("name") not in input_vars]
        if "total" in all_assigned:
            res_var = "total"
        elif "sum" in all_assigned:
            res_var = "sum"
        elif all_assigned:
            res_var = all_assigned[0]
        else:
            res_var = "res"

        new_items = [
            {"action": "if", "condition": f"{res_var} > 0"},
            {"action": "print", "value": "1"},
            {"action": "else"},
            {"action": "print", "value": "0"},
            {"action": "end_if"}
        ]
        updated = _insert_in_body(current_instructions, new_items, is_condition=True)
        return {
            "action": "update",
            "instructions": updated,
            "explanation": f"Added condition: if {res_var} > 0 print 1 else print 0."
        }

    # 13. Add Loop: "use a loop to repeat the input process three times", "loop 3 times"
    WORD_TO_NUM = {
        "once": "1", "one": "1",
        "twice": "2", "two": "2",
        "three": "3", "thrice": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10"
    }
    m_loop = re.search(r'(?:(?:repeat|loop|run|iterate).*\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|twice|thrice)\s*(?:times)?|for.*from\s*1\s*to\s*(\d+))', text, re.I)
    if m_loop:
        raw_val = [g for g in m_loop.groups() if g][0].lower()
        times = WORD_TO_NUM.get(raw_val, raw_val)
        updated = []
        existing_vars = {it.get("name") for it in current_instructions if it.get("name")}
        loop_var = "i"
        for cand in ["i", "j", "k", "idx", "iter"]:
            if cand not in existing_vars:
                loop_var = cand
                break
        updated.append({"action": "declare", "type": "INT", "name": loop_var})
        updated.append({"action": "for", "variable": loop_var, "start": "1", "end": str(times)})
        for it in current_instructions:
            updated.append(deepcopy(it))
        updated.append({"action": "end_for"})
        return {
            "action": "update",
            "instructions": updated,
            "explanation": f"Wrapped program process in a for loop running {times} iterations."
        }

    return None

# ==============================================================================
# MAIN CONVERSATIONAL PROCESSOR
# ==============================================================================

def process_conversational_update(session_id: str, followup_text: str, ollama_url: str = "http://127.0.0.1:11434") -> dict:
    """
    Main entry point for Conversational Programming updates.
    Maintains separate current and candidate states.
    Preserves existing program context if update fails.
    """
    session = get_conversation_session(session_id)
    text = followup_text.strip()
    
    if not text:
        return {
            "success": False,
            "status": "error",
            "error": "Follow-up instruction cannot be empty.",
            "history": session.history
        }

    if not session.current_intent or not session.current_intent.get("instructions"):
        return {
            "success": False,
            "status": "error",
            "error": "No active program found in this conversation session. Please compile an initial natural language program first.",
            "history": session.history
        }

    # Check deterministic shortcuts first (instant ~0.1ms)
    det_res = analyze_deterministic_update(session.current_intent.get("instructions", []), text)
    
    if det_res:
        action = det_res.get("action")
        
        if action == "undo":
            return undo_last_update(session_id)
            
        elif action == "new_program":
            return reset_conversation_session(session_id)
            
        elif action == "explain":
            ok, explanation, err = explain_c_code(session.current_c_code, language="english")
            resp_text = explanation if ok else (err or "Explanation unavailable.")
            session.history.append({"role": "user", "text": text, "timestamp": time.time(), "diff": "Explain Request", "success": True})
            session.history.append({"role": "assistant", "text": resp_text, "timestamp": time.time(), "diff": "Code Explanation", "success": True})
            return {
                "success": True,
                "status": "explanation",
                "explanation": resp_text,
                "c_code": session.current_c_code,
                "il_code": session.current_il,
                "intent": session.current_intent,
                "history": session.history
            }
            
        elif action == "clarify":
            clarify_msg = det_res.get("message")
            session.history.append({"role": "user", "text": text, "timestamp": time.time(), "diff": "Clarification Request", "success": False})
            session.history.append({"role": "assistant", "text": clarify_msg, "timestamp": time.time(), "diff": "Clarification", "success": False})
            return {
                "success": False,
                "status": "clarification",
                "message": clarify_msg,
                "c_code": session.current_c_code,
                "il_code": session.current_il,
                "intent": session.current_intent,
                "history": session.history
            }
            
        elif action == "unsupported":
            unsupported_msg = det_res.get("message")
            session.history.append({"role": "user", "text": text, "timestamp": time.time(), "diff": "Unsupported Feature", "success": False})
            session.history.append({"role": "assistant", "text": unsupported_msg, "timestamp": time.time(), "diff": "Unsupported", "success": False})
            return {
                "success": False,
                "status": "unsupported",
                "error": unsupported_msg,
                "c_code": session.current_c_code,
                "il_code": session.current_il,
                "intent": session.current_intent,
                "history": session.history
            }
            
        elif action == "update":
            candidate_instructions = det_res.get("instructions", [])
            explanation = det_res.get("explanation", "Program updated.")
            return _commit_candidate_update(session, text, candidate_instructions, explanation)

    # Fallback to local Qwen 2.5 3B with conversational update prompt
    try:
        current_intent_json = json.dumps(session.current_intent, indent=2)
        system_prompt = (
            "You are the Conversational Program Modifier for the NLP Compiler.\n"
            "The user wants to update an existing C-target program.\n\n"
            f"Current Program Structured Intent:\n{current_intent_json}\n\n"
            "Rules:\n"
            "1. Preserve all existing variables, reads, and computations unless the user explicitly asks to remove or change them.\n"
            "2. Output ONLY a JSON object with keys:\n"
            '   "action_type": "update" | "clarify" | "unsupported"\n'
            '   "explanation": "<short summary of change>"\n'
            '   "instructions": [<complete updated list of instructions using schema>]\n'
            "3. Allowed actions: declare, read, assign, print, if, else, end_if, while, end_while, for, end_for.\n"
            "4. If ambiguous, set action_type to 'clarify'. If unsupported, set action_type to 'unsupported'.\n"
            "5. Pure valid JSON only."
        )

        payload = {
            "model": "qwen2.5:3b",
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 256
            },
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        }

        res = requests.post(f"{ollama_url}/api/chat", json=payload, timeout=45)
        if res.status_code == 200:
            content = res.json().get("message", {}).get("content", "")
            data = json.loads(content)
            action_type = data.get("action_type", "update")
            explanation = data.get("explanation", "Updated program intent.")
            
            if action_type == "clarify":
                return {
                    "success": False,
                    "status": "clarification",
                    "message": explanation or "Could you clarify what you would like to modify in the program?",
                    "history": session.history
                }
            elif action_type == "unsupported":
                return {
                    "success": False,
                    "status": "unsupported",
                    "error": explanation or "This operation is not supported by the compiler.",
                    "history": session.history
                }
            elif action_type == "update":
                candidate_instructions = data.get("instructions", [])
                return _commit_candidate_update(session, text, candidate_instructions, explanation)

    except Exception as e:
        # Graceful fallback: report error without corrupting state
        pass

    return {
        "success": False,
        "status": "error",
        "error": f"Could not interpret modification '{text}'. Try phrasing as e.g. 'Also print their difference', 'Change the variable name to total', or 'Remove subtraction'.",
        "c_code": session.current_c_code,
        "il_code": session.current_il,
        "intent": session.current_intent,
        "history": session.history
    }

def _commit_candidate_update(session: ConversationSession, user_text: str, candidate_instructions: list, explanation: str) -> dict:
    """
    Validates and deterministically compiles the candidate instructions.
    If valid and compilation succeeds: commits to session state with undo snapshot.
    If fails: discards candidate and preserves existing program.
    """
    # Step 1: Validate candidate intent
    ok, validated_or_err = validate_intent({"instructions": candidate_instructions})
    if not ok:
        session.history.append({
            "role": "user",
            "text": user_text,
            "timestamp": time.time(),
            "diff": "Failed Update",
            "success": False
        })
        session.history.append({
            "role": "assistant",
            "text": f"Update rejected by intent validator: {validated_or_err}. Original program preserved.",
            "timestamp": time.time(),
            "diff": "Validation Error",
            "success": False
        })
        return {
            "success": False,
            "status": "validation_error",
            "error": f"Intent validation failed: {validated_or_err}. Original program was preserved.",
            "c_code": session.current_c_code,
            "il_code": session.current_il,
            "intent": session.current_intent,
            "history": session.history
        }

    # Step 2: Convert to IL
    candidate_il = intent_to_il(validated_or_err)

    # Step 3: Run Deterministic Compiler Pipeline on Candidate
    candidate_sess = f"{session.session_id}_update"
    comp_res = run_compiler_pipeline(candidate_il, session_id=candidate_sess)

    if not comp_res.get("success"):
        err_msg = comp_res.get("error", "Deterministic compilation failed.")
        session.history.append({
            "role": "user",
            "text": user_text,
            "timestamp": time.time(),
            "diff": "Compile Failure",
            "success": False
        })
        session.history.append({
            "role": "assistant",
            "text": f"Update rejected by compiler: {err_msg}. Original program preserved.",
            "timestamp": time.time(),
            "diff": "Compiler Error",
            "success": False
        })
        return {
            "success": False,
            "status": "compile_error",
            "error": f"Compilation failed: {err_msg}. Original program was preserved.",
            "compiler_log": comp_res.get("compiler_log", ""),
            "c_code": session.current_c_code,
            "il_code": session.current_il,
            "intent": session.current_intent,
            "history": session.history
        }

    # Step 4: SUCCESS! Save snapshot to history stack for Undo, then commit
    session.push_snapshot()
    session.current_intent = {"instructions": validated_or_err}
    session.current_il = candidate_il
    session.current_c_code = comp_res.get("c_code", "")
    session.current_compiler_log = comp_res.get("compiler_log", "")

    # Synchronize candidate files to active session files
    base_output = Path(__file__).parent.parent / "output"
    try:
        import shutil
        cand_exe = base_output / f"{candidate_sess}_program.exe"
        active_exe = base_output / f"{session.session_id}_program.exe"
        if cand_exe.exists():
            shutil.copyfile(cand_exe, active_exe)
        cand_c = base_output / f"{candidate_sess}_generated.c"
        active_c = base_output / f"{session.session_id}_generated.c"
        if cand_c.exists():
            shutil.copyfile(cand_c, active_c)
        cand_il = base_output / f"{candidate_sess}_input.il"
        active_il = base_output / f"{session.session_id}_input.il"
        if cand_il.exists():
            shutil.copyfile(cand_il, active_il)
    except Exception:
        pass

    # Unconditionally run compiler pipeline on the active session ID so GCC builds the active binary directly
    try:
        run_compiler_pipeline(candidate_il, session_id=session.session_id)
    except Exception:
        pass

    session.history.append({
        "role": "user",
        "text": user_text,
        "timestamp": time.time(),
        "diff": explanation,
        "success": True
    })
    session.history.append({
        "role": "assistant",
        "text": f"{explanation} Compiled successfully.",
        "timestamp": time.time(),
        "diff": explanation,
        "success": True
    })

    return {
        "success": True,
        "status": "success",
        "session_id": session.session_id,
        "explanation": explanation,
        "c_code": session.current_c_code,
        "il_code": session.current_il,
        "intent": session.current_intent,
        "compiler_log": session.current_compiler_log,
        "history": session.history,
        "can_undo": len(session.history_stack) > 0
    }
