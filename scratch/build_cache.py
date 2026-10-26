import json
import re
from pathlib import Path
import sys

# Ensure workspace is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from compiler.runner import run_compiler_pipeline
from ai.interpreter import interpret_natural_language

CACHE_FILE = BASE_DIR / "ai" / "explanation_cache.json"

def normalize_c_code(code: str) -> str:
    cleaned = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    cleaned = re.sub(r'//.*', '', cleaned)
    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    return "\n".join(lines)

from scratch.generate_cache import get_seed_data
seeds = get_seed_data()

presets_meta = [
    ('add', 'Ask the user for two numbers, add them and display the result.'),
    ('even_odd', 'Ask the user for a number, if the number % 2 == 0 print 1 else print 0'),
    ('loop_sum', 'Create an integer sum, create an integer i, for i from 1 to 5, set sum to sum + i, end for, print sum'),
    ('temperature', 'Ask the user for c, set f to c * 9 / 5 + 32, print f')
]

cache = {}
if CACHE_FILE.exists():
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    except Exception:
        cache = {}

for key, nl in presets_meta:
    ok, intent, il, err = interpret_natural_language(nl)
    if ok:
        res = run_compiler_pipeline(il, session_id='seed_' + key)
        c_code = res.get('c_code', '').strip()
        norm_code = normalize_c_code(c_code)
        
        explanations = seeds.get(key, {})
        for lang, text in explanations.items():
            cache[f"{lang}:::{c_code}"] = text
            cache[f"{lang}:::{norm_code}"] = text
            cache[f"{lang}:::preset_{key}"] = text

            # Also cache with alternative comment headers
            variant1 = c_code.replace("/* NLP COMPILER - Deterministic Generated C */", "/* NLP COMPILER — Deterministic Generated C */")
            cache[f"{lang}:::{variant1}"] = text
            
            # Variant where sum is declared earlier
            if key == 'add':
                var_sum_early = (
                    "/* NLP COMPILER - Deterministic Generated C */\n"
                    "#include <stdio.h>\n"
                    "#include <stdlib.h>\n\n"
                    "int main() {\n"
                    "    setvbuf(stdout, NULL, _IONBF, 0);\n"
                    "    int sum = 0;\n"
                    "    int num1 = 0;\n"
                    "    printf(\"Enter %s: \", \"num1\"); fflush(stdout);\n"
                    "    if (scanf(\"%d\", &num1) != 1) { return 0; }\n"
                    "    int num2 = 0;\n"
                    "    printf(\"Enter %s: \", \"num2\"); fflush(stdout);\n"
                    "    if (scanf(\"%d\", &num2) != 1) { return 0; }\n"
                    "    sum = num1 + num2;\n"
                    "    printf(\"Result: %d\\n\", sum);\n\n"
                    "    return 0;\n"
                    "}"
                )
                cache[f"{lang}:::{var_sum_early}"] = text
                cache[f"{lang}:::{normalize_c_code(var_sum_early)}"] = text

        print(f"Generated cache entries for preset: {key}")
    else:
        print(f"Failed to generate for: {key} ({err})")

with open(CACHE_FILE, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)

print(f"Total cache entries saved to {CACHE_FILE}: {len(cache)}")
