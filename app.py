"""
=============================================================
  Word Frequency Analyzer & MT Draft Generator
  ─────────────────────────────────────
  วิเคราะห์คำที่ใช้บ่อย + สร้างไฟล์แปลสองภาษาอัตโนมัติ
=============================================================
"""

import re
import io
import collections
import time

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ─── ติดตั้ง dependency เพิ่มเติม ───────────────────────────────
try:
    from docx import Document
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx"])
    from docx import Document

import nltk
from deep_translator import GoogleTranslator

# โหลดข้อมูลตัวตัดประโยค
@st.cache_resource
def download_nltk_data():
    try:
        nltk.download('punkt')
        nltk.download('punkt_tab')
    except:
        pass

download_nltk_data()

# ─── Stopwords ภาษาอังกฤษ ──────────────────────────
DEFAULT_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "up", "about", "into", "through",
    "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "need", "dare", "ought",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it",
    "his", "her", "its", "they", "them", "their", "this", "that",
    "these", "those", "who", "which", "what", "how", "when", "where",
    "not", "no", "nor", "so", "yet", "both", "either", "neither",
    "as", "such", "while", "than", "then", "also", "just", "more",
    "s", "t", "re", "ve", "ll", "d", "m",
}

# ═══════════════════════════════════════════════════════════════════
#  PAGE CONFIG & CSS
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Translator Toolkit", page_icon="📖", layout="wide")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background: #0f1117; color: #e8e3d9; }
[data-testid="stSidebar"] { background: #16191f; border-right: 1px solid #2a2d35; }
h1, h2, h3 { font-family: 'Georgia', serif; }
[data-testid="metric-container"] { background: #1c1f29; border: 1px solid #2e3240; border-radius: 10px; padding: 16px 20px; }
[data-testid="stFileUploader"] { border: 2px dashed #4a5568; border-radius: 12px; padding: 8px; background: #13151d; }
.stDownloadButton > button { background: linear-gradient(135deg, #e8b84b, #c9922a) !important; color: #0f1117 !important; font-weight: 700 !important; border: none !important; border-radius: 8px !important; }
hr { border-color: #2a2d35 !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════
def extract_text_from_txt(file_bytes):
    try: return file_bytes.decode("utf-8")
    except: return file_bytes.decode("latin-1")

def extract_text_from_docx(file_bytes):
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs)

def tokenize(text):
    return re.findall(r"[a-z]+", text.lower())

def count_words(tokens, stopwords, min_len=2):
    filtered = [w for w in tokens if w not in stopwords and len(w) >= min_len]
    counter = collections.Counter(filtered)
    df = pd.DataFrame(counter.most_common(), columns=["คำ", "จำนวนครั้ง"])
    df.index = df.index + 1
    return df

def plot_bar_chart(df, top_n, color_accent):
    data = df.head(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, max(5, top_n * 0.35)))
    fig.patch.set_facecolor("#1c1f29")
    ax.set_facecolor("#1c1f29")
    bars = ax.barh(data["คำ"], data["จำนวนครั้ง"], color=color_accent, edgecolor="none", height=0.65)
    for bar in bars:
        width = bar.get_width()
        ax.text(width + max(data["จำนวนครั้ง"]) * 0.01, bar.get_y() + bar.get_height() / 2, f"{int(width):,}", va="center", color="#c8c2b4")
    ax.tick_params(colors="#c8c2b4")
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.set_xlabel("จำนวนครั้งที่ปรากฏ", color="#9a9488")
    plt.tight_layout()
    return fig

@st.cache_data(show_spinner=False)
def generate_mt_draft(text):
    sentences = nltk.sent_tokenize(text)
    translator = GoogleTranslator(source='en', target='th')
    
    draft_data = []
    # แปลทีละประโยค (จำกัดไว้ที่ 100 ประโยคเพื่อไม่ให้เว็บค้าง)
    limit = min(len(sentences), 100)
    for i in range(limit):
        src = sentences[i].replace('\n', ' ').strip()
        if src:
            try:
                tgt = translator.translate(src)
                draft_data.append({"Source (English)": src, "Target (Thai)": tgt})
            except:
                draft_data.append({"Source (English)": src, "Target (Thai)": "[Translation Error]"})
    
    return pd.DataFrame(draft_data), len(sentences)

# ═══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ การตั้งค่า")
    top_n = st.slider("จำนวนคำที่แสดง (Top N)", 5, 50, 30, 5)
    min_len = st.slider("ความยาวคำขั้นต่ำ", 1, 6, 2)
    chart_color = st.color_picker("สีแผนภูมิ", "#e8b84b")
    extra_sw_input = st.text_area("เพิ่ม Stopwords เอง", placeholder="e.g. said mr mrs also", height=100)
    extra_stopwords = set(extra_sw_input.lower().split())
    all_stopwords = DEFAULT_STOPWORDS | extra_stopwords
    st.caption(f"Stopwords ที่ใช้งานอยู่: **{len(all_stopwords)}** คำ")

# ═══════════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════════
st.markdown("<h1 style='color:#e8e3d9;'>📖 Translator Toolkit</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#9a9488;'>วิเคราะห์คำที่ใช้บ่อย และสร้างไฟล์แปลสองภาษา (MT Draft) แบบอัตโนมัติ</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("อัปโหลดเอกสาร (.txt หรือ .docx)", type=["txt", "docx"], label_visibility="collapsed")

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()

    if ext == "txt": raw_text = extract_text_from_txt(file_bytes)
    elif ext == "docx": raw_text = extract_text_from_docx(file_bytes)
    
    # ─── แบ่งหน้าจอเป็น 2 แท็บ ───
    tab1, tab2 = st.tabs(["📊 Word Frequency Analyzer", "🇹🇭 Bilingual MT Draft Generator"])
    
    # ================= TAB 1: ของเดิม =================
    with tab1:
        tokens = tokenize(raw_text)
        df_all = count_words(tokens, all_stopwords, min_len)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📄 ชื่อไฟล์", uploaded_file.name)
        col2.metric("🔤 คำทั้งหมด (raw)", f"{len(tokens):,}")
        col3.metric("✂️ หลังกรอง stopwords", f"{df_all['จำนวนครั้ง'].sum():,}")
        col4.metric("🗂️ คำไม่ซ้ำกัน", f"{len(df_all):,}")

        st.markdown(f"### 📈 Top {top_n} คำที่ใช้บ่อยที่สุด")
        if not df_all.empty:
            fig = plot_bar_chart(df_all, top_n, chart_color)
            st.pyplot(fig)
            plt.close(fig)

            df_display = df_all.head(top_n).copy()
            df_display["สัดส่วน (%)"] = (df_display["จำนวนครั้ง"] / df_display["จำนวนครั้ง"].sum() * 100).round(2)
            st.dataframe(df_display, use_container_width=True)
            
            csv_bytes = df_all.to_csv(index=True, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button("⬇️ ดาวน์โหลด CSV (คำทั้งหมด)", data=csv_bytes, file_name="word_freq.csv", mime="text/csv")
            
    # ================= TAB 2: ฟีเจอร์ใหม่ =================
    with tab2:
        st.markdown("### 🤖 สร้างไฟล์แปลสองภาษา (Bilingual MT Draft)")
        st.write("หั่นประโยคภาษาอังกฤษและแปลเป็นภาษาไทยเบื้องต้น เพื่อนำไปทำเป็นไฟล์อ้างอิงใน CAT Tool")
        
        if st.button("🚀 เริ่มสกัดและแปลประโยค (Start MT)"):
            with st.spinner('AI กำลังทำงาน... อาจใช้เวลาสักครู่...'):
                df_mt, total_sentences = generate_mt_draft(raw_text)
                
            st.success(f"✅ แปลสำเร็จ! (แสดงผลสูงสุด 100 ประโยคแรกจากทั้งหมด {total_sentences} ประโยค)")
            st.dataframe(df_mt, use_container_width=True, height=400)
            
            csv_mt = df_mt.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ Bilingual Draft (CSV)",
                data=csv_mt,
                file_name="bilingual_mt_draft.csv",
                mime="text/csv"
            )

else:
    st.info("👆 อัปโหลดไฟล์ .txt หรือ .docx ด้านบนเพื่อเริ่มใช้งาน")
