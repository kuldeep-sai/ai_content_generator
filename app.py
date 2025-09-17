import streamlit as st
from openai import OpenAI
import random

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
st.write("Generate Google SERP-optimized content with E-E-A-T principles.")

templates = {
    "Resume": "Write a professional SEO-optimized resume article with examples, structure, and FAQs.",
    "Cover Letter": "Create a compelling cover letter guide with examples, templates, and FAQs.",
    "Generic": "Generate an in-depth SEO-optimized article with clear structure, examples, and FAQs.",
    "How to Become": "Write a step-by-step guide on how to become [ROLE], with skills, salary insights, and FAQs.",
    "Job Description": "Write an SEO-friendly job description template with responsibilities, skills, and FAQs.",
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
        with st.spinner("✨ Generating SEO content..."):
            try:
                prompt = f"""
                Generate a long-form SEO article on "{topic}".
                Must follow Google E-E-A-T guidelines:
                - Show experience, expertise, authority, and trustworthiness.
                - Include introduction, key sections, examples, and conclusion.
                - Add FAQs at the end (with detailed answers).
                - Use engaging formats (tables, bullet points, checkboxes, infographics, graphs where possible).
                - Ensure readability and keyword optimization without stuffing.
                - Follow template style: {custom_prompt}
                """

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1500,
                )

                article = response.choices[0].message.content

                st.success("✅ Content Generated Successfully!")
                st.markdown(article)

                # -------------------------
                # Add Sample Engagement Blocks
                # -------------------------
                st.subheader("📊 Example Data Visualization")
                st.bar_chart(
                    {
                        "Skills Demand": [random.randint(40, 90) for _ in range(5)],
                        "Salary Growth": [random.randint(50, 100) for _ in range(5)],
                    }
                )

                st.subheader("🖼️ Suggested Image Placeholder")
                st.image("https://placehold.co/600x400?text=Infographic+Placeholder")

                st.subheader("✅ Checklist Example")
                st.write(
                    """
                    - [ ] Step 1: Research keywords  
                    - [ ] Step 2: Optimize metadata  
                    - [ ] Step 3: Add engaging visuals  
                    - [ ] Step 4: Include FAQs  
                    - [ ] Step 5: Review for E-E-A-T  
                    """
                )

            except Exception as e:
                st.error(f"⚠️ Error: {e}")
