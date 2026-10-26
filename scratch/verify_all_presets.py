import requests
import json

base = "http://127.0.0.1:8000"

presets = [
    ("add", "Ask the user for two numbers, add them and display the result."),
    ("even_odd", "Ask the user for a number, if the number % 2 == 0 print 1 else print 0"),
    ("loop_sum", "Create an integer sum, create an integer i, for i from 1 to 5, set sum to sum + i, end for, print sum"),
    ("temperature", "Ask the user for c, set f to c * 9 / 5 + 32, print f")
]

for name, nl in presets:
    print(f"\n--- Testing preset: {name} ---")
    r_comp = requests.post(f"{base}/api/compile", json={
        "content": nl,
        "mode": "nlp",
        "session_id": f"sess_verify_{name}"
    })
    assert r_comp.status_code == 200, f"Compile failed for {name}"
    c_code = r_comp.json()["c_code"]
    
    for lang in ["english", "hindi", "tamil", "telugu"]:
        r_exp = requests.post(f"{base}/api/explain", json={
            "c_code": c_code,
            "language": lang
        })
        assert r_exp.status_code == 200, f"Explain failed for {name} in {lang}"
        exp = r_exp.json()["explanation"]
        print(f"  [{lang:7s}] OK ({len(exp)} chars)")

print("\nALL 4 PRESETS IN ALL 4 LANGUAGES VERIFIED!")
