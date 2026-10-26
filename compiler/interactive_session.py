import asyncio
import os
import subprocess
import threading
import queue
from pathlib import Path

class ExecutionSession:
    """
    Manages an active C process with interactive, real-time stdin/stdout over WebSocket.
    """
    def __init__(self, exe_path: str, websocket):
        self.exe_path = exe_path
        self.ws = websocket
        self.proc = None
        self.output_queue = queue.Queue()
        self.loop = asyncio.get_event_loop()
        self.running = False

    def _reader_thread(self, pipe, pipe_name):
        while self.running:
            try:
                # Read 1 byte at a time to support immediate interactive prompts (e.g. "Enter a: ") without buffering
                chunk = pipe.read(1)
                if not chunk:
                    break
                self.output_queue.put({"type": "stdout" if pipe_name == "stdout" else "stderr", "data": chunk.decode('utf-8', errors='replace')})
            except Exception:
                break
        pipe.close()

    async def start(self):
        try:
            self.proc = subprocess.Popen(
                [self.exe_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0  # unbuffered
            )
        except Exception as e:
            await self.ws.send_json({"type": "error", "message": f"Failed to start executable: {str(e)}"})
            return

        self.running = True

        # Launch reader threads
        t_out = threading.Thread(target=self._reader_thread, args=(self.proc.stdout, "stdout"), daemon=True)
        t_err = threading.Thread(target=self._reader_thread, args=(self.proc.stderr, "stderr"), daemon=True)
        t_out.start()
        t_err.start()

        # Background pump for streaming output to WebSocket
        asyncio.create_task(self._pump_output())

    async def _pump_output(self):
        while self.running:
            # Batch read queue to send chunks responsively
            items = []
            while not self.output_queue.empty():
                try:
                    items.append(self.output_queue.get_nowait())
                except queue.Empty:
                    break
            
            if items:
                # Combine consecutive stdout chars
                combined = []
                for it in items:
                    if combined and combined[-1]["type"] == it["type"]:
                        combined[-1]["data"] += it["data"]
                    else:
                        combined.append(it)
                for c in combined:
                    await self.ws.send_json(c)

            # Check if process ended
            if self.proc.poll() is not None and self.output_queue.empty():
                exit_code = self.proc.poll()
                self.running = False
                await self.ws.send_json({
                    "type": "exit",
                    "exit_code": exit_code,
                    "message": f"Program exited with code {exit_code}"
                })
                break

            await asyncio.sleep(0.02)

    def write_stdin(self, text: str):
        if self.proc and self.proc.stdin and self.running:
            try:
                # Ensure newline
                if not text.endswith("\n"):
                    text += "\n"
                self.proc.stdin.write(text.encode("utf-8"))
                self.proc.stdin.flush()
            except Exception as e:
                pass

    def terminate(self):
        self.running = False
        if self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
