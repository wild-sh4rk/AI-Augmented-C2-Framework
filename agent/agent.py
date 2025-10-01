import requests
import time
import socket

# Server address (same one where your Flask app runs)
SERVER = "http://127.0.0.1:5000"

# Agent ID (using machine hostname for uniqueness)
AGENT_ID = socket.gethostname()

while True:
    try:
        # 1. Register with server
        requests.post(f"{SERVER}/register", json={"agent_id": AGENT_ID})

        # 2. Get task
        task_response = requests.get(f"{SERVER}/task/{AGENT_ID}")
        task = task_response.json().get("task", "none")
        print(f"[Agent] Task received: {task}")

        # 3. Execute task (for now only "ping")
        if task == "Is Agent ONLINE?":
            result = "yes!, Agent is Online"
        else:
            result = f"Unknown task: {task}"

        # 4. Report back
        requests.post(f"{SERVER}/report", json={"agent_id": AGENT_ID, "result": result})
        print(f"[Agent] Reported result: {result}")

    except Exception as e:
        print(f"[Agent] Error: {e}")

    # 5. Wait before asking again
    time.sleep(5)
