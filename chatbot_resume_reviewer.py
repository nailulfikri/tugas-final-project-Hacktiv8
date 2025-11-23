import os
import fitz  # PyMuPDF
import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="AI Resume Reviewer", layout="centered")
st.title("📄 AI Resume Reviewer")

# --- Sidebar untuk Kontrol ---
with st.sidebar:
    st.header("Settings")
    
    # Tombol Reset Session
    if st.button("Reset / Ganti CV"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
        
    st.info("Gunakan tombol di atas jika ingin mengupload CV baru.")

# --- 1. Cek API Key ---
if "GOOGLE_API_KEY" not in os.environ:
    google_api_key = st.text_input("Masukkan Google API Key", type="password")
    if st.button("Start"):
        if not google_api_key:
            st.error("API Key tidak boleh kosong!")
            st.stop()
        os.environ["GOOGLE_API_KEY"] = google_api_key
        st.rerun()
    st.stop()

# --- 2. Inisiasi LLM ---
# Menggunakan try-except untuk menangani jika model belum tersedia atau API key salah
try:
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)
except Exception as e:
    st.error(f"Error inisiasi LLM: {e}")
    st.stop()

# --- 3. Upload & Proses PDF ---
if "participant_resume" not in st.session_state:
    uploaded_pdf = st.file_uploader("Upload CV (PDF only)", type="pdf")
    if uploaded_pdf:
        with st.spinner("Menganalisa dokumen..."):
            try:
                pdf_bytes = uploaded_pdf.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text()
                
                # Simpan teks ke session state
                st.session_state["participant_resume"] = text
                st.rerun()
            except Exception as e:
                st.error(f"Gagal membaca PDF: {e}")
    st.stop()

resume_text = st.session_state["participant_resume"]

# --- 4. Setup Chat History ---
if "messages_history" not in st.session_state:
    # System Prompt yang lebih spesifik
    system_prompt = f"""
    You are an expert HR and Resume Reviewer. 
    Your goal is to provide constructive feedback, find grammar mistakes, 
    and suggest improvements to the candidate.
    
    Here is the candidate's resume content:
    {resume_text}
    
    Answer based on the resume context above.
    """
    st.session_state["messages_history"] = [SystemMessage(content=system_prompt)]

messages_history = st.session_state["messages_history"]

# --- 5. Tampilan Chat ---
# Container chat agar input text selalu di bawah
chat_container = st.container()

with chat_container:
    for message in messages_history:
        if isinstance(message, SystemMessage):
            continue
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(message.content)

# --- 6. Input User & Respon AI ---
if prompt := st.chat_input("Tanyakan sesuatu tentang resume ini..."):
    # Tampilkan pesan user
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)
    
    # Tambahkan ke history
    messages_history.append(HumanMessage(content=prompt))
    
    # Generate jawaban
    with chat_container:
        with st.chat_message("assistant"):
            with st.spinner("Sedang mengetik..."):
                response = llm.invoke(messages_history)
                st.markdown(response.content)
                
    # Simpan jawaban AI ke history
    messages_history.append(response)
