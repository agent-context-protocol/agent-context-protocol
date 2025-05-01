import streamlit as st, graphviz as gv
def render_execution_dag(exec_list: dict, completed: set[str] | set[int] = None):
    completed = {str(x) for x in (completed or set())}
    # group nodes by depth
    depth_layers = {}
    for nid, meta in exec_list.items():
        depth_layers.setdefault(meta["depth"], []).append(str(nid))

    dot = gv.Digraph(engine="dot")
    dot.attr(
    rankdir="TB",            # Top to Bottom
    bgcolor="transparent",
    nodesep="0.3",           # ↓ tighter spacing
    ranksep="0.4",
    fontsize="6",           # ↓ smaller node text
    margin="0.1"
)

    for depth, nodes in depth_layers.items():          # keep same-depth on one rank
        with dot.subgraph(name=f"cluster_{depth}") as sg:
            sg.attr(rank="same", style="invis")
            for n in nodes:
                sg.node(
                    n,
                    f"Task {n}",
                    shape="circle",
                    style="filled",
                    fillcolor="limegreen" if n in completed else "lightgray",
                    fontsize="6",           # smaller font
                    width="0.3", height="0.3", fixedsize="true",  # smaller circle
                )

    for nid, meta in exec_list.items():                # edges
        for parent in meta["dependent_on"]:
            dot.edge(str(parent), str(nid))

    svg = dot.pipe(format="svg").decode("utf-8")

    # Optional: clip overflow, add scroll if needed
    style = """
    <div style='height: 280px; overflow: auto; border: 1px solid #ccc; border-radius: 8px; padding: 4px;'>
    """ + svg + "</div>"

    st.markdown(style, unsafe_allow_html=True)
