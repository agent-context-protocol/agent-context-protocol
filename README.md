# Agent Context Protocols

ACPs (Agent Context Protocols) are a **domain-agnostic, structured standard** for agent–agent messaging, coordination, and fault-tolerant error recovery. They centre on a persistent **Execution Blueprint**—a DAG whose nodes are individual tool invocations and whose edges capture data dependencies. 

---

## Why ACP?

| Capability | What it means |
|------------|---------------|
| **Execution Blueprint engine** | Persistently tracks all agent steps, inputs, and outputs inside a DAG; enables live visualisation and restart-from-failure |
| **Structured messaging** | Enforces `AGENT_REQUEST`, `AGENT_RESPONSE`, and `ASSISTANCE_REQUEST` schemas so agents stay interoperable with rigid tools |
| **Robust error handling** | Standard status codes 601-607 stop cascade failures and trigger automatic recovery |
| **Plug-and-play tools** | Drop in new domain APIs without retraining the core system—paper shows SOTA by merely adding a handful of extra tools |
| **Proven at scale** | Achieves **28.3 % accuracy on AssistantBench**—best overall among 16 baselines—plus top-rated multimodal reports and dashboards |

---

## Install

```bash
pip install agent_context_protocol           # PyPI (coming soon)
# or
pip install git+https://github.com/agent-context-protocol/agent-context-protocol.git
```

When any step fails, an **ASSISTANCE\_REQUEST** with a descriptive status code (e.g. `604 TOOL_CALL_FAILURE`) lets a fault-tolerance agent re-plan or retry, so unrelated branches keep running.&#x20;

---

## Status-code cheat-sheet

| Code | Meaning (pipeline stage)              |   |
| ---- | ------------------------------------- | - |
| 601  | Missing required parameters (request) |   |
| 602  | Wrong step details                    |   |
| 603  | Invalid parameter usage               |   |
| 604  | Tool-call failure                     |   |
| 605  | Incomplete information (response)     |   |
| 606  | Dependency incomplete information     |   |
| 607  | Wrong / irrelevant information        |   |

---

## Modules at a glance

```plaintext
agent-context-protocol/
├── available_tools/          # Plug-and-play wrappers for external tools (GitHub, Maps, Slack, etc.)
├── external_env_details/     # API keys, endpoint configs, and other environment-specific settings
├── prompts/                  # System, agent, and assistance prompt templates
├── __init__.py               # Package marker; re-exports top-level helpers for easy import
├── acp_manager.py            # Orchestrates agents: schedules DAG groups, tracks progress, handles fault-tolerance
├── agent.py                  # Agent class that executes blueprint steps and enforces ACP message schema
├── base.py                   # Shared base classes, constants, and utility functions
├── dag_compiler.py           # Converts JSON task specs into an Execution Blueprint (DAG)
├── mcp_node.py               # Seamless adapter layer for calling Model Context Protocol (MCP) servers
└── task_decomposer.py        # Splits high-level tasks into atomic subtasks/groups before scheduling
```