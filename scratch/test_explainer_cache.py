import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai.explainer import explain_c_code

c_code = """/* NLP COMPILER - Deterministic Generated C */
#include <stdio.h>
#include <stdlib.h>

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    int num1 = 0;
    printf("Enter %s: ", "num1"); fflush(stdout);
    if (scanf("%d", &num1) != 1) { return 0; }
    int num2 = 0;
    printf("Enter %s: ", "num2"); fflush(stdout);
    if (scanf("%d", &num2) != 1) { return 0; }
    int sum = 0;
    sum = num1 + num2;
    printf("Result: %d\\n", sum);

    return 0;
}"""

for lang in ['english', 'hindi', 'tamil', 'telugu']:
    t0 = time.time()
    ok, exp, err = explain_c_code(c_code, language=lang)
    dt = round((time.time() - t0) * 1000, 2)
    print(f"Lang: {lang:7s} | Time: {dt:6.2f}ms | Success: {ok} | Length: {len(exp)}")
