# Agent Context Protocols
![ACP Diagram](images/acp.svg)

ACP are a domain and agent-agnostic set of structured protocols for agent-agent communication, coordination, and error handling.
ACPs enable fault-tolerant and long-horizon multi-step collective inference across a diverse set of domain and task-specialized agents.

**Why this matters:** Combine specialized state-of-the-art agents with ACP to build state-of-the-art general multi-agent systems. 

**ACP + MCP:** Rapidly prototype multi-agent systems. Combine any set of state-of-the-art agents with ACP and access any set of contexts with MCP (Model Context Protocols) to create state-of-the-art muti-agent applications.

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
pip install agent_context_protocol           
# or
pip install git+https://github.com/agent-context-protocol/agent-context-protocol.git
```

When any step fails, an **ASSISTANCE\_REQUEST** with a descriptive status code (e.g. `604 TOOL_CALL_FAILURE`) lets a fault-tolerance agent re-plan or retry, so unrelated branches keep running.&#x20;

---
## Robust Error Handling: Status Codes

When an agent fails at any stage, ACP issues an `ASSISTANCE_REQUEST` containing a **standardized error code**, execution trace, and recovery options.

These codes help **localize, categorize, and resolve errors** without halting unrelated branches in the DAG.

> **Use Case Example**
> If a `TripadvisorSearchHotels` API call fails due to a missing check-in date, the agent issues `601 MISSING REQUIRED PARAMETERS`. This allows a fault-tolerant agent to automatically retry with corrected inputs, without pausing agents searching for restaurants.

---

### Status Code Reference

| Code | Error Stage             | Description                                                                                             |
| ---- | ----------------------- | ------------------------------------------------------------------------------------------------------- |
| 601  | Tool Call Request       | **MISSING REQUIRED PARAMETERS** — Agent omitted one or more necessary input fields.                     |
| 602  | Tool Call Request       | **WRONG STEP DETAILS** — The step schema or structure is malformed.                                     |
| 603  | Tool Call Request       | **INVALID PARAMETER USAGE** — Parameter types or formats are not accepted by the tool.                  |
| 604  | Tool Execution          | **TOOL CALL FAILURE** — External API call failed due to timeout, network error, or other runtime issue. |
| 605  | Tool Output Extraction  | **INCOMPLETE INFORMATION** — Output missing key fields required to proceed.                             |
| 606  | Dependency Output Usage | **DEPENDENCY INCOMPLETE INFORMATION** — Output is incomplete for dependent downstream sub-task(s).      |
| 607  | Tool Output Extraction  | **WRONG INFORMATION** — Output is irrelevant, incorrect, or invalid for the sub-task.                   |

Each code serves as a diagnostic checkpoint and feeds into ACP's **recovery logic**, ensuring the workflow continues smoothly wherever possible.

---

## Structured Messaging Formats

ACP ensures that all agent interactions adhere to **rigid, schema-bound messaging protocols**, which serve three core functions:

| Schema                  | Purpose                                                                                                                                                                               |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **AGENT\_REQUEST**      | Defines input for a sub-task: includes method name, headers, and body fields with parameters. Parameters may come from user prompts, internal reasoning, or upstream agent outputs.   |
| **AGENT\_RESPONSE**     | Wraps structured output from tool calls: includes output variables, status codes, and extracted values needed for downstream tasks.                                                   |
| **ASSISTANCE\_REQUEST** | Triggered when execution fails: contains a **status code**, error description, and possible recovery steps (e.g. retry, use alternate tool). Enables fault-tolerant agents to replan. |

These formats allow agents to interoperate with external APIs, tools, and each other—without relying on vague, natural language instructions. 

---

## 📬 End-to-End ACP Message Structures

Below are full examples of the three structured message formats used by ACP systems—`ASSISTANCE_REQUEST`, `AGENT_REQUEST`, and `AGENT_RESPONSE`. Each includes detailed chain-of-thought reasoning, structured fields, and recovery suggestions, as captured during real execution.

---

### Example of `ASSISTANCE_REQUEST`

> This example demonstrates how an agent encounters a missing input issue during a sub-task and raises an Assistance Request using standardized error codes and structured reasoning to recover gracefully.

```
$$CHAIN_OF_THOUGHT$$

• I reviewed the workflow for Sub-Task 1, which aims to display average temperatures of vacation spots in India.
• In Step 1, the Perplexity API successfully provided `vacation_spots_list` containing the names of the top vacation spots.
• In Step 2, the Open-Meteo API is supposed to retrieve average temperature data.
• The Open-Meteo API requires latitude and longitude as input parameters.
• The input variables for Step 2 only include `vacation_spots_list` and `daily_parameters`.
• The required latitude and longitude parameters are missing.
• Without these parameters, the Open-Meteo API cannot retrieve the weather data.
• We need to obtain latitude and longitude for each vacation spot, possibly by adding an intermediate step.
• Reminder to not use API output specifics while explaining the error in Assistance Request.

$$STATUS_UPDATE$$

Progress:
• Previous Progress: Successfully executed Step 1 of the workflow for Sub-Task 1.
• Current Progress: Attempted to execute Step 2 using the Open-Meteo API to retrieve weather data.

Current Step: Sub-Task 1, Step 2

Completed APIs:
• Perplexity: Retrieved a list of top vacation spots in India.
• `vacation_spots_list` is ready for use in subsequent steps.

Encountered Issues:
• Open-Meteo API call failed due to missing latitude and longitude parameters.

$$ASSISTANCE_REQUEST$$

