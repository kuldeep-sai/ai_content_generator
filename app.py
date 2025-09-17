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
st.write("Generate AI-overview optimized content with SERP-style titles, FAQs, and India-specific template examples.")

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
        with st.spinner("✨ Generating content..."):
            try:
                # 1. Generate 5 SERP-style titles (India-focused)
                title_prompt = f"""
                Generate 5 article titles for the topic: "{topic}".
                The titles should mimic top-ranking website titles in Google SERPs.
                Keep them engaging, concise, click-worthy, human-like.
                Ensure the titles are relevant to Indian readers, with India-specific context or examples where applicable.
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
                    # 2. Generate AI Overview Summary (India-focused)
                    summary_prompt = f"""
                    Write a concise, direct answer summary (50–80 words) for the topic: "{topic}".
                    Use the selected article title: "{selected_title}".
                    - Make it human-like and natural, not detectable as AI-generated.
                    - Ensure it is plagiarism-free and unique.
                    - Contextualize all information for Indian readers (examples, references, spelling, and phrasing).
                    """
                    summary_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": summary_prompt}],
                        temperature=0.7,
                        max_tokens=200,
                    )
                    ai_summary = summary_response.choices[0].message.content

                    # 3. Generate Full Article (India-focused)
                    article_prompt = f"""
                    Generate a detailed article on "{topic}" with the title "{selected_title}".
                    Requirements:
                    - Start with a clear introduction.
                    - Add structured sections with subheadings, examples, and FAQs.
                    - Include bullet points, checklists where useful.
                    - Make the writing human-like, natural, plagiarism-free.
                    - Contextualize all content for India (jobs, salaries, companies, culture, examples).
                    - Follow this style: {custom_prompt}
                    """
                    article_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": article_prompt}],
                        temperature=0.7,
                        max_tokens=1500,
                    )
                    article = article_response.choices[0].message.content

                    # 4. Generate 3–4 examples/templates (India-focused)
                    examples_prompt = f"""
                    Generate 3–4 distinct examples for the chosen template "{template_choice}" on the topic "{topic}".
                    - Ensure all examples are human-like, plagiarism-free, and contextualized for India.
                    - If Resume: provide 3–4 Indian-style resume templates (format, examples, job roles relevant to India).
                    - If Cover Letter: provide 3–4 Indian-context cover letter examples.
                    - If Generic: provide 3–4 articles/blog examples relevant to Indian readers.
                    - If How to Become: provide 3–4 step-by-step guides relevant to Indian industries and roles.
                    - If Job Description: provide 3–4 job description templates reflecting Indian companies and job market.
                    Separate each example clearly, and number them.
                    """
                    examples_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": examples_prompt}],
                        temperature=0.7,
                        max_tokens=1000,
                    )
                    examples_text = examples_response.choices[0].message.content

                    # -------------------------
                    # Display Content
                    # -------------------------
                    st.success("✅ Content Generated Successfully!")

                    st.subheader("🖋️ Article Title")
                    st.markdown(f"**{selected_title}**")

                    st.subheader("🔎 AI Overview Answer Summary")
                    st.markdown(f"> {ai_summary}")

                    st.subheader("📄 Full Article")
                    st.markdown(article)

                    st.subheader(f"📚 {template_choice} Examples / Templates")
                    st.markdown(examples_text)

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

                    # -------------------------
                    # Download Button (TXT)
                    # -------------------------
                    download_content = f"""
Article Title:
{selected_title}

AI Overview Answer Summary:
{ai_summary}

Full Article:
{article}

{template_choice} Examples / Templates:
{examples_text}
"""
                    st.download_button(
                        label="💾 Download All Outputs as TXT",
                        data=download_content,
                        file_name=f"{topic.replace(' ', '_')}_SEO_Content.txt",
                        mime="text/plain"
                    )

                    # -------------------------
                    # Download Button (HTML)
                    # -------------------------
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
<p>{article.replace('\n', '<br>')}</p>

<h2>{template_choice} Examples / Templates</h2>
<p>{examples_text.replace('\n', '<br>')}</p>

<h2>Checklist</h2>
<ul>
<li>Step 1: Research keywords</li>
<li>Step 2: Optimize headings and subheadings</li>
<li>Step 3: Use bullet points and checklists</li>
<li>Step 4: Include FAQs</li>
<li>Step 5: Review content for clarity and accuracy</li>
</ul>
</body>
</html>
"""

                    st.download_button(
                        label="💾 Download All Outputs as HTML",
                        data=html_content,
                        file_name=f"{topic.replace(' ', '_')}_SEO_Content.html",
                        mime="text/html"
                    )

            except Exception as e:
                st.error(f"⚠️ Error: {e}")
