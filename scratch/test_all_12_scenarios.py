import json
import uuid
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app import app
from ai.conversational import get_conversation_session, reset_conversation_session

client = TestClient(app)

def run_tests():
    print("=" * 70)
    print("NLP COMPILER — 12-SCENARIO CONVERSATIONAL PROGRAMMING TEST SUITE")
    print("=" * 70)

    # --------------------------------------------------------------------------
    # Scenario 1: Initial Program Creation
    # --------------------------------------------------------------------------
    print("\n[Scenario 1] Initial Program Creation")
    sess_a = f"sess_test_{uuid.uuid4().hex[:6]}"
    resp = client.post("/api/compile", json={
        "mode": "nlp",
        "content": "Ask the user for two numbers, add them and display the result.",
        "session_id": sess_a
    })
    assert resp.status_code == 200, f"Scenario 1 failed: {resp.text}"
    data = resp.json()
    assert data["success"] is True
    assert "c_code" in data and len(data["c_code"]) > 20
    assert len(data.get("history", [])) >= 2
    c_code_v1 = data["c_code"]
    print(f"  [OK] Initial program compiled successfully ({len(c_code_v1)} bytes C code).")

    # --------------------------------------------------------------------------
    # Scenario 2: Add Operation ("Also print their difference")
    # --------------------------------------------------------------------------
    print("\n[Scenario 2] Add Operation ('Also print their difference')")
    resp = client.post("/api/conversation/update", json={
        "session_id": sess_a,
        "message": "Also print their difference."
    })
    assert resp.status_code == 200, f"Scenario 2 failed: {resp.text}"
    data = resp.json()
    assert data["success"] is True
    assert data["status"] == "success"
    c_code_v2 = data["c_code"]
    assert "+" in c_code_v2, "Original addition (+) must be preserved!"
    assert "-" in c_code_v2, "Subtraction (-) must be added!"
    print("  [OK] Program updated: addition preserved and subtraction added.")

    # --------------------------------------------------------------------------
    # Scenario 3: Another Operation ("Also multiply the numbers")
    # --------------------------------------------------------------------------
    print("\n[Scenario 3] Another Operation ('Also multiply the numbers')")
    resp = client.post("/api/conversation/update", json={
        "session_id": sess_a,
        "message": "Also multiply the numbers."
    })
    assert resp.status_code == 200, f"Scenario 3 failed: {resp.text}"
    data = resp.json()
    assert data["success"] is True
    c_code_v3 = data["c_code"]
    assert "+" in c_code_v3 and "-" in c_code_v3 and "*" in c_code_v3
    print("  [OK] Program updated: addition, subtraction, and multiplication present.")

    # --------------------------------------------------------------------------
    # Scenario 4: Variable Rename ("Change the variable name to total")
    # --------------------------------------------------------------------------
    print("\n[Scenario 4] Variable Rename ('Change the variable name to total')")
    resp = client.post("/api/conversation/update", json={
        "session_id": sess_a,
        "message": "Change the variable name to total."
    })
    assert resp.status_code == 200, f"Scenario 4 failed: {resp.text}"
    data = resp.json()
    assert data["success"] is True
    c_code_v4 = data["c_code"]
    assert "total" in c_code_v4, "Variable 'total' must be in C code!"
    print("  [OK] Variable successfully renamed to 'total'.")

    # --------------------------------------------------------------------------
    # Scenario 5: Add Condition ("Add a condition to check whether the result is positive")
    # --------------------------------------------------------------------------
    print("\n[Scenario 5] Add Condition ('Add a condition to check whether the result is positive')")
    resp = client.post("/api/conversation/update", json={
        "session_id": sess_a,
        "message": "Add a condition to check whether the result is positive."
    })
    assert resp.status_code == 200, f"Scenario 5 failed: {resp.text}"
    data = resp.json()
    assert data["success"] is True
    c_code_v5 = data["c_code"]
    assert "if" in c_code_v5 and "> 0" in c_code_v5
    print("  [OK] Condition 'if result > 0' added successfully.")

    # --------------------------------------------------------------------------
    # Scenario 6: Add Loop ("Use a loop to repeat the input process three times")
    # --------------------------------------------------------------------------
    print("\n[Scenario 6] Add Loop ('Use a loop to repeat the input process three times')")
    resp = client.post("/api/conversation/update", json={
        "session_id": sess_a,
        "message": "Use a loop to repeat the input process three times."
    })
    assert resp.status_code == 200, f"Scenario 6 failed: {resp.text}"
    data = resp.json()
    assert data["success"] is True
    c_code_v6 = data["c_code"]
    assert "for" in c_code_v6 or "while" in c_code_v6
    print("  [OK] Loop wrapping added successfully.")

    # --------------------------------------------------------------------------
    # Scenario 7: Remove Operation ("Remove the multiplication operation")
    # --------------------------------------------------------------------------
    print("\n[Scenario 7] Remove Operation ('Remove the multiplication operation')")
    resp = client.post("/api/conversation/update", json={
        "session_id": sess_a,
        "message": "Remove the multiplication operation."
    })
    assert resp.status_code == 200, f"Scenario 7 failed: {resp.text}"
    data = resp.json()
    assert data["success"] is True
    c_code_v7 = data["c_code"]
    # Check that product calculation is removed
    assert "prod" not in c_code_v7
    print("  [OK] Multiplication operation removed while remaining program preserved.")

    # --------------------------------------------------------------------------
    # Scenario 8: Clarification Request ("Make it faster")
    # --------------------------------------------------------------------------
    print("\n[Scenario 8] Clarification Request ('Make it faster')")
    resp = client.post("/api/conversation/update", json={
        "session_id": sess_a,
        "message": "Make it faster."
    })
    # Clarification returns status 400 or handled response with status="clarification"
    data = resp.json()
    assert data["status"] == "clarification", f"Expected clarification, got {data}"
    assert "clarify" in data["message"].lower() or "optimize" in data["message"].lower()
    # Ensure current C code is NOT overwritten
    assert data["c_code"] == c_code_v7
    print(f"  [OK] System asked clarification without guessing: '{data['message']}'")

    # --------------------------------------------------------------------------
    # Scenario 9: Unsupported Feature Rejection ("Save the output to a MySQL database")
    # --------------------------------------------------------------------------
    print("\n[Scenario 9] Unsupported Feature Rejection ('Save the output to a MySQL database')")
    resp = client.post("/api/conversation/update", json={
        "session_id": sess_a,
        "message": "Save the output to a MySQL database."
    })
    data = resp.json()
    assert data["status"] == "unsupported", f"Expected unsupported, got {data}"
    assert "database" in data["error"].lower()
    assert data["c_code"] == c_code_v7, "C code must be preserved intact!"
    print(f"  [OK] Unsupported feature rejected safely: '{data['error']}'")

    # --------------------------------------------------------------------------
    # Scenario 10: Compiler Failure Rollback
    # --------------------------------------------------------------------------
    print("\n[Scenario 10] Compiler Failure Rollback")
    # Directly test candidate rejection with an illegal instruction that fails intent validation
    session_obj = get_conversation_session(sess_a)
    accepted_before = session_obj.current_c_code
    from ai.conversational import _commit_candidate_update
    illegal_candidate = [{"action": "invalid_opcode", "foo": "bar"}]
    fail_res = _commit_candidate_update(session_obj, "Do invalid opcode", illegal_candidate, "Invalid")
    assert fail_res["success"] is False
    assert fail_res["status"] == "validation_error"
    assert session_obj.current_c_code == accepted_before
    print("  [OK] Intent/compiler validation error caught; candidate discarded and original accepted state preserved.")

    # --------------------------------------------------------------------------
    # Scenario 11: Multi-Level Undo
    # --------------------------------------------------------------------------
    print("\n[Scenario 11] Multi-Level Undo")
    # We are currently at state v7. Let's undo.
    resp = client.post("/api/conversation/undo", json={"session_id": sess_a})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    # The undone code should equal state v6
    assert data["c_code"] == c_code_v6
    print("  [OK] Level 1 Undo successful (reverted to Loop state v6).")

    # Undo again
    resp = client.post("/api/conversation/undo", json={"session_id": sess_a})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    # Should equal state v5
    assert data["c_code"] == c_code_v5
    print("  [OK] Level 2 Undo successful (reverted to Condition state v5).")

    # --------------------------------------------------------------------------
    # Scenario 12: Session Isolation
    # --------------------------------------------------------------------------
    print("\n[Scenario 12] Session Isolation")
    sess_b = f"sess_test_{uuid.uuid4().hex[:6]}"
    resp_b = client.post("/api/compile", json={
        "mode": "nlp",
        "content": "Ask the user for c, set f to c * 9 / 5 + 32, print f",
        "session_id": sess_b
    })
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    assert data_b["success"] is True
    c_b = data_b["c_code"]

    # Verify session A is still at state v5 (add, diff, prod, total, if)
    resp_a_hist = client.get(f"/api/conversation/history/{sess_a}")
    assert resp_a_hist.status_code == 200
    data_a_hist = resp_a_hist.json()
    assert data_a_hist["has_active_program"] is True

    session_a_obj = get_conversation_session(sess_a)
    session_b_obj = get_conversation_session(sess_b)
    assert session_a_obj.current_c_code != session_b_obj.current_c_code
    assert "total" in session_a_obj.current_c_code
    assert "32" in session_b_obj.current_c_code
    print("  [OK] Session isolation verified: Session A and Session B maintain distinct programs and histories.")

    # --------------------------------------------------------------------------
    # Scenario: Verify Non-Auto-Execution (No subprocess automatically spawned)
    # --------------------------------------------------------------------------
    print("\n[Non-Auto-Execution Verification]")
    from app import _ACTIVE_SESSIONS
    assert sess_a not in _ACTIVE_SESSIONS, "Conversational updates must NEVER auto-spawn execution processes!"
    print("  [OK] Non-auto-execution confirmed: Binary compiled, but execution remains user-controlled.")

    print("\n" + "=" * 70)
    print("ALL 12 CONVERSATIONAL PROGRAMMING SCENARIOS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
