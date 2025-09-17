import streamlit as st
import re
import ast
import io
import base64
import json
import pandas as pd
import matplotlib.pyplot as plt
from keybert import KeyBERT
import markdown as md
import textwrap
from openai import OpenAI  # adapt if you use openai package differently

# ---------- Configuration ----------
# init OpenAI client (replace with your own initialization if needed)
client = OpenAI()

kw_model = KeyBERT()

st.set_page_config(page_title="SEO Content Generator — WP HTML Export", layout="wide")
st.title("📝 SEO Content Generator — HTML for WordPress + JSON-LD FAQ")

# ---------- Templates ----------
templates = {
    "Resume": textwrap.dedent("""\
        SEO article about resumes.
        - Add GRAPH for "Most popular resume formats".
        - Add TABLE for comparison of Resume formats.
        - Insert image placeholders.
        - End with FAQs (section title: Frequently Asked Questions).
        """),
    "Cover Letter": textwrap.dedent("""\
        SEO article about cover letters.
        - Add GRAPH for "Common mistakes in cover letters".
        - Add TABLE comparing Formal vs Informal cover letters.
        - Insert image placeholders.
        - End with FAQs (section title: Frequently Asked Questions).
        """),
    "Generic Blog": textwrap.dedent("""\
        Write a blog-style SEO article optimized for Google SERPs.
        - Suggest GRAPHs (pie, bar, line) with data.
        - Suggest TABLEs for comparisons.
        - Insert image placeholders where relevant.
        - End with FAQs (section title: Frequently Asked Questions).
        """),
    "How to Become": textwrap.dedent("""\
        Career guide "How to become [ROLE]".
        - Add TABLE for Skills vs Certifications.
        - Add GRAPH for Demand growth.
        - Insert image placeholders and checklists.
        - End with FAQs (section title: Frequently Asked Questions).
        """),
    "Job Description": textwrap.dedent("""\
        SEO article about job descriptions.
        - Add TABLE with sample JD content.
        - Add GRAPH for "Demand over years".
        - Insert image placeholders.
        - End with FAQs (section title: Frequently Asked Questions).
        """)
}

# ---------- Inputs ----------
topic = st.text_input("Enter your topic / primary keyword", value="")
template_choice = st.selectbox("Choose a template", list(templates.keys()))
tone = st.selectbox("Tone", ["Professional", "Conversational", "Educational", "Persuasive"])
word_count = st.slider("Target word count", 500, 3000, 1200, step=100)

# editable prompt (prefill from template)
custom_prompt = st.text_area("Customize the SEO prompt (editable)", value=templates[template_choice], height=220)

model = st.selectbox("Model (adjust to your setup)", ["gpt-4o-mini", "gpt-4o", "gpt-4o-mini-preview"])  # adapt to your org model names

generate_button = st.button("Generate SEO Article & HTML")


# ---------- Helpers ----------
def find_blocks(content, tag):
    """Find JSON-like blocks after 'TAG:' labels. Returns list of raw string dicts."""
    pattern = rf"{tag}:\s*(\{{.*?\}})"
    return re.findall(pattern, content, flags=re.DOTALL)


def render_table_html(table_dict):
    """Build HTML table from dict {headers, rows}."""
    headers = table_dict.get("headers", [])
    rows = table_dict.get("rows", [])
    html = "<table class='wp-block-table' style='border-collapse: collapse; width:100%;'>"
    # header
    if headers:
        html += "<thead><tr>"
        for h in headers:
            html += f"<th style='border:1px solid #ddd; padding:6px; text-align:left'>{md.escape(h)}</th>"
        html += "</tr></thead>"
    # body
    html += "<tbody>"
    for r in rows:
        html += "<tr>"
        for c in r:
            html += f"<td style='border:1px solid #ddd; padding:6px'>{md.escape(str(c))}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html


def fig_to_base64_img(fig, fmt="png"):
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/{fmt};base64,{b64}"


