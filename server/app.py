from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory store (for now, will move to database later)
agents = {}
tasks = {}

# Root route (optional, just to check server is running)
@app.route("/")
def home():
    return "AI Augmented C2 Framework Server is running!"

# Register agent
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    agent_id = data.get("agent_id")
    agents[agent_id] = {"status": "active"}
    return jsonify({"message": f"Agent {agent_id} registered successfully."})

# Get task for a specific agent
@app.route("/task/<agent_id>", methods=["GET"])
def get_task(agent_id):
    task = tasks.get(agent_id, "Is Agent ONLINE?")  # default task = "ping"
    return jsonify({"task": task})

# Report results
@app.route("/report", methods=["POST"])
def report():
    data = request.get_json()
    agent_id = data.get("agent_id")
    result = data.get("result")
    print(f"[Server] Report from {agent_id}: {result}")
    return jsonify({"message": "Report received"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
