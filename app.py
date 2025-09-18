import streamlit as st
from openai import OpenAI

# -------------------------
# Sidebar: API Key Handling
# -------------------------
st.sidebar.subheader("🔑 OpenAI API Key")

if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""

api_key_input = st.sidebar.text_input(
    "Enter your OpenAI API key", type="password", value=st.session_state["api_key"]
)

save_key = st.sidebar.checkbox("Remember for this session", value=True)

if api_key_input:
    if save_key:
        st.session_state["api_key"] = api_key_input
    api_key = api_key_input
else:
    api_key = st.session_state["api_key"]

client = None
if api_key:
    client = OpenAI(api_key=api_key)
else:
    st.sidebar.warning("⚠️ Please enter your OpenAI API key to continue.")

# -------------------------
# App UI
# -------------------------
st.title("📈 AI-Powered SEO Content Generator (India-Focused)")
st.write("Generate SEO-optimized articles with FAQs, examples, and a quality checklist (India-focused).")

templates = {
    "Resume": "Write a professional article with topic-specific resume examples, structure, and FAQs.",
    "Cover Letter": "Create a compelling cover letter guide with examples, templates, and FAQs.",
    "Generic": "Generate a comprehensive, well-structured article with examples and FAQs.",
    "How to Become": "Write a step-by-step guide on how to become [ROLE], with skills, salary insights, and FAQs.",
    "Job Description": "Write a job description template with responsibilities, skills, and FAQs.",
}

template_choice = st.selectbox("📄 Choose Template", list(templates.keys()))
topic = st.text_input("🎯 Enter Topic / Primary Keyword", "")
custom_prompt = st.text_area(
    "✍️ Customize Prompt (optional)", value=templates[template_choice], height=120
)

generate_button = st.button("🚀 Generate Optimized Content")

# -------------------------
# Master Prompt
# -------------------------
master_prompt = """
You are an expert Indian SEO content strategist.

Write a plagiarism-free, AI-detection-free article based on the given topic and title.
Follow Google’s SEO guidelines + E-E-A-T principles.
Ensure Indian context (use Indian companies, salaries, culture, examples).

## Content Requirements:
1. Title & Meta Description
2. Introduction
3. Main Body with H2/H3 headings, examples, lists
4. FAQs (People Also Ask style, India-focused)
5. Practical Examples/Templates
6. Conclusion

At the end, add a Content Quality Checklist with ✅ or ❌ for:
- SEO Optimization
- E-E-A-T
- Indian Context
- Structure & Formatting
- Human-like tone
- Actionable Value
- Readability

Suggest a 1-line fix for any ❌.
"""

# -------------------------
# Content Generation Logic
# -------------------------
if generate_button:
    if not client:
        st.error("❌ Please enter your OpenAI API key in the sidebar.")
    elif not topic.strip():
        st.error("❌ Please enter a topic/primary keyword.")
    else:
        with st.spinner("✨ Generating content..."):
            try:
                # 1. Generate 5 SERP-style titles (India-focused)
                title_prompt = f"""
                Generate 5 SEO-friendly article titles for: "{topic}".
                Titles must mimic top-ranking Google SERPs.
                Keep them concise, engaging, and contextualized for India.
                """
                title_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": title_prompt}],
                    temperature=0.7,
                    max_tokens=200,
                )
                titles_text = title_response.choices[0].message.content
                titles_list = [t.strip("-•0123456789. ") for t in titles_text.split("\n") if t.strip()]

                selected_title = st.selectbox("📝 Select Article Title", titles_list)

                if selected_title:
                    # 2. Generate AI Overview Summary
                    summary_prompt = f"""
                    Write a concise summary (50–80 words) for "{topic}".
                    Use the title: "{selected_title}".
                    Ensure it is plagiarism-free, natural, and contextualized for Indian readers.
                    """
                    summary_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": summary_prompt}],
                        temperature=0.6,
                        max_tokens=200,
                    )
                    ai_summary = summary_response.choices[0].message.content

                    # 3. Generate Full Article
                    article_prompt = f"""
                    Topic: "{topic}"
                    Title: "{selected_title}"
                    {custom_prompt}

                    {master_prompt}
                    """
                    article_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": article_prompt}],
                        temperature=0.6,
                        max_tokens=1500,
                    )
                    article_text = article_response.choices[0].message.content

                    # -------------------------
                    # Display Content
                    # -------------------------
                    st.success("✅ Content Generated Successfully!")

                    st.subheader("🖋️ Article Title")
                    st.markdown(f"**{selected_title}**")

                    st.subheader("🔎 AI Overview Answer Summary")
                    st.markdown(f"> {ai_summary}")

                    st.subheader("📄 Full Article")
                    st.markdown(article_text)

                    # -------------------------
                    # Export Buttons
                    # -------------------------
                    download_content = f"""
Article Title:
{selected_title}

AI Overview Answer Summary:
{ai_summary}

Full Article:
{article_text}
"""
                    st.download_button(
                        label="💾 Download as TXT",
                        data=download_content,
                        file_name=f"{topic.replace(' ', '_')}_SEO_Content.txt",
                        mime="text/plain"
                    )

                    html_content = f"""
<html>
<head>
<meta charset="UTF-8">
<title>{selected_title}</title>
</head>
<body>
<h1>{selected_title}</h1>

<h2>AI Overview Answer Summary</h2>
<p>{ai_summary}</p>

<h2>Full Article</h2>
<p>{article_text.replace('\n', '<br>')}</p>
</body>
</html>
"""
                    st.download_button(
                        label="💾 Download as HTML",
                        data=html_content,
                        file_name=f"{topic.replace(' ', '_')}_SEO_Content.html",
                        mime="text/html"
                    )

            except Exception as e:
                st.error(f"⚠️ Error: {e}")