def extract_faqs_from_text(content):
    """
    Find 'Frequently Asked Questions' section and parse Q/A pairs.
    Expects format:
    Frequently Asked Questions (or FAQs)
    Q: Question?
    A: Answer...
    or
    - Q: ... A: ...
    """
    # try to locate the FAQ header (case-insensitive)
    faq_header_match = re.search(r"(Frequently Asked Questions|FAQs|FAQ)", content, flags=re.IGNORECASE)
    if not faq_header_match:
        return []

    # take substring from header to end
    start = faq_header_match.start()
    faq_text = content[start:]
    # split lines and find Q/A
    lines = faq_text.splitlines()
    faqs = []
    q = None
    a = None
    for line in lines[1:]:
        line_strip = line.strip()
        if re.match(r"^(Q:|Q\.)", line_strip, flags=re.IGNORECASE):
            if q and a:
                faqs.append({"question": q.strip(), "answer": a.strip()})
            q = re.sub(r"^(Q:|Q\.)\s*", "", line_strip, flags=re.IGNORECASE)
            a = ""
        elif re.match(r"^(A:|A\.)", line_strip, flags=re.IGNORECASE):
            a = re.sub(r"^(A:|A\.)\s*", "", line_strip, flags=re.IGNORECASE)
        elif line_strip.startswith("- Q:") or line_strip.startswith("* Q:"):
            if q and a:
                faqs.append({"question": q.strip(), "answer": a.strip()})
            parts = line_strip.split("A:")
            q = parts[0].replace("- Q:", "").replace("* Q:", "").replace("Q:", "").strip()
            a = parts[1].strip() if len(parts) > 1 else ""
        else:
            # continuation of answer
            if a is not None:
                a += " " + line_strip
    if q and a:
        faqs.append({"question": q.strip(), "answer": a.strip()})
    # fallback: try to parse bullet lists like "- Question? — Answer."
    if not faqs:
        bullets = re.findall(r"[-\*\u2022]\s*(.+?)\s*[–—\-]\s*(.+)", faq_text)
        for qtxt, atxt in bullets:
            faqs.append({"question": qtxt.strip(), "answer": atxt.strip()})
    return faqs


def build_faq_json_ld(faqs):
    items = []
    for f in faqs:
        items.append({
            "@type": "Question",
            "name": f["question"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": f["answer"]
            }
        })
    if not items:
        return ""
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": items
    }
    return json.dumps(schema, indent=2)


