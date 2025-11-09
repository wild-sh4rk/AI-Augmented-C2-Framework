# AI-Augmented C2 Framework

Overview
"AI-Augmented C2 Framework" is a Command-and-Control (C2) proof-of-concept (PoC) project designed to explore "next-generation adversarial operations", combining classical C2 features with "AI-driven adaptability, dynamic payload generation, and stealth capabilities".

Unlike traditional frameworks (e.g., Metasploit, Cobalt Strike, Havoc, Merlin), this framework is being designed to:
- Support "multi-agent communication".
- Adapt payloads dynamically using "machine learning" and "mutation techniques".
- Provide "cross-platform compatibility".
- Enable a "controller-focused workflow", where operators interact only through the controller while the server remains stealthy.

---

Current State (PoC)
At this stage, the framework provides a "basic working backbone":
- Server (`server/app.py`)  
  - Receives agent registration.  
  - Tracks agents, their OS, and working directory.  
  - Stores last command results.  

- Agent (`agent/agent.py`)  
  - Registers itself with the server (including OS + working directory).  
  - Polls the server for tasks.  
  - Executes shell commands and returns output.  
  - Supports directory navigation (`cd`, `pwd`) and system commands (`whoami`, `dir`, `ipconfig`, etc.).  

- Controller (`server/controller.py`)  
  - CLI interface for the operator.  
  - Connects to a chosen agent.  
  - Sends dynamic commands (similar to `msfconsole` or `netcat` interaction).  
  - Displays live output from the agent.

---

Installation & Usage

1. Clone the Repository
```bash
git clone https://github.com/wild-sh4rk/AI-Augmented-C2-Framework.git
cd AI-Augmented-C2-Framework