Error Type: 601 MISSING_REQUIRED_PARAMETERS
Error Step: Sub-Task 1, Step 2
Error API: Open-Meteo

Error Description:
• The Open-Meteo API requires latitude and longitude parameters, which are missing from the input variables.

Relevant Context:
• The `vacation_spots_list` contains names but not coordinates.
• Without coordinates, we cannot fetch weather data.

Suggested Resolution:
• Add a step to obtain latitude and longitude for each vacation spot, possibly using the Perplexity API.
```

---

### 📤 Example of `AGENT_REQUEST`

> This example illustrates how the agent constructs structured requests to external tools—in this case, Perplexity AI function—to fetch missing latitude and longitude data for vacation spots.

```
$$CHAIN_OF_THOUGHT$$

Input Variables:
• Name: `vacation_spots_list`
  • Parameter: `query`
  • Type: string
  • Source: TOOL_Output (Sub-Task 1, Step 1)
  • Description: List of vacation spots from Sub-Task 1
  • Value:
    ["The Dolomites, Italy", "Santorini, Greece", "Prague, Czech Republic", 
     "Cinque Terre, Italy", "Barcelona, Spain", "London, UK", "Rome, Italy", 
     "Amsterdam, Netherlands", "Munich, Germany", "Dublin, Ireland"]

Verification of Input Variables:
• The `query` parameter is required and expects a string representing the user's question or search term.
• The `vacation_spots_list` is a list of vacation spot names.
• Since the `query` parameter accepts a single string, and the API recommends not to ask too much information in one search, we should execute separate API requests for each vacation spot.

Determining Single vs. Multiple API Requests:
• The API documentation advises to break down queries and not ask for too much information in one search.
• Therefore, we will execute individual API requests for each vacation spot to ensure accurate and concise responses.
• We are keeping the number of API requests below 5 by getting latitude and longitude data of multiple cities at once.

Method & Function Name:
• Method: FUNCTION
• Function Name: `perplexity_api_response`

Headers:
• No headers are required for this function call.

Request Body Strategy:
• For each vacation spot, we will construct a `query` asking for the latitude and longitude of that specific place.
• The `preplexity_ai_key` is provided as `"YOUR_API_KEY"`.

Final Decision:
• Create ten separate agent requests, one for each vacation spot.
• Each request will have its own `query` parameter formatted as 
  "What are the latitude and longitude of [vacation spot]?"

$$AGENT_REQUEST$$

Method: FUNCTION
URL: perplexity_api_response

BODY:
{
  "query": "What are the latitude and longitude for the following places: 
            \"The Dolomites, Italy\", \"Santorini, Greece\", \"Prague, Czech Republic\", 
            \"Cinque Terre, Italy\", \"Barcelona, Spain\"",
  "preplexity_ai_key": "YOUR_API_KEY"
}

$$AGENT_REQUEST$$

Method: FUNCTION
URL: perplexity_api_response

BODY:
{
  "query": "What are the latitude and longitude for the following places: 
            \"London, UK\", \"Rome, Italy\", \"Amsterdam, Netherlands\", 
            \"Munich, Germany\", \"Dublin, Ireland\"",
  "preplexity_ai_key": "YOUR_API_KEY"
}

```
---

### Example of `AGENT_RESPONSE`

> This example shows how the agent formats and validates tool outputs, converting a response into a structured output variable, which can be parsed and stored in the Execution Blueprint, such that, the downstream steps can reliably consume it in case of inter-dependencies.

```
$$CHAIN_OF_THOUGHT$$

• The API response provides a comprehensive list of vacation spots in the USA, categorized by different types of destinations such as national parks, beach destinations, and urban experiences. This aligns with the expected output variable `vacation_spots_list_usa` for the current step.
• For the current step, the Output Variable `vacation_spots_list_usa` requires a list of recommended vacation spots in the USA. The response provides a list of well-known spots, and these can be extracted and formatted correctly. We will keep the description of the vacation spots as well.
• The extracted vacation spots include a variety of destinations like Yellowstone National Park, Grand Canyon, Hawaii, and New York City, which are popular vacation spots in the USA. These spots can be structured as a list for the output variable.
• For the dependent step (Sub-Task 2, Step 1), the Input Variable `vacation_spots_list_usa` requires a list of vacation spots to retrieve geographic coordinates for each location. The extracted list of vacation spots from the current step meets the requirement of the dependent input and is formatted as a string array, making it compatible for use in the subsequent API call.
• The data is structured appropriately for both the current step's output and the dependent step’s input. The list of vacation spots is formatted as an array of strings, ready to be passed as input to retrieve latitude and longitude.

$$AGENT_RESPONSE$$

Status_Code: 200 OK

Output_Variables:
• Variable Name: `vacation_spots_list_usa`
  • Content:
    National Parks and Natural Wonders:
      - Yellowstone National Park
      - Grand Canyon National Park
      - Glacier National Park
      - Zion National Park
    Beach Destinations:
      - Hawaii
      - Myrtle Beach, South Carolina
    Cities and Urban Experiences:
      - New York City
      - New Orleans, Louisiana
      - San Francisco, California

Dependent_Input_Variables:
• Variable Name: `vacation_spots_list_usa`
  • Sub-Task: 2
  • Step: 1
  • Type: string
  • Content:
    ["San Francisco", "New York City", "New Orleans", 
     "Myrtle Beach, South Carolina", "Hawaii", 
     "Zion National Park", "Glacier National Park", 
     "Grand Canyon National Park", "Yellowstone National Park"]
```
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