# ---------- Main generation ----------
if generate_button:
    if not topic.strip():
        st.error("Please enter a topic/primary keyword.")
    else:
        with st.spinner("Extracting semantic keywords..."):
            candidate_text = f"Write an article about {topic} including related keywords, trends, and subtopics."
            keywords = kw_model.extract_keywords(candidate_text, keyphrase_ngram_range=(1, 2), stop_words="english", top_n=20)
            semantic_keywords = [kw for kw, score in keywords]

        # Compose prompt
        prompt = f"""
{custom_prompt}

Topic: "{topic}"
Word count: {word_count}
Tone: {tone}
Semantic keywords: {', '.join(semantic_keywords)}

⚠️ IMPORTANT (strict formatting instructions for visuals to be parsed):
- Start with 'Meta Title:' then meta title on the same line.
- Then 'Meta Description:' then a short description on the same line.
- Write the main article using Markdown-style H1/H2/H3.
- For TABLE suggestions, include exact literal: 
  TABLE: {{'headers': ['Col1','Col2'], 'rows': [['r1c1','r1c2'], ['r2c1','r2c2']] }}
- For GRAPH suggestions, include exact literal:
  GRAPH: {{'type': 'bar'|'pie'|'line', 'title': 'Title', 'x': ['a','b'], 'y': [10,20] }}
- Use image placeholders as: ![Alt text](image.jpg) where relevant.
- End with a section titled 'Frequently Asked Questions' or 'FAQs' and list at least 3 Q/A pairs using 'Q:' and 'A:' markers.
"""

        # Call OpenAI (adapt to your wrapper; adjust arguments)
        with st.spinner("Calling the language model..."):
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=3000
            )
            content = resp.choices[0].message.content

        # Normalize spacing
        content = re.sub(r"\n{3,}", "\n\n", content)

        # Extract raw GRAPH/TABLE definitions
        raw_tables = find_blocks(content, "TABLE")
        raw_graphs = find_blocks(content, "GRAPH")

        # Remove raw TABLE/G RAPH textual blocks from displayed main article
        display_content = re.sub(r"(TABLE|GRAPH):\s*\{.*?\}", "", content, flags=re.DOTALL)

        st.subheader("✅ Generated Article (Preview)")
        st.markdown(display_content)

        # Parse and render tables (visual in Streamlit + HTML conversion later)
        rendered_tables_html = []
        if raw_tables:
            st.subheader("📋 Parsed Tables")
            for idx, t in enumerate(raw_tables, start=1):
                try:
                    table_dict = ast.literal_eval(t)
                    df = pd.DataFrame(table_dict.get("rows", []), columns=table_dict.get("headers", []))
                    st.table(df)
                    rendered_tables_html.append(render_table_html(table_dict))
                except Exception as e:
                    st.warning(f"Could not parse/render TABLE #{idx}: {e}")

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
                    fig, ax = plt.subplots(figsize=(6, 3.5))
                    if gtype == "bar":
                        ax.bar(x, y)
                        ax.set_ylabel(graph_dict.get("yLabel", ""))
                    elif gtype == "line":
                        ax.plot(x, y, marker="o")
                        ax.set_ylabel(graph_dict.get("yLabel", ""))
                    elif gtype == "pie":
                        ax.pie(y, labels=x, autopct="%1.1f%%")
                    else:
                        ax.text(0.5, 0.5, f"Unsupported graph type: {gtype}", ha='center')
                    ax.set_title(title)
                    st.pyplot(fig)

                    # convert fig to base64 for embedding in HTML
                    img_b64 = fig_to_base64_img(fig)
                    rendered_graphs_html.append(f"<h3>{md.escape(title)}</h3><img src='{img_b64}' alt='{md.escape(title)}' style='max-width:100%; height:auto;'/>")
                except Exception as e:
                    st.warning(f"Could not parse/render GRAPH #{idx}: {e}")

        # Extract Meta Title & Meta Description if model followed instruction
        meta_title = ""
        meta_desc = ""
        mtitle = re.search(r"Meta Title:\s*(.+)", content)
        mdesc = re.search(r"Meta Description:\s*(.+)", content)
        if mtitle:
            meta_title = mtitle.group(1).strip()
        if mdesc:
            meta_desc = mdesc.group(1).strip()

        # Extract FAQs & build JSON-LD
        faqs = extract_faqs_from_text(content)
        faq_schema = build_faq_json_ld(faqs)

        st.subheader("🔑 Semantic Keywords (suggested)")
        st.write(", ".join(semantic_keywords))

        # Keyword coverage
        content_lower = content.lower()
        matched_keywords = [kw for kw in semantic_keywords if kw.lower() in content_lower]
        coverage = (len(matched_keywords) / len(semantic_keywords)) * 100 if semantic_keywords else 0
        st.subheader("📊 Keyword Coverage")
        st.progress(int(coverage))
        st.write(f"Matched {len(matched_keywords)} / {len(semantic_keywords)} keywords — {coverage:.1f}%")
        st.write("Keywords used:", ", ".join(matched_keywords))

        # ---------- Build WordPress-ready HTML ----------
        st.subheader("📦 Export: WordPress-ready HTML (with FAQ JSON-LD)")

        # Convert article markdown to HTML (this keeps images placeholders as <img>)
        # Use markdown package to convert markdown to HTML
        article_html_body = md.markdown(display_content, extensions=['extra', 'nl2br'])

        # Insert rendered tables & graphs into the article HTML after the main body
        visuals_html = ""
        if rendered_tables_html:
            visuals_html += "<section class='generated-tables'>" + "".join(rendered_tables_html) + "</section>"
        if rendered_graphs_html:
            visuals_html += "<section class='generated-graphs'>" + "".join(rendered_graphs_html) + "</section>"

        # Build final HTML
        html_title_tag = f"<title>{md.escape(meta_title) if meta_title else md.escape(topic)}</title>"
        meta_desc_tag = f"<meta name='description' content='{md.escape(meta_desc)}'/>" if meta_desc else ""
        faq_script_tag = f"<script type='application/ld+json'>{faq_schema}</script>" if faq_schema else ""

        final_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
{html_title_tag}
{meta_desc_tag}
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
/* Minimal styling for WordPress paste */
body {{ font-family: Arial, sans-serif; line-height:1.6; padding:16px; color:#222 }}
h1,h2,h3 {{ color:#111 }}
table.wp-block-table {{ border-collapse: collapse; width:100%; margin:12px 0; }}
table.wp-block-table th, table.wp-block-table td {{ border:1px solid #ddd; padding:8px; text-align:left }}
.checklist {{ list-style: none; padding-left:0 }}
.checklist li::before {{ content: "✅ "; padding-right:6px }}
</style>
{faq_script_tag}
</head>
<body>
{article_html_body}
{visuals_html}
</body>
</html>
"""

        # Show small preview of HTML (collapsed)
        st.markdown("**Preview — HTML snippet (first 5000 chars)**")
        st.code(final_html[:5000], language="html")

        # Provide downloads: txt, full html, faq json-ld separately
        st.download_button("📥 Download Article (.txt)", display_content, file_name=f"{topic.replace(' ','_')}.txt", mime="text/plain")
        st.download_button("📥 Download HTML for WordPress (.html)", final_html, file_name=f"{topic.replace(' ','_')}.html", mime="text/html")
        if faq_schema:
            st.download_button("📥 Download FAQ JSON-LD (.json)", faq_schema, file_name=f"{topic.replace(' ','_')}_faq.json", mime="application/json")

        st.success("Done — HTML ready for WordPress. Paste the HTML into 'Custom HTML' block or upload as needed.")
