import plotly.express as px
import plotly.io as pio
import base64
import io

def fig_to_base64_img_plotly(fig, fmt="png"):
    """Convert plotly fig to base64 <img> tag."""
    buf = io.BytesIO()
    fig.write_image(buf, format=fmt)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/{fmt};base64,{b64}"

# ... inside your generation loop:

# Parse and render graphs
rendered_graphs_html = []
if raw_graphs:
    st.subheader("📊 Parsed Graphs")
    for idx, g in enumerate(raw_graphs, start=1):
        try:
            graph_dict = ast.literal_eval(g)
            gtype = graph_dict.get("type", "bar")
            title = graph_dict.get("title", "")
            x = graph_dict.get("x", [])
            y = graph_dict.get("y", [])

            if gtype == "bar":
                fig = px.bar(x=x, y=y, title=title)
            elif gtype == "line":
                fig = px.line(x=x, y=y, title=title, markers=True)
            elif gtype == "pie":
                fig = px.pie(values=y, names=x, title=title)
            else:
                fig = px.scatter(x=[0], y=[0], title=f"Unsupported type: {gtype}")

            st.plotly_chart(fig, use_container_width=True)

            # Convert fig to base64 for embedding in WordPress HTML
            img_b64 = fig_to_base64_img_plotly(fig)
            rendered_graphs_html.append(
                f"<h3>{title}</h3><img src='{img_b64}' alt='{title}' style='max-width:100%; height:auto;'/>"
            )
        except Exception as e:
            st.warning(f"Could not parse/render GRAPH #{idx}: {e}")
