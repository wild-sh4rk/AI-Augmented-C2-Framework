# Proof of Concept (POC) – AI-Augmented-C2 Framework

📌 Objective
To demonstrate the initial working prototype of the "AI-Augmented Command and Control (C2) Framework" by establishing communication between a central server and an agent.

⚙️ Components
1. Server (`server/app.py`)  
   - Built using Flask.  
   - Handles:
     - Agent registration
     - Task assignment
     - Report collection

2. Agent (`agent/agent.py`) 
   - Written in Python.  
   - Simulates a client machine that:
     - Registers with the server
     - Fetches assigned tasks
     - Executes tasks
     - Reports results back to server

🔄 Workflow
1. Agent starts and registers with the server using a unique ID.  
2. Server assigns a task (e.g., "Is Server ONLINE?").  
3. Agent executes the task and generates a response.  
4. Agent reports results back to the server.  
5. Server logs the report.  

✅ POC Demonstration
Agent Output (Terminal):
