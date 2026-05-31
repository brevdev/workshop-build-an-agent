import json
import os

class MockConfig:
    def __init__(self):
        self.system_prompt = "You are a secure local bash automation agent."

class MockBash:
    def __init__(self, config):
        self.cwd = os.getcwd()
        
    def to_json_schema(self):
        return {
            "name": "exec_bash_command",
            "description": "Execute a safe command in the local environment terminal sandbox",
            "parameters": {
                "type": "object",
                "properties": {"cmd": {"type": "string"}},
                "required": ["cmd"]
            }
        }
        
    def exec_bash_command(self, command):
        print(f"    ⚙️   [SANDBOX EXECUTION] Running: {command}")
        # Only allow safe informational commands in sandbox simulation
        if any(bad in command for bad in ["rm", "sudo", "shutdown", "mkfs"]):
            return json.dumps({"error": "Security Restriction: Command blocked in sandbox model."})
        try:
            import subprocess
            res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
            return json.dumps({"output": res.stdout if res.stdout else res.stderr})
        except Exception as e:
            return json.dumps({"error": str(e)})

class MockLLM:
    def __init__(self, config):
        self.counter = 0
        
    def query(self, messages, schemas):
        self.counter += 1
        last_msg = messages.messages[-1]["content"] if messages.messages else ""
        
        # Reasoner chain-of-thought simulation mimicking modern R1 structures
        think_prefix = "<think>\nAnalyzing local path architecture and checking file node system...\n</think>\n"
        
        class ToolCallFunction:
            def __init__(self, name, args):
                self.name = name
                self.arguments = json.dumps(args)
                
        class ToolCall:
            def __init__(self, name, args):
                self.id = "call_local_123"
                self.function = ToolCallFunction(name, args)

        # Level 4 Customization: Let the agent understand system commands locally
        if "ls" in last_msg.lower() or "dir" in last_msg.lower() or "show" in last_msg.lower():
            if self.counter % 2 != 0:
                return think_prefix + "[AI Agent]: I will check the file structure of the current directory.", [ToolCall("exec_bash_command", {"cmd": "ls -l | head -n 5"})]
        
        return think_prefix + f"[AI Agent]: Processing completed. I have verified your request inside this secure sandbox zone.", None

class MockMessages:
    def __init__(self, system_prompt):
        self.messages = [{"role": "system", "content": system_prompt}]
    def add_user_message(self, text):
        self.messages.append({"role": "user", "content": text})
    def add_assistant_message(self, text):
        self.messages.append({"role": "assistant", "content": text})
    def add_tool_message(self, result, tool_id):
        self.messages.append({"role": "tool", "content": str(result), "tool_id": tool_id})

def confirm_execution(cmd: str) -> bool:
    return input(f"    ▶️   Execute '{cmd}'? [y/N]: ").strip().lower() == "y"

def main():
    print("\n" + "="*50)
    print("🤖 ENTERPRISE BASH-AGENT CUSTOMIZATION SANDBOX ACTIVE")
    print("="*50)
    print("[INFO] Type 'quit' at any time to exit the loop.\n")
    
    config = MockConfig()
    bash = MockBash(config)
    llm = MockLLM(config)
    messages = MockMessages(config.system_prompt)

    while True:
        user = input(f"['{bash.cwd}' 🙂] ").strip()
        if user.lower() == "quit":
            print("\n[🤖] Shutting down customized agent interface. Bye!\n")
            break
        if not user:
            continue
            
        user += f"\n Current working directory: `{bash.cwd}`"
        messages.add_user_message(user)

        while True:
            print("\n[🤖] Thinking...")
            response, tool_calls = llm.query(messages, [bash.to_json_schema()])

            if response:
                response = response.strip()
                if "</think>" in response:
                    response = response.split("</think>")[-1].strip()
                if response:
                    messages.add_assistant_message(response)

            if tool_calls:
                for tc in tool_calls:
                    function_name = tc.function.name
                    function_args = json.loads(tc.function.arguments)

                    if function_name != "exec_bash_command" or "cmd" not in function_args:
                        tool_call_result = json.dumps({"error": "Incorrect tool or function argument"})
                    else:
                        command = function_args["cmd"]
                        if confirm_execution(command):
                            tool_call_result = bash.exec_bash_command(command)
                        else:
                            tool_call_result = {"error": "The user declined execution."}

                    messages.add_tool_message(tool_call_result, tc.id)
            else:
                if response:
                    print(f"\n💬 {response}")
                    print("-" * 50 + "\n")
                break

if __name__ == "__main__":
    main()