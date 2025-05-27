import streamlit as st
import json
import requests
from pathlib import Path
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import re

# === Load environment variables ===
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

# === Sidebar Info and Snark Control ===
st.sidebar.title("Catullus Translation Lab")
st.info("⚡ Powered by Groq and LLaMA 3. Stylometry meets sarcasm.")

snark_level = st.sidebar.select_slider(
    "Sarcasm Intensity",
    options=["Mild", "Medium", "High"],
    value="Medium"
)

show_raw = st.sidebar.checkbox("Show Raw Rewrite Output")

snark_instructions = {
    "Mild": "Use very restrained, subtle irony. Understatement only.",
    "Medium": "Use clever sarcasm, dry wit, and confident irony.",
    "High": "Exaggerate with mock-flattery, courtly sarcasm, or overt poetic snark — but stay in character."
}

# === Prompt Templates ===
comparison_prompt = PromptTemplate.from_template("""
You are a literary stylist and critic evaluating two English translations of a Latin poem by Catullus.

Your task is to compare them across five literary dimensions. You must choose **exactly one label per cell** from the allowed values — no blends, ranges, or explanations.

Format your response **exactly** like this:

| Dimension         | {label1} | {label2} |
|------------------|----------|----------|
| Tone             | [value]  | [value]  |
| Diction          | [value]  | [value]  |
| Fluency          | [value]  | [value]  |
| Literary Devices | [value]  | [value]  |
| Neoteric Spirit  | [value]  | [value]  |

---

### Allowed Values

**Tone** — Formal, Informal, Ironic, Sincere  
**Diction** — Archaic, Modern, Elevated, Plain  
**Fluency** — Fluid, Dense, Stilted, Fragmented  
**Literary Devices** — Minimal, Moderate, Heavy  
**Neoteric Spirit** — Strong, Moderate, Weak

---

**Translation 1 ({label1}):**
'''{text1}'''

**Translation 2 ({label2}):**
'''{text2}'''

Return only the completed markdown table. No commentary or prose.
""")

rewrite_prompt_template = PromptTemplate.from_template("""
You are a literary translator and voice mimic with a flair for subtle or scathing irony.

Your task is to rewrite a modern English translation of a Latin poem by Catullus. You will **fully adopt the tone, diction, fluency, and stylistic register** of a provided reference translation — while injecting **sarcasm** that feels native to that style.

---

### Instructions

- **Preserve** the meaning and structure (line-for-line if possible)  
- **Imitate** the tone, diction, fluency, and rhythm of the reference  
- **Write it as a poem** — use line breaks, poetic units, and formatting  
- Inject sarcasm that feels authentic to the style:  
    - For elevated styles: mock-heroic, grandiose overstatement  
    - For modern styles: dry wit, undercutting, ironic restraint  

This is not a summary. This is not a paraphrase. This is a voice transfer.

---

### Sarcasm Guidance:
{snark_tone}

---

**Input Translation:**
'''{source_text}'''

**Reference Style (to imitate):**
'''{reference_text}'''

Now rewrite the input in poetic form, preserving line structure.  
Do not include notes, titles, explanations, or markdown formatting.  
Return only the rewritten poem.
""")

# === Groq API Call ===
def call_groq(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt.strip()}],
        "temperature": 0.7
    }
    response = requests.post(GROQ_ENDPOINT, headers=headers, json=data)
    if response.status_code != 200:
        return f"❌ Groq Error {response.status_code}: {response.text}"
    return response.json()["choices"][0]["message"]["content"].strip()

# === Load Data ===
FOLDER = Path(r"C:\Users\benva\OneDrive\Documents\Catullus\Catullus-poems\data")
path = FOLDER / "catullus_combined_translations.json"
with open(path, "r", encoding="utf-8") as f:
    poems = json.load(f)

translators = ["Negenborn", "Perseus", "Wikisource", "PoetryinTranslation"]

# === Sidebar Selection ===
poem_titles = [f"{p['id']}. {p['latin_title']}" for p in poems]
selected_title = st.sidebar.selectbox("Choose a Latin Poem", poem_titles)
selected_poem = next(p for p in poems if f"{p['id']}. {p['latin_title']}" == selected_title)

translator_1 = st.sidebar.selectbox("Translation 1 (source)", translators)
translator_2 = st.sidebar.selectbox("Translation 2 (reference style)", [t for t in translators if t != translator_1])

# === Latin Text Display ===
st.title("📜 Catullus Sarcastic Stylometry Lab")
with st.expander("Latin Original", expanded=False):
    st.code(selected_poem["latin_text"], language="latin")

# === Get Translations ===
t1_text = selected_poem["translations"].get(translator_1)
t2_text = selected_poem["translations"].get(translator_2)

# === Side-by-side Display ===
def split_lines(text):
    return text.splitlines() if text else []

lines_1 = split_lines(t1_text)
lines_2 = split_lines(t2_text)
max_lines = max(len(lines_1), len(lines_2))

st.markdown("### 🌍 Side-by-Side Translations")
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**{translator_1} Translation**")
    for i in range(max_lines):
        st.markdown(lines_1[i] if i < len(lines_1) else "")
with col2:
    st.markdown(f"**{translator_2} Translation**")
    for i in range(max_lines):
        st.markdown(lines_2[i] if i < len(lines_2) else "")

# === Run Chains ===
if t1_text and t2_text:
    with st.spinner("Analyzing style and generating poetic sarcasm..."):
        # Comparison
        comp_prompt = comparison_prompt.format(
            label1=translator_1,
            label2=translator_2,
            text1=t1_text,
            text2=t2_text
        )
        comparison_result = call_groq(comp_prompt)

        # Rewrite
        snark_tone = snark_instructions[snark_level]
        rewrite_prompt = rewrite_prompt_template.format(
            source_text=t1_text,
            reference_text=t2_text,
            snark_tone=snark_tone
        )
        rewrite_result = call_groq(rewrite_prompt)

    st.markdown("### 📊 Comparison Table")
    st.markdown(comparison_result, unsafe_allow_html=True)

    if show_raw:
        st.markdown("### 🔍 Raw Rewrite")
        st.code(rewrite_result)

    # === Clean Rewrite Output ===
    poem_lines = []
    started = False
    for line in rewrite_result.splitlines():
        line_clean = line.strip()
        if not started:
            if line_clean.lower().startswith((
                "note:", "tone:", "style:", "diction:", "fluency:", "*", "here is", "sarcasm", "return", "---"
            )) or re.match(r"^\W*$", line_clean):
                continue
            if line_clean:
                started = True
        if started:
            poem_lines.append(line_clean)

    spaced_rewrite = "\n".join(poem_lines)
    st.markdown("### 🎭 Cleaned Sarcastic Rewrite")
    st.code(spaced_rewrite, language="markdown")
