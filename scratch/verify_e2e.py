import requests
import json

base = "http://127.0.0.1:8000"

print("1. Testing GET /ide ...")
r_ide = requests.get(f"{base}/ide")
assert r_ide.status_code == 200, f"GET /ide failed: {r_ide.status_code}"
assert '<script src="/ide.js"></script>' in r_ide.text
assert 'explanation-drawer' in r_ide.text
print("   -> OK: /ide loaded successfully with single /ide.js script")

print("2. Testing GET /ide.js ...")
r_js = requests.get(f"{base}/ide.js")
assert r_js.status_code == 200, f"GET /ide.js failed: {r_js.status_code}"
assert "window.ideScriptLoaded = true;" in r_js.text
assert "renderDrawerResult" in r_js.text
assert "renderDrawerWelcome" in r_js.text
print("   -> OK: /ide.js served with guard and drawer renderers")

print("3. Testing POST /api/compile for 'Add two numbers' ...")
r_comp = requests.post(f"{base}/api/compile", json={
    "content": "Ask the user for two numbers, add them and display the result.",
    "mode": "nlp",
    "session_id": "test_e2e_verify"
})
assert r_comp.status_code == 200, f"Compilation failed: {r_comp.text}"
comp_data = r_comp.json()
assert comp_data.get("success") is True
c_code = comp_data.get("c_code", "")
assert "main" in c_code
print("   -> OK: Generated C code obtained")

print("4. Testing POST /api/explain in all 4 languages ...")
for lang in ["english", "hindi", "tamil", "telugu"]:
    r_exp = requests.post(f"{base}/api/explain", json={
        "c_code": c_code,
        "language": lang
    })
    assert r_exp.status_code == 200, f"Explain failed for {lang}: {r_exp.text}"
    exp_data = r_exp.json()
    assert exp_data.get("success") is True
    explanation = exp_data.get("explanation", "")
    assert len(explanation) > 100, f"Explanation too short for {lang}"
    print(f"   -> OK: {lang.capitalize():7s} explanation verified ({len(explanation)} chars)")

print("\nALL VERIFICATION CHECKS PASSED PERFECTLY!")
