import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components

import base64
import os
def load_icons_as_base64(icon_dir: str):
    """
    Reads all files in icon_dir and returns a dict mapping
    filename -> data URI (base64).
    """
    icon_data = {}
    for fname in os.listdir(icon_dir):
        path = os.path.join(icon_dir, fname)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(fname)[1].lower()
        # choose MIME type
        if ext == ".svg":
            mime = "image/svg+xml"
        elif ext in {".png", ".jpg", ".jpeg", ".gif"}:
            mime = f"image/{ext.lstrip('.')}"
        else:
            # skip unknown types
            continue
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        icon_data[fname] = f"data:{mime};base64,{b64}"
    return icon_data

# load all your icons into memory once
ICON_DATA_URI = load_icons_as_base64("icons")

ICON_MAP = {
    # GitHub Tools
    "create_or_update_file": "github.jpeg",
    "search_repositories": "github.jpeg",
    "create_repository": "github.jpeg",
    "get_file_contents": "github.jpeg",
    "push_files": "github.jpeg",
    "create_issue": "github.jpeg",
    "create_pull_request": "github.jpeg",
    "fork_repository": "github.jpeg",
    "create_branch": "github.jpeg",
    "list_commits": "github.jpeg",
    "list_issues": "github.jpeg",
    "update_issue": "github.jpeg",
    "add_issue_comment": "github.jpeg",
    "search_code": "github.jpeg",
    "search_issues": "github.jpeg",

    # Perplexity Tools
    "perplexity_ask": "perplexity.png",
    "perplexity_research": "perplexity.png",
    "perplexity_reason": "perplexity.png",

    # Google Maps Tools
    "maps_geocode": "maps.png",
    "maps_reverse_geocode": "maps.png",
    "maps_search_places": "maps.png",
    "maps_place_details": "maps.png",
    "maps_distance_matrix": "maps.png",
    "maps_elevation": "maps.png",
    "maps_directions": "maps.png",

    # Slack Tools
    "slack_list_channels": "slack.png",
    "slack_post_message": "slack.png",
    "slack_reply_to_thread": "slack.png",
    "slack_add_reaction": "slack.png",
    "slack_get_channel_history": "slack.png",
    "slack_get_thread_replies": "slack.png",
    "slack_get_users": "slack.png",
    "slack_get_user_profile": "slack.png",

    # QuickChart
    "generate_chart": "chart.png",
    "download_chart": "chart.png",

    # YouTube
    "get-video-info-for-summary-from-url": "youtube.jpeg",

    # EverArt
    "generate_image": "everart.png",

    # PostgreSQL Query
    "query": "postgresql.png",

    # Google Calendar
    "list-calendars": "calendar.png",
    "list-events": "calendar.png",
    "search-events": "calendar.png",
    "list-colors": "calendar.png",
    "create-event": "calendar.png",
    "update-event": "calendar.png",
    "delete-event": "calendar.png",
}

def _node_label(icon_filename: str, label_text: str) -> str:
    return f"""<
        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
            <TR><TD><IMG SRC="icons/{icon_filename}" SCALE="TRUE"/></TD></TR>
            <TR><TD><B>{label_text}</B></TD></TR>
        </TABLE>
    >"""

# print(ICON_DATA_URI)
def render_execution_dag_pyvis(exec_list: dict,
                              completed: set[str] | set[int] = None,
                              blueprint: dict[str, dict] = None):
    completed = {str(x) for x in (completed or set())}

    net = Network(
        height="320px",
        width="100%",
        directed=True,
        bgcolor="#1f1f2e",  # dark background
        font_color="#e0e0e5"  # light font
    )

    net.set_options("""
    var options = {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed"
        }
      },
      "nodes": {
        "shape": "circle",
        "size": 20,
        "font": {
          "size": 12,
          "face": "monospace",
          "color": "#e0e0e5"
        },
        "borderWidth": 1
      },
      "edges": {
        "arrows": {"to": {"enabled": true}},
        "color": {
          "color": "red",
          "highlight": "red",
          "inherit": false
        },
        "width": 1.5
      },
      "physics": {
        "enabled": false
      }
    }
    """)

    # Add nodes
    for nid, meta in exec_list.items():
        n = str(nid)
        desc = blueprint[n].get("subtask_description", "") if blueprint and n in blueprint else ""
        icon = ICON_MAP.get(blueprint[n]["steps"]["1"]["tool"], "default.svg")
        
        net.add_node(
            n,
            # label='Label 1',  # or label_text if you want some text underneath
            shape='image',
            image=ICON_DATA_URI[icon],  # icon = e.g., 'github.svg'
            title=desc,
            color="#32CD32" if n in completed else "#2b2b3a",
            font={"color": "#e0e0e5"},
            borderWidth=1.5
        )

    # Add edges
    for nid, meta in exec_list.items():
        for parent in meta["dependent_on"]:
            net.add_edge(str(parent), str(nid))

    # Embed
    html = net.generate_html()
    components.html(html, height=340, scrolling=True)


def update_and_draw_dag(data: dict,
                        completed: set[str] | set[int],
                        placeholder: st.delta_generator.DeltaGenerator):
    placeholder.empty()
    with placeholder.container():
        execution_list: dict[str, dict] = {}

        for sub_id, sub in data.items():
            execution_list[sub_id] = {"dependent_on": [], "depth": 0}

        for sub_id, sub in data.items():
            for step in sub["steps"].values():
                for inp in step["input_vars"]:
                    for dep in inp.get("dependencies", []):
                        if dep["sub_task"] not in execution_list[sub_id]["dependent_on"]:
                            execution_list[sub_id]["dependent_on"].append(dep["sub_task"])

        changed = True
        while changed:
            changed = False
            for sub_id, meta in execution_list.items():
                for p in meta["dependent_on"]:
                    pd = execution_list[str(p)]["depth"] + 1
                    if pd > meta["depth"]:
                        meta["depth"] = pd
                        changed = True

        render_execution_dag_pyvis(execution_list, completed, data)
