import requests
import time

SERVER_URL = "http://127.0.0.1:5000"

# Command translation map
COMMAND_MAP = {
    "Windows": {
        "ls": "dir",
        "ifconfig": "ipconfig",
        "pwd": "cd",
        "clear": "cls"
    },
    "Linux": {
        "dir": "ls",
        "ipconfig": "ifconfig",
        "cls": "clear"
    },
    "Darwin": {  # macOS
        "dir": "ls",
        "ipconfig": "ifconfig",
        "cls": "clear"
    }
}

def get_agent_info(agent_id):
    try:
        res = requests.get(f"{SERVER_URL}/info/{agent_id}")
        if res.status_code == 200:
            return res.json()
        else:
            return None
    except Exception as e:
        print(f"[Controller Error] {e}")
        return None

def assign_task(agent_id, task):
    try:
        res = requests.post(f"{SERVER_URL}/assign/{agent_id}", json={"task": task})
        if res.status_code == 200:
            print(f"[Controller] Sent: {task}")
        else:
            print(f"[Controller Error] Failed to send task: {res.text}")
    except Exception as e:
        print(f"[Controller Error] {e}")

def get_report(agent_id):
    try:
        res = requests.get(f"{SERVER_URL}/get_report/{agent_id}")
        if res.status_code == 200:
            data = res.json()
            if "result" in data:
                return data
        return None
    except Exception as e:
        print(f"[Controller Error] {e}")
        return None

def main():
    target = input("Enter target agent ID: ")
    agent_info = get_agent_info(target)

    if not agent_info:
        print("[!] Agent not found or offline.")
        return

    os_type = agent_info.get("os", "Unknown")
    cwd = agent_info.get("cwd", "")
    print(f"[*] Connected to agent: {target} ({os_type})")
    print(f"[*] Current Directory: {cwd}")

    while True:
        try:
            # 🔹 Dynamic shell-like prompt
            cmd = input(f"{target}@{os_type}:{cwd}> ").strip()
            if cmd.lower() in ["exit", "quit"]:
                print("[Controller] Exiting...")
                break

            # 🔹 Translate command if needed
            translated = COMMAND_MAP.get(os_type, {}).get(cmd.split(" ")[0], cmd.split(" ")[0])
            if translated != cmd.split(" ")[0]:
                cmd = cmd.replace(cmd.split(" ")[0], translated, 1)

            assign_task(target, cmd)

            # 🔹 Poll until we get a report
            while True:
                time.sleep(1)
                response = get_report(target)
                if response:
                    result = response.get("result", "")
                    cwd = response.get("cwd", cwd)  # update cwd if changed
                    print(result)
                    break

        except KeyboardInterrupt:
            print("\n[Controller] Exiting...")
            break
        except Exception as e:
            print(f"[Controller Error] {e}")

if __name__ == "__main__":
    main()
