import sys
sys.path.insert(0, '.')
from ai.interpreter import parse_deterministic_nl
from ai.conversational import analyze_deterministic_update

t1 = parse_deterministic_nl('Ask the user for two numbers and add them and display the result and rename "result" to "sum".')
print('=== Initial 1 (rename result to sum) ===')
for it in t1:
    print(it)

t2 = parse_deterministic_nl('Ask the user for two numbers and add them and display the result and rename "result" to "total".')
print('\n=== Initial 2 (rename result to total) ===')
for it in t2:
    print(it)

current = [
    {'action': 'declare', 'type': 'INT', 'name': 'num1'},
    {'action': 'read', 'name': 'num1'},
    {'action': 'declare', 'type': 'INT', 'name': 'num2'},
    {'action': 'read', 'name': 'num2'},
    {'action': 'declare', 'type': 'INT', 'name': 'sum'},
    {'action': 'assign', 'name': 'sum', 'value': 'num1 + num2'},
    {'action': 'print', 'value': 'sum'}
]

res = analyze_deterministic_update(current, 'rename "result" to "total"')
print('\n=== Conv: rename "result" to "total" ===')
print('Explanation:', res['explanation'])
for it in res['instructions']:
    print(it)

from compiler.runner import run_compiler_pipeline
from ai.validator import intent_to_il

il_code = intent_to_il(res['instructions'])
out = run_compiler_pipeline(il_code)
print('\n=== Compiler Pipeline Status ===')
print('Success:', out.get('success'))
print('Generated C code:\n', out.get('c_code', ''))

import subprocess
il1 = intent_to_il(t1)
out1 = run_compiler_pipeline(il1)
print('\n=== Initial 1 Execution (inputs 12, 1) ===')
print('C code:\n', out1.get('c_code', ''))
res_exec = subprocess.run([out1['exe_path']], input='12\n1\n', text=True, capture_output=True)
print('Execution stdout:\n', res_exec.stdout)



