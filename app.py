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
st.write("Generate SEO-ready articles with metadata, keywords, suggested headings, FAQs, and inline samples.")

templates = {
    "Resume": "Write an article with resume writing guide, inline resume samples, and FAQs.",
    "Cover Letter": "Write a cover letter guide with inline cover letter samples, templates, and FAQs.",
    "Generic": "Generate a comprehensive, well-structured article with examples and FAQs.",
    "How to Become": "Write a step-by-step guide on how to become [ROLE], with skills, salary insights, and FAQs.",
    "Job Description": "Write a detailed job description with structured inline sections, India-specific examples, and salary insights.",
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
                # 1. Generate 5 SERP-style titles
                title_prompt = f"""
                Generate 5 SEO-friendly article titles for: "{topic}".
                Titles must mimic top-ranking Google SERPs.
                Keep them concise, engaging, and India-specific.
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
                    # 2. SEO Meta (Title & Description)
                    meta_prompt = f"""
                    Generate an SEO meta title and meta description for the article titled: "{selected_title}".
                    Requirements:
                    - Meta title: ≤60 characters, engaging, India-focused
                    - Meta description: ≤160 characters, concise, includes primary keyword: "{topic}"
                    - Human-like, plagiarism-free
                    Format:
                    Meta Title: ...
                    Meta Description: ...
                    """
                    meta_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": meta_prompt}],
                        temperature=0.7,
                        max_tokens=200,
                    )
                    meta_text = meta_response.choices[0].message.content

                    # 3. Suggested Headings (H2/H3)
                    headings_prompt = f"""
                    Generate a suggested list of H2 and H3 headings for the article titled: "{selected_title}".
                    Requirements:
                    - Use primary keyword: "{topic}" in at least one heading
                    - Include India-specific examples where relevant
                    - Structured for SEO optimization
                    - Provide headings only, in list format
                    """
                    headings_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": headings_prompt}],
                        temperature=0.7,
                        max_tokens=300,
                    )
                    headings_text = headings_response.choices[0].message.content

                    # 4. SEO Keywords
                    keywords_prompt = f"""
                    Generate a list of 5–10 SEO keywords for the topic: "{topic}".
                    Requirements:
                    - Include primary, secondary, and long-tail keywords
                    - India-specific context
                    - Format as comma-separated list
                    """
                    keywords_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": keywords_prompt}],
                        temperature=0.7,
                        max_tokens=200,
                    )
                    keywords_text = keywords_response.choices[0].message.content

                    # 5. AI Overview Summary
                    summary_prompt = f"""
                    Write a concise, direct answer summary (50–80 words) for the topic: "{topic}".
                    Use the selected article title: "{selected_title}".
                    Ensure it is human-like, plagiarism-free, and India-focused.
                    """
                    summary_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": summary_prompt}],
                        temperature=0.7,
                        max_tokens=200,
                    )
                    ai_summary = summary_response.choices[0].message.content

                    # 6. Full Article
                    article_prompt = f"""
                    Generate a detailed article on "{topic}" with the title "{selected_title}".
                    Requirements:
                    - Clear introduction
                    - Structured subheadings
                    - Examples and FAQs
                    - Bullet points or checklists
                    - Human-like, plagiarism-free
                    - India-contextualized
                    - Follow this style: {custom_prompt}
                    """
                    article_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": article_prompt}],
                        temperature=0.7,
                        max_tokens=1500,
                    )
                    article = article_response.choices[0].message.content

                    # 7. FAQs
                    faq_prompt = f"""
                    Generate 5–7 FAQs with concise answers for the topic: "{topic}".
                    - Relevant to Indian readers
                    - Human-like, plagiarism-free
                    - Actionable and informative
                    Format: Q: ... A: ...
                    """
                    faq_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": faq_prompt}],
                        temperature=0.7,
                        max_tokens=600,
                    )
                    faq_text = faq_response.choices[0].message.content

                    # 8. Examples/Samples (inline)
                    if template_choice == "Resume":
                        examples_prompt = f"""
                        Generate 3 detailed resume samples for "{topic}".
                        Use fixed inline headings:

                        ### Fresher Resume Sample
                        [Full fresher resume]

                        ### Mid-level Resume Sample
                        [Full mid-level resume]

                        ### Experienced Resume Sample
                        [Full experienced resume]

                        Context: Indian job market, human-like, plagiarism-free.
                        """
                    elif template_choice == "Cover Letter":
                        examples_prompt = f"""
                        Generate 3 detailed cover letter samples for "{topic}".
                        Use fixed inline headings:

                        ### Fresher Cover Letter Sample
                        [Full fresher cover letter]

                        ### Mid-level Cover Letter Sample
                        [Full mid-level cover letter]

                        ### Experienced Cover Letter Sample
                        [Full experienced cover letter]

                        Context: Indian job market, human-like, plagiarism-free.
                        """
                    elif template_choice == "Job Description":
                        examples_prompt = f"""
                        Generate a detailed Job Description for "{topic}".
                        Use these fixed inline headings:

                        ### Job Title
                        [Insert job title]

                        ### Job Summary
                        [Short overview]

                        ### Key Responsibilities
                        [6–8 bullet points]

                        ### Required Skills & Qualifications
                        [Technical + soft skills, education]

                        ### Salary Insights (India-specific)
                        [Fresher / Mid-level / Experienced INR ranges]

                        ### About the Company (Optional)
                        [Sample company description, India-focused]

                        Context: Human-like, plagiarism-free, India-specific.
                        """
                    else:
                        examples_prompt = f"""
                        Generate 3–4 distinct examples for the template "{template_choice}" on "{topic}".
                        Ensure India-specific, human-like, plagiarism-free.
                        """

                    examples_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": examples_prompt}],
                        temperature=0.7,
                        max_tokens=1200,
                    )
                    examples_text = examples_response.choices[0].message.content

                    # -------------------------
                    # Display Content
                    # -------------------------
                    st.success("✅ Content Generated Successfully!")

                    st.subheader("📝 SEO Meta")
                    st.markdown(meta_text)

                    st.subheader("🏷️ Suggested SEO Keywords")
                    st.markdown(keywords_text)

                    st.subheader("🗂️ Suggested Headings (H2/H3)")
                    st.markdown(headings_text)

                    st.subheader("🔎 AI Overview Answer Summary")
                    st.markdown(f"> {ai_summary}")

                    st.subheader("📄 Full Article")
                    st.markdown(article)

                    st.subheader("❓ FAQs")
                    st.markdown(faq_text)

                    st.subheader(f"📚 {template_choice} Samples / Templates")
                    st.markdown(examples_text)

                    st.subheader("✅ Content Quality Checklist")
                    st.write(
                        """
                        - [ ] Step 1: Research keywords  
                        - [ ] Step 2: Optimize headings & subheadings  
                        - [ ] Step 3: Add bullet points & checklists  
                        - [ ] Step 4: Include FAQs  
                        - [ ] Step 5: Review content for clarity & accuracy  
                        """
                    )

                    # -------------------------
                    # Download Buttons
                    # -------------------------
                    download_content = f"""
SEO Meta:
{meta_text}

SEO Keywords:
{keywords_text}

Suggested Headings:
{headings_text}

AI Overview Answer Summary:
{ai_summary}

Full Article:
{article}

FAQs:
{faq_text}

{template_choice} Samples / Templates:
{examples_text}
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

<h2>SEO Meta</h2>
<p>{meta_text}</p>

<h2>SEO Keywords</h2>
<p>{keywords_text}</p>

<h2>Suggested Headings</h2>
<p>{headings_text.replace('\n', '<br>')}</p>

<h2>AI Overview Answer Summary</h2>
<p>{ai_summary}</p>

<h2>Full Article</h2>
<p>{article.replace('\n', '<br>')}</p>

<h2>FAQs</h2>
<p>{faq_text.replace('\n', '<br>')}</p>

<h2>{template_choice} Samples / Templates</h2>
<p>{examples_text.replace('\n', '<br>')}</p>

<h2>Checklist</h2>
<ul>
<li>Step 1: Research keywords</li>
<li>Step 2: Optimize headings & subheadings</li>
<li>Step 3: Add bullet points & checklists</li>
<li>Step 4: Include FAQs</li>
<li>Step 5: Review content for clarity & accuracy</li>
</ul>
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
