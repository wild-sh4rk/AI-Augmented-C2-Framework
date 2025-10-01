# AI-Augmented-C2-Framework
# AI Augmented C2 Framework  

## 📖 Introduction  
This project is part of my Bachelor’s research work in Computer Science.  
The goal is to design and implement a **Command-and-Control (C2) framework** that is enhanced with artificial intelligence techniques for future extensions.  

The framework demonstrates how agents (remote clients) can connect to a central server, receive tasks, and report results. Later versions will include a database, security features, and AI components for adaptive behavior.  

---

## 🎯 Objectives  
1. Develop a minimal but functional C2 framework (server + agent).  
2. Extend the framework with secure communication and logging.  
3. Explore AI-based modules for adaptive tasking and evasion.  
4. Document weekly progress for supervisor review.  

---

## 🏗️ Project Phases / Roadmap  
### Week 1–2  
- Literature review (C2 frameworks, REST APIs, Flask basics).  
- Repository setup.  

### Week 3 (Current Phase)  
- Build a minimal Flask server with endpoints:  
  - `/register` → agent registration.  
  - `/task/<agent_id>` → assign tasks.  
  - `/report` → collect results.  
- Create a minimal agent that:  
  - Registers itself.  
  - Requests a task.  
  - Executes simple “ping” task → responds with “pong”.  

### Week 4  
- Add database (SQLite/MongoDB) for storing agents, tasks, and reports.  

### Week 5  
- Add security (encryption/authentication).  

### Week 6+  
- Begin AI integration:  
  - Adaptive task assignment.  
  - Simple evasion strategies.  
- Extend supported agent commands.  

---

## 📂 Project Structure  
