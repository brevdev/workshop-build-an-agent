"""Run notebook cells in a real Jupyter kernel, answering input() prompts from a script."""

import queue
import time

from jupyter_client.manager import start_new_kernel


class CellError(RuntimeError):
    """A cell raised; the message carries the cell's error and output."""


class Kernel:
    """A python3 kernel started in `cwd`.

    `answers(prompt)` returns the text to type at an input() prompt, like a
    learner would; return None to fail the run on an unexpected prompt.
    """

    def __init__(self, cwd, answers=None, startup_timeout=120):
        self.manager, self.client = start_new_kernel(kernel_name="python3", cwd=str(cwd),
                                                     startup_timeout=startup_timeout)
        self.answers = answers or (lambda prompt: None)
        self.transcript = []

    def run(self, code, timeout=900):
        """Execute `code`; return its text output. Raise CellError on an exception or timeout."""
        msg_id = self.client.execute(code, allow_stdin=True, store_history=True)
        output, deadline = [], time.monotonic() + timeout
        while True:
            if time.monotonic() > deadline:
                self.manager.interrupt_kernel()
                raise CellError(f"Timed out after {timeout}s.\n" + "".join(output)[-3000:])
            try:
                request = self.client.get_stdin_msg(timeout=0.05)
                if request["msg_type"] == "input_request":
                    prompt = request["content"]["prompt"]
                    reply = self.answers(prompt)
                    if reply is None:
                        self.manager.interrupt_kernel()
                        raise CellError(f"Unexpected input prompt: {prompt!r}\n" + "".join(output)[-3000:])
                    output.append(f"{prompt}{reply}\n")
                    self.client.input(reply)
            except queue.Empty:
                pass
            try:
                message = self.client.get_iopub_msg(timeout=0.2)
            except queue.Empty:
                continue
            if message["parent_header"].get("msg_id") != msg_id:
                continue
            kind, content = message["msg_type"], message["content"]
            if kind == "stream":
                output.append(content["text"])
            elif kind in ("execute_result", "display_data"):
                data = content["data"]
                output.append((data.get("text/markdown") or data.get("text/plain", "")) + "\n")
            elif kind == "error":
                output.append(f"{content['ename']}: {content['evalue']}\n")
                self.transcript.append("".join(output))
                raise CellError("".join(output)[-4000:])
            elif kind == "status" and content["execution_state"] == "idle":
                break
        text = "".join(output)
        self.transcript.append(text)
        return text

    def close(self):
        self.client.stop_channels()
        self.manager.shutdown_kernel(now=True)
