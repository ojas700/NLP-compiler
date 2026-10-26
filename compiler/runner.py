import subprocess
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
COMPILER_EXE = BASE_DIR / "compiler" / "nlp_compiler.exe"
OUTPUT_DIR = BASE_DIR / "output"

def run_compiler_pipeline(il_code: str, session_id: str = "default"):
    """
    Executes the deterministic compiler stages on the given IL code:
    1. Lexer & Parser
    2. Symbol Table & Semantic Analysis
    3. Intermediate Representation (3-Address Code)
    4. C Code Generation
    5. MinGW / GCC Compilation

    Returns a dict with stage outputs, errors, success status, and executable path.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    il_file = OUTPUT_DIR / f"{session_id}_input.il"
    c_file = OUTPUT_DIR / f"{session_id}_generated.c"
    exe_file = OUTPUT_DIR / f"{session_id}_program.exe"

    # Clean old executable to guarantee no stale execution
    if exe_file.exists():
        try:
            exe_file.unlink()
        except Exception:
            pass

    # Write IL code
    with open(il_file, "w", encoding="utf-8") as f:
        f.write(il_code.strip() + "\n")

    # Step A: Run nlp_compiler.exe
    cmd_compile = [str(COMPILER_EXE), str(il_file), str(c_file)]
    res = subprocess.run(cmd_compile, capture_output=True, text=True, cwd=str(BASE_DIR))

    compiler_log = res.stdout + ("\n" + res.stderr if res.stderr else "")
    
    if res.returncode != 0:
        return {
            "success": False,
            "stage": "compiler_pipeline",
            "error": f"Compiler failed with exit code {res.returncode}",
            "compiler_log": compiler_log,
            "c_code": None,
            "exe_path": None
        }

    # Step B: Read generated C code
    c_code = ""
    if c_file.exists():
        with open(c_file, "r", encoding="utf-8") as f:
            c_code = f.read()

    # Step C: Compile with GCC/MinGW (-O1 for fast build time without slow unrolling/inlining)
    gcc_cmd = ["gcc", "-Wall", "-O1", "-o", str(exe_file), str(c_file)]
    gcc_res = subprocess.run(gcc_cmd, capture_output=True, text=True, cwd=str(BASE_DIR))

    if gcc_res.returncode != 0:
        return {
            "success": False,
            "stage": "gcc_compilation",
            "error": f"GCC compilation failed:\n{gcc_res.stderr}",
            "compiler_log": compiler_log,
            "c_code": c_code,
            "exe_path": None
        }

    return {
        "success": True,
        "stage": "ready_to_run",
        "compiler_log": compiler_log,
        "c_code": c_code,
        "exe_path": str(exe_file)
    }

def run_c_pipeline(c_code: str, session_id: str = "default"):
    """
    Compiles arbitrary user C source directly with MinGW/GCC without NLP/IL translation.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    c_file = OUTPUT_DIR / f"{session_id}_user.c"
    exe_file = OUTPUT_DIR / f"{session_id}_program.exe"

    if exe_file.exists():
        try:
            exe_file.unlink()
        except Exception:
            pass

    with open(c_file, "w", encoding="utf-8") as f:
        f.write(c_code.strip() + "\n")

    gcc_cmd = ["gcc", "-Wall", "-O1", "-o", str(exe_file), str(c_file)]
    gcc_res = subprocess.run(gcc_cmd, capture_output=True, text=True, cwd=str(BASE_DIR))

    compiler_log = f"=== GCC DIRECT C COMPILATION ===\nSource: {c_file}\n"
    if gcc_res.stdout:
        compiler_log += gcc_res.stdout + "\n"
    if gcc_res.stderr:
        compiler_log += gcc_res.stderr + "\n"

    if gcc_res.returncode != 0:
        return {
            "success": False,
            "stage": "gcc_compilation",
            "error": f"GCC compilation failed:\n{gcc_res.stderr}",
            "compiler_log": compiler_log,
            "c_code": c_code,
            "exe_path": None
        }

    compiler_log += "[SUCCESS] Direct C source compiled to native executable with GCC 14.2.0.\n"
    return {
        "success": True,
        "stage": "ready_to_run",
        "compiler_log": compiler_log,
        "c_code": c_code,
        "exe_path": str(exe_file)
    }
