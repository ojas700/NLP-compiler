import uuid
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from ai.interpreter import interpret_natural_language
from ai.explainer import explain_c_code
from ai.conversational import (
    init_or_update_session,
    process_conversational_update,
    undo_last_update,
    reset_conversation_session,
    get_conversation_session
)
from compiler.runner import run_compiler_pipeline, run_c_pipeline
from compiler.interactive_session import ExecutionSession

BASE_DIR = Path(__file__).parent
app = FastAPI(title="NLP Compiler")

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "gui")), name="static")

class CompileRequest(BaseModel):
    content: str
    mode: str = "nlp"  # "nlp" or "c"
    session_id: str = ""

class ExplainRequest(BaseModel):
    c_code: str
    language: str = "english"

class ConvUpdateRequest(BaseModel):
    session_id: str
    message: str

class ConvSessionRequest(BaseModel):
    session_id: str

@app.get("/")
def get_landing():
    return FileResponse(BASE_DIR / "gui" / "index.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/ide")
def get_ide():
    return FileResponse(BASE_DIR / "gui" / "ide.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/ide.css")
def get_ide_css():
    return FileResponse(BASE_DIR / "gui" / "ide.css", media_type="text/css", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/ide.js")
def get_ide_js():
    return FileResponse(BASE_DIR / "gui" / "ide.js", media_type="application/javascript", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/style.css")
def get_style_css():
    return FileResponse(BASE_DIR / "gui" / "style.css", media_type="text/css", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/landing.js")
def get_landing_js():
    return FileResponse(BASE_DIR / "gui" / "landing.js", media_type="application/javascript", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.post("/api/compile")
def compile_pipeline(req: CompileRequest):
    sess_id = req.session_id or f"sess_{uuid.uuid4().hex[:8]}"
    content = req.content.strip()

    if not content:
        return JSONResponse(status_code=400, content={
            "success": False,
            "error": "Input content cannot be empty."
        })

    # Fresh transaction: initialize all stage outputs to null/empty
    stage_data = {
        "success": False,
        "mode": req.mode,
        "session_id": sess_id,
        "nlp_input": content if req.mode == "nlp" else "",
        "intent": None,
        "il_code": "",
        "compiler_log": "",
        "c_code": "",
        "exe_ready": False,
        "error": None,
        "stage": "nlu" if req.mode == "nlp" else "gcc"
    }

    if req.mode == "c":
        # Direct C code compilation
        comp_res = run_c_pipeline(content, session_id=sess_id)
        stage_data["c_code"] = content
        stage_data["compiler_log"] = comp_res.get("compiler_log", "")
        if not comp_res["success"]:
            stage_data["error"] = comp_res.get("error", "GCC compilation failed.")
            stage_data["stage"] = "gcc_compilation"
            return JSONResponse(status_code=400, content=stage_data)
        stage_data["success"] = True
        stage_data["stage"] = "ready"
        stage_data["exe_ready"] = True
        return stage_data

    # Check for direct IL input: bypass Qwen entirely if valid IL is provided
    def is_direct_il(text: str) -> bool:
        il_keywords = {'DECLARE', 'READ', 'ASSIGN', 'PRINT', 'IF', 'ELSE', 'END_IF', 'WHILE', 'END_WHILE', 'FOR', 'END_FOR'}
        lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip() and not ln.strip().startswith('//') and not ln.strip().startswith('#')]
        if not lines:
            return False
        return all(ln.split()[0].upper() in il_keywords for ln in lines)

    if req.mode == "il" or is_direct_il(content):
        # Direct IL bypass: 0ms LLM overhead
        il_code = content
        stage_data["il_code"] = il_code
        stage_data["intent"] = {"mode": "direct_il_bypass"}
    else:
        # NLP Mode: Qwen NLU -> IL -> Deterministic compiler
        ok, intent_data, il_code, err = interpret_natural_language(content)
        if not ok:
            stage_data["error"] = err or "Natural Language interpretation failed."
            return JSONResponse(status_code=400, content=stage_data)
        
        stage_data["intent"] = intent_data
        stage_data["il_code"] = il_code

    # Run deterministic compiler stages (Lexer -> Parser -> Semantic -> IR -> C -> GCC)
    comp_res = run_compiler_pipeline(il_code, session_id=sess_id)
    
    stage_data["compiler_log"] = comp_res.get("compiler_log", "")
    stage_data["c_code"] = comp_res.get("c_code", "")

    if not comp_res["success"]:
        stage_data["stage"] = comp_res.get("stage", "compiler")
        stage_data["error"] = comp_res.get("error", "Compilation failed")
        return JSONResponse(status_code=400, content=stage_data)

    stage_data["success"] = True
    stage_data["stage"] = "ready"
    stage_data["exe_ready"] = True

    # Initialize conversational programming session for NLP mode
    if req.mode == "nlp" and stage_data.get("intent"):
        try:
            conv_sess = init_or_update_session(
                session_id=sess_id,
                prompt=content,
                intent_data=stage_data["intent"],
                il_code=stage_data["il_code"],
                c_code=stage_data["c_code"],
                compiler_log=stage_data["compiler_log"]
            )
            stage_data["history"] = conv_sess.history
            stage_data["can_undo"] = len(conv_sess.history_stack) > 0
        except Exception as e:
            # Fallback non-fatal
            pass

    return stage_data

@app.post("/api/conversation/update")
def conversation_update(req: ConvUpdateRequest):
    if not req.session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "session_id is required."})
    res = process_conversational_update(req.session_id, req.message)
    if not res.get("success"):
        return JSONResponse(status_code=400, content=res)
    return res

@app.post("/api/conversation/undo")
def conversation_undo(req: ConvSessionRequest):
    if not req.session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "session_id is required."})
    res = undo_last_update(req.session_id)
    if not res.get("success"):
        return JSONResponse(status_code=400, content=res)
    return res

