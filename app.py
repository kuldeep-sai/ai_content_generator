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
st.title("📈 AI-Powered SEO Content Generator")
st.write("Generate AI-overview optimized content with SERP-style titles and FAQs.")

templates = {
    "Resume": "Write a professional article with resume examples, structure, and FAQs.",
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
# Content Generation Logic
# -------------------------
if generate_button:
    if not client:
        st.error("❌ Please enter your OpenAI API key in the sidebar.")
    elif not topic.strip():
        st.error("❌ Please enter a topic/primary keyword.")
    else:
        with st.spinner("✨ Generating SERP-style titles..."):
            try:
                # 1. Generate 5 SERP-style titles
                title_prompt = f"""
                Generate 5 article titles for the topic: "{topic}".
                The titles should mimic top-ranking website titles in Google SERPs.
                Keep them engaging, concise, and click-worthy.
                """
                title_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": title_prompt}],
                    temperature=0.6,
                    max_tokens=200,
                )
                titles_text = title_response.choices[0].message.content
                titles_list = [t.strip("-•0123456789. ") for t in titles_text.split("\n") if t.strip()]

                selected_title = st.selectbox("📝 Select Article Title", titles_list)

                if selected_title:
                    # 2. Generate AI Overview Summary
                    summary_prompt = f"""
                    Write a concise, direct answer summary (50–80 words) for the topic: "{topic}".
                    This should be optimized for AI Overview and featured snippet visibility.
                    Use the selected article title: "{selected_title}".
                    """
                    summary_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": summary_prompt}],
                        temperature=0.4,
                        max_tokens=200,
                    )
                    ai_summary = summary_response.choices[0].message.content

                    # 3. Generate Full Article
                    article_prompt = f"""
                    Generate a detailed article on "{topic}" with the title "{selected_title}".
                    Requirements:
                    - Start with a clear introduction.
                    - Add structured sections with subheadings, examples, and FAQs.
                    - Include bullet points, checklists where useful.
                    - Avoid mentioning Google or algorithms.
                    - Follow this style: {custom_prompt}
                    """
                    article_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": article_prompt}],
                        temperature=0.7,
                        max_tokens=1500,
                    )
                    article = article_response.choices[0].message.content

                    # -------------------------
                    # Display
                    # -------------------------
                    st.success("✅ Content Generated Successfully!")

                    st.subheader("🖋️ Article Title")
                    st.markdown(f"**{selected_title}**")

                    st.subheader("🔎 AI Overview Answer Summary")
                    st.markdown(f"> {ai_summary}")

                    st.subheader("📄 Full Article")
                    st.markdown(article)

                    st.subheader("✅ Checklist Example")
                    st.write(
                        """
                        - [ ] Step 1: Research keywords  
                        - [ ] Step 2: Optimize headings and subheadings  
                        - [ ] Step 3: Use bullet points and checklists  
                        - [ ] Step 4: Include FAQs  
                        - [ ] Step 5: Review content for clarity and accuracy  
                        """
                    )

            except Exception as e:
                st.error(f"⚠️ Error: {e}")
