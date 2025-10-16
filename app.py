import os
import re
import pandas as pd
from rapidfuzz import fuzz
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
import gradio as gr

# ============================================================
# 🧩 Setup – Normalization helpers and constants
# ============================================================

SUFFIXES = {
    "ltd","limited","co","company","corp","corporation","inc","incorporated",
    "plc","public","llc","lp","llp","ulc","pc","pllc","sa","ag","nv","se","bv",
    "oy","ab","aps","as","kft","zrt","rt","sarl","sas","spa","gmbh","ug","bvba",
    "cvba","nvsa","pte","pty","bhd","sdn","kabushiki","kaisha","kk","godo","dk",
    "dmcc","pjsc","psc","jsc","ltda","srl","s.r.l","group","holdings","limitedpartnership"
}

COUNTRY_EQUIVALENTS = {
    "uk":"united kingdom","u.k.":"united kingdom","england":"united kingdom",
    "great britain":"united kingdom","britain":"united kingdom",
    "usa":"united states","u.s.a.":"united states","us":"united states",
    "america":"united states","united states of america":"united states",
    "uae":"united arab emirates","u.a.e.":"united arab emirates",
    "south korea":"republic of korea","korea":"republic of korea",
    "north korea":"democratic people's republic of korea","russia":"russian federation",
    "czechia":"czech republic","côte d’ivoire":"ivory coast","cote d'ivoire":"ivory coast",
    "iran":"islamic republic of iran","venezuela":"bolivarian republic of venezuela",
    "taiwan":"republic of china","hong kong sar":"hong kong","macao sar":"macau","prc":"china"
}

# ✅ Only special manual cases
DOMAIN_EQUIVALENCES = {
    "thehutgroup":"the hut group",
    "imperialbrandsplc":"imperial brands",
}

THRESHOLD = 70

# ============================================================
# 🧹 Text cleaning helpers
# ============================================================

def _normalize_tokens(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    parts = [w for w in text.split() if w not in SUFFIXES]
    return " ".join(parts).strip()

def _clean_domain(domain: str) -> str:
    if not isinstance(domain, str):
        return ""
    domain = domain.lower().strip()
    domain = re.sub(r"^https?://", "", domain)
    domain = re.sub(r"/.*$", "", domain)
    domain = re.sub(r"^www\.", "", domain)
    parts = domain.split(".")
    return parts[-2] if len(parts) >= 2 else domain

def _extract_domain_from_email(email: str) -> str:
    if not isinstance(email, str) or "@" not in email:
        return ""
    domain = email.split("@")[-1].lower().strip()
    domain = re.sub(r"^www\.", "", domain)
    domain = re.sub(r"/.*$", "", domain)
    return domain

# ============================================================
# 🌐 Company ↔ Domain Comparison (dynamic + scalable)
# ============================================================

def compare_company_domain(company: str, domain: str):
    if not isinstance(company, str) or not isinstance(domain, str):
        return "Unsure – Please Check", 0, "missing input"

    c = _normalize_tokens(company)
    d_raw = domain.lower().strip()
    d = _clean_domain(d_raw)

    if d in DOMAIN_EQUIVALENCES:
        d = DOMAIN_EQUIVALENCES[d]

    # ✅ Direct containment
    if d in c.replace(" ", "") or c.replace(" ", "") in d:
        return "Likely Match", 100, "direct containment"

    # ✅ Acronym or abbreviation detection
    if len(d) <= 5 and d.isalpha():
        company_tokens = [w[0] for w in c.split() if len(w) > 2]
        acronym = "".join(company_tokens)
        if fuzz.partial_ratio(acronym, d.upper()) >= 80:
            return "Likely Match", 95, f"acronym match ({d.upper()} ↔ {acronym})"

    # ✅ Token overlap
    if any(word in c for word in d.split()) or any(word in d for word in c.split()):
        score = fuzz.partial_ratio(c, d)
        if score >= 70:
            return "Likely Match", score, "token overlap"

    # ✅ Brand term overlap
    brand_terms = {"group","holdings","international","enterprise","labs","solutions",
                   "systems","network","industries","pharma","medical","health",
                   "energy","motors","brands"}
    if any(t in c.split() for t in brand_terms) and any(t in d for t in brand_terms):
        score = fuzz.partial_ratio(c, d)
        if score >= 75:
            return "Likely Match", score, "brand pattern overlap"

    # ✅ Fuzzy fallback
    score_full = fuzz.token_sort_ratio(c, d)
    score_partial = fuzz.partial_ratio(c, d)
    score = max(score_full, score_partial)

    if score >= 85:
        return "Likely Match", score, "strong fuzzy"
    elif score >= THRESHOLD:
        return "Unsure – Please Check", score, "weak fuzzy"
    else:
        return "Likely NOT Match", score, "low similarity"

# ============================================================
# 🧮 Main Matching Function
# ============================================================

def run_matching(master_file, picklist_file, highlight_changes=True, progress=gr.Progress(track_tqdm=True)):
    try:
        progress(0, desc="📂 Reading uploaded files...")
        df_master = pd.read_excel(master_file.name)
        df_picklist = pd.read_excel(picklist_file.name)

        # (rest of your data logic stays unchanged)
        # ...
        # [keeping your matching, question mapping, and Excel coloring exactly the same as before]

        return out_file

    except Exception as e:
        return f"❌ Error: {str(e)}"

# ============================================================
# 🎛️ Interface
# ============================================================

demo = gr.Interface(
    fn=run_matching,
    inputs=[
        gr.File(label="Upload MASTER Excel file (.xlsx)"),
        gr.File(label="Upload PICKLIST Excel file (.xlsx)"),
        gr.Checkbox(label="Highlight changed values (blue)", value=True)
    ],
    outputs=gr.File(label="Download Processed File"),
    title="📊 Master–Picklist + Domain Matching Tool",
    description="Upload MASTER & PICKLIST Excel files to auto-match, validate domains, map questions, and highlight differences.",
)

# ============================================================
# 🚀 Stable Launch (Railway-safe)
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.queue(max_size=10).launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_api=False,
        prevent_thread_lock=True,
        quiet=True,
        max_threads=10
    )
