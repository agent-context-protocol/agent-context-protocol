import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components
import json

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
                              blueprint: dict[str, dict] = None, height = 600):
    completed = {str(x) for x in (completed or set())}

    # 1) Create the PyVis network with white bg and extra tall height
    net = Network(
        height=f"{height}px",
        width="100%",
        directed=True,
        bgcolor="#F7F7F7",
        font_color="#10000000",
    )

    # 2) Build options as Python dict, then dump to JSON
    options = {
        "interaction": {
            "zoomView": True
        },
        "layout": {
            "hierarchical": {
            "enabled": True,
            "direction": "UD",
            "sortMethod": "directed",
            "parentCentralization": True,
            "blockShifting": True
            }
        },
        "nodes": {
            "shape": "circle",
            "size": 30,
            "font": {"size": 12, "face": "monospace", "color": "#000000"},
            "borderWidth": 1
        },
        "edges": {
            "arrows": {"to": {"enabled": True}},
            "width": 5,
            "inherit": False
        },
        "physics": {"enabled": False}
    }
    net.set_options(json.dumps(options))

    # 3) Add nodes with image icons
    for nid, meta in exec_list.items():
        n = str(nid)
        desc = blueprint.get(n, {}).get("subtask_description", "")
        # pick the first step's tool for icon lookup
        tool = None
        if blueprint and n in blueprint:
            steps = blueprint[n].get("steps", {})
            first = next(iter(steps.values()), {})
            tool = first.get("tool")
        icon_file = ICON_MAP.get(tool, "default.png")
        icon_uri  = ICON_DATA_URI.get(icon_file, "")

        net.add_node(
            n,
            shape="image",
            label = "",
            image=icon_uri,
            title=desc,
            color="#32CD32" if n in completed else "#DDDDDD",
            borderWidth=2
        )

    # 4) Add edges, coloring based on source-completion
    for nid, meta in exec_list.items():
        for parent in meta.get("dependent_on", []):
            src, dst = str(parent), str(nid)
            edge_color = "green" if src in completed else "#B22222"
            net.add_edge(
                src,
                dst,
                color={"color": edge_color, "highlight": edge_color},
                arrows="to"
            )

    # 5) Render and embed in Streamlit with matching height
    # net.fit(html=True)
    html = "<style>.edgeLabel{display:none!important;}</style>" + net.generate_html()
    html = html.replace("<hr>", "").replace("<hr/>", "")
    html = "<style>hr{display:none;}</style>" + html
    components.html(html, height=height, scrolling=True)


def update_and_draw_dag(data: dict,
                        completed: set[str] | set[int],
                        placeholder: st.delta_generator.DeltaGenerator):
    placeholder.empty()
    with placeholder.container():
        execution_list: dict[str, dict] = {
            sub_id: {"dependent_on": [], "depth": 0}
            for sub_id in data
        }

        # build dependency list
        for sub_id, sub in data.items():
            for step in sub.get("steps", {}).values():
                for inp in step.get("input_vars", []):
                    for dep in inp.get("dependencies", []):
                        task = dep.get("sub_task")
                        if task and task not in execution_list[sub_id]["dependent_on"]:
                            execution_list[sub_id]["dependent_on"].append(task)

        # compute depths (unused visually but kept for potential layout tweaks)
        changed = True
        while changed:
            changed = False
            for sid, meta in execution_list.items():
                for p in meta["dependent_on"]:
                    pd = execution_list[str(p)]["depth"] + 1
                    if pd > meta["depth"]:
                        meta["depth"] = pd
                        changed = True
        max_depth = max(meta["depth"] for meta in execution_list.values())  # 0-based
        # e.g. 150px per level, plus 100px padding:
        computed_height = 100 + (max_depth + 1) * 150
        render_execution_dag_pyvis(execution_list, completed, data, height = computed_height)