# Vibe Analyst

**Visualize, orchestrate, and monitor complex multi-agent workflows in real-time—powered by Agent Context Protocols (ACP).**

Vibe Analyst provides an intuitive, interactive dashboard (`app.py`) that elegantly showcases the capabilities of ACP. By leveraging ACP, users can effortlessly orchestrate and visualize task execution across multiple agents, making complex automation tasks simple and visually intuitive.

## Setup Guide

### Installation

```bash
git clone https://github.com/acp/vibe-analyst.git
cd vibe-analyst

# Install dependencies
pip install -e .
```

### Setting up MCP Servers

Vibe Analyst integrates seamlessly with Multiple Context Protocol (MCP) servers, enabling ACP to manage complex tasks effectively. By default, the following MCP servers are included:

1. **`github`**: Manage GitHub repositories, issues, pull requests, and commits.
2. **`perplexity-ask`**: Perform AI-driven searches and obtain detailed research summaries.
3. **`google-maps`**: Geocode locations, route planning, and place searches.
4. **`slack`**: Integrate Slack messaging directly into workflows.
5. **`mcp-server-chart`**: Create dynamic visualizations and charts.
6. **`youtube-video-summarizer-mcp`**: Automatically summarize YouTube videos.
7. **`everart`**: Generate visuals and creative artwork using generative AI.
8. **`postgres`**: Execute queries and interact seamlessly with PostgreSQL databases.
9. **`google-calendar-mcp`**: Programmatically manage events on Google Calendar.

To add a new server:

* **Python-based servers**: Specify the path to the server's `server.py` file and its virtual environment, along with required environment variables or arguments (refer to the included `config.yml`).
* **Node-based servers**: Provide the path to the built `index.js` after running `npm install`, along with required environment variables or arguments (see examples in `config.yml`).

An example `config.yml` file is provided. To integrate a new MCP server, simply install it and update the `config.yml` accordingly.

### Required Environment Variables

Set up these variables according to each server’s documentation:

* `GITHUB_PERSONAL_ACCESS_TOKEN`
* `PERPLEXITY_API_KEY`
* `GOOGLE_MAPS_API_KEY`
* `SLACK_BOT_TOKEN`
* `SLACK_TEAM_ID`
* `EVERART_API_KEY`
* `database_url` (for PostgreSQL)

**Optional:**

* `SLACK_CHANNEL_IDS`

Finally, run:

```bash
streamlit run app.py
```

Then open your browser at [http://localhost:8501](http://localhost:8501) to start using Vibe Analyst.

---

## `app.py`—Interactive Dashboard Overview

Vibe Analyst (`app.py`) provides an elegant Streamlit-based dashboard featuring:

* **Natural Task Input:** Easily input prompts in plain language or structured JSON.
* **Real-Time DAG Visualization:** Interactive, live-updating Directed Acyclic Graphs (DAGs) clearly show subtasks, dependencies, and execution flow.
* **User-Friendly Outputs:** Dark-themed, responsive UI, ensuring clarity and aesthetic appeal.

You can also customize the dashboard's appearance and functionality by modifying the dashboard prompt. The dashboard prompt defines how tasks, statuses, and agent outputs are presented, allowing you to tailor the visual and interactive aspects of the Vibe Analyst to suit your preferences or requirements.

---

### Future Directions

Currently, Vibe Analyst and ACP provide a streamlined approach to integrating MCP servers. Beyond MCP servers, ACP inherently supports integration with any "tool," including those available within the existing `available_tools` directory. In future updates, we aim to further simplify and generalize this integration process, allowing seamless addition and orchestration of diverse tools with minimal effort.
