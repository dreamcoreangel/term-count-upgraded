"""
=============================================================
  Word Frequency Analyzer สำหรับนักแปล
  ─────────────────────────────────────
  วิเคราะห์คำที่ใช้บ่อยในเอกสาร .txt / .docx
  รองรับ stopwords ภาษาอังกฤษ | แสดง bar chart | export CSV
=============================================================
"""

import re
import io
import collections
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import textstat  # เพิ่มไลบรารีสำหรับประเมินความยาก

# ─── ติดตั้ง dependency เพิ่มเติมหากยังไม่มี ───────────────────────────────
try:
    from docx import Document
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx"])
    from docx import Document

# ─── Stopwords ภาษาอังกฤษ (เพิ่มเติมได้ใน sidebar) ──────────────────────────
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
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Translation Analyzer Pro",
    page_icon="📖",
    layout="wide",
)

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background: #0f1117; color: #e8e3d9; }
[data-testid="stSidebar"] { background: #16191f; border-right: 1px solid #2a2d35; }
h1 { font-family: 'Georgia', serif; letter-spacing: -1px; }
h2, h3 { font-family: 'Georgia', serif; }
[data-testid="metric-container"] { background: #1c1f29; border: 1px solid #2e3240; border-radius: 10px; padding: 16px 20px; }
[data-testid="stFileUploader"] { border: 2px dashed #4a5568; border-radius: 12px; padding: 8px; background: #13151d; transition: border-color 0.2s; }
[data-testid="stFileUploader"]:hover { border-color: #e8b84b; }
.stDownloadButton > button { background: linear-gradient(135deg, #e8b84b, #c9922a) !important; color: #0f1117 !important; font-weight: 700 !important; border: none !important; border-radius: 8px !important; padding: 0.5rem 1.4rem !important; transition: opacity 0.2s !important; }
.stDownloadButton > button:hover { opacity: 0.85 !important; }
hr { border-color: #2a2d35 !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def extract_text_from_txt(file_bytes: bytes) -> str:
    try: return file_bytes.decode("utf-8")
    except UnicodeDecodeError: return file_bytes.decode("latin-1")

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs)

def tokenize(text: str) -> list[str]:
    text = text.lower()
    return re.findall(r"[a-z]+", text)

def count_words(tokens: list[str], stopwords: set, min_len: int = 2) -> pd.DataFrame:
    filtered = [w for w in tokens if w not in stopwords and len(w) >= min_len]
    counter = collections.Counter(filtered)
    df = pd.DataFrame(counter.most_common(), columns=["คำ", "จำนวนครั้ง"])
    df.index = df.index + 1
    return df

def plot_bar_chart(df: pd.DataFrame, top_n: int, color_accent: str) -> plt.Figure:
    data = df.head(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, max(5, top_n * 0.35)))
    fig.patch.set_facecolor("#1c1f29")
    ax.set_facecolor("#1c1f29")
    bars = ax.barh(data["คำ"], data["จำนวนครั้ง"], color=color_accent, edgecolor="none", height=0.65)
    for bar in bars:
        width = bar.get_width()
        ax.text(width + max(data["จำนวนครั้ง"]) * 0.01, bar.get_y() + bar.get_height() / 2, f"{int(width):,}", va="center", ha="left", fontsize=9, color="#c8c2b4")
    ax.tick_params(colors="#c8c2b4", labelsize=11)
    ax.xaxis.label.set_color("#c8c2b4")
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.axvline(0, color="#3a3d4a", linewidth=1)
    ax.grid(axis="x", color="#2a2d35", linewidth=0.7, linestyle="--")
    ax.set_xlabel("จำนวนครั้งที่ปรากฏ", color="#9a9488", fontsize=11, labelpad=10)
    ax.set_title(f"Top {top_n} คำที่ใช้บ่อยที่สุด", color="#e8e3d9", fontsize=14, fontweight="bold", pad=16)
    plt.tight_layout()
    return fig

# ═══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ การตั้งค่า")
    st.divider()
    top_n = st.slider("จำนวนคำที่แสดง (Top N)", min_value=5, max_value=50, value=30, step=5)
    min_len = st.slider("ความยาวคำขั้นต่ำ (ตัวอักษร)", min_value=1, max_value=6, value=2)
    chart_color = st.color_picker("สีแผนภูมิ", value="#e8b84b")
    st.divider()
    extra_sw_input = st.text_area("เพิ่ม Stopwords (คั่นด้วยช่องว่าง)", placeholder="e.g. said mr mrs also", height=100)
    extra_stopwords = set(extra_sw_input.lower().split())
    all_stopwords = DEFAULT_STOPWORDS | extra_stopwords
    st.caption(f"Stopwords ทั้งหมด: **{len(all_stopwords)}** คำ")

# ═══════════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<div style='padding: 1.5rem 0 0.5rem 0;'>
  <h1 style='margin:0; font-size:2.2rem; color:#e8e3d9;'>
    📖 Translation Analyzer Pro
  </h1>
  <p style='color:#e8b84b; margin:0.4rem 0 0 0; font-size:1.1rem; font-weight:bold;'>
    [อัปเกรด] วิเคราะห์คำศัพท์ + ประเมินความยากของเอกสาร (สำหรับสายแปล/PM)
  </p>
</div>
""", unsafe_allow_html=True)
st.divider()

# ═══════════════════════════════════════════════════════════════════
#  MAIN PROCESSING
# ═══════════════════════════════════════════════════════════════════
uploaded_file = st.file_uploader(label="อัปโหลดไฟล์ .txt หรือ .docx", type=["txt", "docx"])

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()

    with st.spinner("กำลังประมวลผล..."):
        if ext == "txt": raw_text = extract_text_from_txt(file_bytes)
        elif ext == "docx": raw_text = extract_text_from_docx(file_bytes)

    tokens = tokenize(raw_text)
    df_all = count_words(tokens, all_stopwords, min_len)

    # ─── คำนวณความยากง่ายด้วย Textstat ───
    st.divider()
    st.markdown("### 🧠 ประเมินความยาก-ง่าย (Complexity Analysis)")
    
    if len(raw_text.strip()) > 0:
        flesch_score = textstat.flesch_reading_ease(raw_text)
        reading_level = textstat.text_standard(raw_text)
        
        # แปลผลคะแนน
        if flesch_score >= 80: difficulty, d_color = "ง่ายมาก (เหมาะสำหรับเด็ก)", "🟢"
        elif flesch_score >= 60: difficulty, d_color = "ปานกลาง (คนทั่วไปอ่านได้)", "🟡"
        elif flesch_score >= 30: difficulty, d_color = "ยาก (ระดับมหาวิทยาลัย)", "🟠"
        else: difficulty, d_color = "ยากมาก (ศัพท์เฉพาะทาง/วิชาการ)", "🔴"

        colA, colB, colC = st.columns(3)
        colA.metric("📚 ระดับการอ่าน (Grade Level)", reading_level)
        colB.metric("📊 คะแนนความอ่านง่าย (0-100)", f"{flesch_score:.1f}")
        colC.metric("⚖️ สรุปความยาก", f"{d_color} {difficulty}")
    else:
        st.warning("เอกสารสั้นเกินไป ไม่สามารถวิเคราะห์ความยากได้")

    # ─── แสดงสถิติคำศัพท์ (ฟีเจอร์เดิม) ───
    st.divider()
    st.markdown("### 📊 ภาพรวมคำศัพท์ (Vocabulary Stats)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📄 ชื่อไฟล์", uploaded_file.name)
    col2.metric("🔤 คำทั้งหมด", f"{len(tokens):,}")
    col3.metric("✂️ หลังลบ stopwords", f"{df_all['จำนวนครั้ง'].sum():,}")
    col4.metric("🗂️ คำไม่ซ้ำกัน (Unique)", f"{len(df_all):,}")

    # ─── แสดง Bar Chart ───
    st.divider()
    st.markdown(f"### 📈 Top {top_n} คำที่ใช้บ่อยที่สุด")
    if not df_all.empty:
        fig = plot_bar_chart(df_all, top_n, chart_color)
        st.pyplot(fig)
        plt.close(fig)

    # ─── แสดงตารางและดาวน์โหลด ───
    st.divider()
    df_display = df_all.head(top_n).copy()
    df_display["สัดส่วน (%)"] = (df_display["จำนวนครั้ง"] / df_display["จำนวนครั้ง"].sum() * 100).round(2)
    st.dataframe(df_display, use_container_width=True, height=300)

    csv_bytes = df_all.to_csv(index=True, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(label="⬇️ ดาวน์โหลด CSV (คำทั้งหมด)", data=csv_bytes, file_name=f"{uploaded_file.name}_freq.csv", mime="text/csv")
