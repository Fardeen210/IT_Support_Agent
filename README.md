# IT Support Agent 🤖

A modern agentic AI system for IT request processing, built with **FastAPI**, modular LLM agents (via [dspy](https://github.com/stanfordnlp/dspy)), and smart memory management using [MCP Context Pruner](https://github.com/langchain-ai/mcp).  
Automate diagnosis, script generation, and workflow approvals for enterprise IT support—all with extensibility and transparency.

---

## 🚀 Features

- **Multi-Agent Orchestration:** Coordinator, Diagnostic, Automation, and Writer agents work together on each request.
- **LLM-Driven Automation:** Uses dspy to route requests and chain skills.
- **Context Pruning:** Keeps memory relevant and under token limits with MCP context pruner.
- **Approval Workflows:** Supports pause/resume and approvals for sensitive actions.
- **API-First:** FastAPI backend for easy integration with ITSM tools or chat interfaces.
- **Script Generation & Validation:** Generates and validates PowerShell/Bash scripts.
- **Extensible:** Add new agents, skills, and tools easily.

---

## 🛠️ Tech Stack

- [FastAPI]– API backend
- [dspy] -Agent/skill orchestration
- [MCP Context Pruner]- Context management
- [LangGraph]- Agent graph orchestration
- [OpenAI API]- or other LLM providers
- [pytest]-Testing
- Python 3.9+

