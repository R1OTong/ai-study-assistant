import streamlit as st
import os
import requests
from PyPDF2 import PdfReader

# =========================
# CONFIG
# =========================
API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"
PDF_FOLDER = "data/pdfs"

st.set_page_config(page_title="AI Study Assistant", layout="wide")

# =========================
# UI STYLE
# =========================
st.markdown("""
<style>
body {background-color: #0f172a; color: white;}
.block-container {
    background: rgba(15,23,42,0.85);
    padding: 2rem;
    border-radius: 20px;
}
.user-msg {
    background: #2563eb;
    padding: 10px;
    border-radius: 10px;
    margin: 10px 0;
    text-align: right;
}
.ai-msg {
    background: #1e293b;
    padding: 10px;
    border-radius: 10px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# =========================
# SESSION STATE
# =========================
if "chat" not in st.session_state:
    st.session_state.chat = []

# =========================
# LOAD PDF TEXT
# =========================
@st.cache_data
def load_pdfs():
    texts = []
    if not os.path.exists(PDF_FOLDER):
        return texts

    for file in os.listdir(PDF_FOLDER):
        if file.endswith(".pdf"):
            try:
                reader = PdfReader(os.path.join(PDF_FOLDER, file))
                for page in reader.pages:
                    txt = page.extract_text()
                    if txt:
                        texts.append(txt)
            except:
                continue

    return texts

# =========================
# SIMPLE SEARCH
# =========================
def search(query, texts):
    return [t[:300] for t in texts if query.lower() in t.lower()][:3]

# =========================
# AI FUNCTION (SAFE)
# =========================
def ai_answer(prompt):
    if not API_KEY:
        return "❌ API key not set. Add GROQ_API_KEY."

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are an expert Automation & Robotics teacher. Answer clearly for diploma students."},
                {"role": "user", "content": prompt}
            ]
        }

        res = requests.post(url, headers=headers, json=data, timeout=10)

        if res.status_code != 200:
            return f"⚠️ API Error:\n{res.text}"

        return res.json()["choices"][0]["message"]["content"]

    except requests.exceptions.Timeout:
        return "⚠️ AI took too long. Try again."

    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# =========================
# FALLBACK ANSWER
# =========================
def fallback_answer(query):
    return f"""
Basic explanation:

{query} is a concept in engineering.

(⚠️ No detailed notes found in your PDFs)

Try adding proper notes or ask a more specific question.
"""

# =========================
# HEADER
# =========================
st.title("🤖 AI Study Assistant")

# =========================
# FILTERS
# =========================
col1, col2 = st.columns(2)

with col1:
    semester = st.selectbox("Semester", ["All","SEM 2","SEM 3","SEM 4","SEM 5","SEM 6"])

with col2:
    subject = st.selectbox("Subject", [
        "All","BEL","EEE","DTE","CSC","MAB","STC",
        "AIR","AAS","MAA","POR","RPA",
        "TDP","MIR","IPC","ESY","DSP",
        "VLSI","IIT","DRT","ARS","AR VR","ETE"
    ])

# =========================
# INPUT
# =========================
query = st.chat_input("Ask your question...")

# =========================
# PROCESS QUERY
# =========================
if query:
    st.session_state.chat.append(("user", query))

    with st.spinner("AI thinking..."):
        texts = load_pdfs()
        results = search(query, texts)

        context = "\n".join(results)

        prompt = f"""
Question: {query}
Semester: {semester}
Subject: {subject}
Context: {context}

Give a clear, exam-ready answer with simple explanation.
"""

        answer = ai_answer(prompt)

        # fallback if AI fails
        if "Error" in answer or "API" in answer:
            answer = fallback_answer(query)

    st.session_state.chat.append(("ai", answer))

# =========================
# DISPLAY CHAT
# =========================
for role, msg in st.session_state.chat:
    if role == "user":
        st.markdown(f"<div class='user-msg'>{msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-msg'>{msg}</div>", unsafe_allow_html=True)