@app.post("/api/conversation/reset")
def conversation_reset(req: ConvSessionRequest):
    if not req.session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "session_id is required."})
    res = reset_conversation_session(req.session_id)
    return res

@app.get("/api/conversation/history/{session_id}")
def conversation_history(session_id: str):
    sess = get_conversation_session(session_id)
    return {
        "success": True,
        "session_id": session_id,
        "history": sess.history,
        "can_undo": len(sess.history_stack) > 0,
        "has_active_program": sess.current_intent is not None
    }

@app.post("/api/explain")
def explain_code_endpoint(req: ExplainRequest):
    c_code = req.c_code.strip()
    if not c_code or c_code == "Deterministic C code generated by compiler will appear here.":
        return JSONResponse(status_code=400, content={
            "success": False,
            "error": "No C code found to explain. Please compile a program first."
        })

    ok, explanation, err = explain_c_code(c_code, language=req.language)
    if not ok:
        return JSONResponse(status_code=500, content={
            "success": False,
            "error": err or "Failed to generate explanation."
        })

    return {
        "success": True,
        "language": req.language,
        "explanation": explanation
    }

# Active interactive sessions for WebSocket stdin/stdout
_ACTIVE_SESSIONS = {}

@app.websocket("/ws/exec/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    exe_path = BASE_DIR / "output" / f"{session_id}_program.exe"

    if not exe_path.exists():
        await websocket.send_json({
            "type": "error",
            "message": "Executable not found. Please compile your program first."
        })
        await websocket.close()
        return

    session = ExecutionSession(str(exe_path), websocket)
    _ACTIVE_SESSIONS[session_id] = session
    await session.start()

    try:
        while True:
            raw_msg = await websocket.receive_text()
            try:
                data = json.loads(raw_msg)
                msg_type = data.get("type")
                if msg_type == "stdin":
                    session.write_stdin(data.get("data", ""))
                elif msg_type == "kill":
                    session.terminate()
                    break
            except json.JSONDecodeError:
                # Raw text fallback
                session.write_stdin(raw_msg)
    except WebSocketDisconnect:
        session.terminate()
    finally:
        _ACTIVE_SESSIONS.pop(session_id, None)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
