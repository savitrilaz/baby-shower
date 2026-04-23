import streamlit as st
import pandas as pd
import requests
import io

# CONFIG
SHEET_ID = "1fUsJxGXaovwEEhiP6vjV62xDo1fQ6wlaQ9DGaHMFREE"
SPLITWISE_URL = "https://splitwise.com"

CAT_ICONS = {
    "Venue & Logistics": "🏛",
    "Invitations & Guest Experience": "✉️",
    "Food": "🍽️",
    "Drinks": "🥂",
    "Decor & Styling": "🌿",
    "Activities & Games": "🎯",
    "Keepsakes & Sentimental Touches": "💌",
    "Favors & Gifts": "🎁",
    "Budget & Coordination": "📊",
}

STATUS_COLORS = {
    "Completed":        "#D1FAE5",
    "In Progress":      "#DBEAFE",
    "Not Yet Started":  "#F3F4F6",
    "Considering":      "#FFF3CD",
}

STATUS_TEXT = {
    "Completed":        "#065F46",
    "In Progress":      "#1E40AF",
    "Not Yet Started":  "#374151",
    "Considering":      "#856404",
}

PRIORITY_COLORS = {
    "High":   ("#FEE2E2", "#B91C1C"),
    "Medium": ("#FEF3C7", "#92400E"),
    "Low":    ("#EAF2EA", "#4A7C59"),
}

OWNER_COLORS = {
    "Jessica": ("#F2E4E1", "#8C3A3A"),
    "Carly":   ("#E4EAF2", "#2C4A8C"),
    "Kirsten": ("#EAF2E4", "#2C6B3A"),
    "Savitri": ("#F0E4F2", "#6B2C8C"),
}

IDEA_CATS = [
    ("decor",       "🌿", "Decor & balloons"),
    ("food",        "🍽️", "Food ideas"),
    ("drinks",      "🥂", "Signature drinks"),
    ("gifts",       "🎁", "Favors & gift bags"),
    ("activities",  "🎯", "Activities & games"),
    ("other",       "✨", "Other / misc"),
]

SEED_IDEAS = {
    "decor": [
        {"id": 1, "text": "Oversized sage balloon arch at entrance", "author": "Savitri", "score": 3},
        {"id": 2, "text": "Pressed flower place cards at each seat", "author": "Kirsten", "score": 2},
    ],
    "food": [
        {"id": 3, "text": "Cantaloupe + prosciutto skewers as apps", "author": "Jessica", "score": 4},
        {"id": 4, "text": "Mini uncrustable sliders with fancy labels", "author": "Carly", "score": 5},
    ],
    "drinks": [
        {"id": 5, "text": "Nicole's drink: Hugo Spritz with elderflower", "author": "Carly", "score": 3},
        {"id": 6, "text": "Zach's drink: smoky mezcal aperol riff", "author": "Carly", "score": 2},
    ],
    "gifts": [
        {"id": 7, "text": "Passport-style booklet favor with trip tips", "author": "Kirsten", "score": 1},
        {"id": 8, "text": "Custom airline baggage tag with baby's name", "author": "Jessica", "score": 4},
    ],
    "activities": [
        {"id": 9, "text": "Destination bingo — guests pick where baby travels first", "author": "Savitri", "score": 3},
    ],
    "other": [],
}

# PAGE CONFIG
st.set_page_config(
    page_title="Baby's First Flight",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Cormorant Garamond', Georgia, serif;
}

.main { background: linear-gradient(145deg, #FDFAF4 0%, #F7F2EA 40%, #EAF2EA 100%); }

.block-container { padding-top: 0 !important; max-width: 1200px; }

.header-bar {
    background: #2C3E35;
    padding: 18px 32px;
    margin: -1rem -1rem 1.5rem -1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-radius: 0;
}

.header-title { font-size: 22px; font-weight: 500; color: #FDFAF4; }
.header-sub { font-size: 11px; color: #B8C4CC; font-family: 'DM Mono', monospace; letter-spacing: 0.07em; margin-top: 2px; }
.header-links { display: flex; gap: 10px; align-items: center; }

.kpi-card {
    background: white;
    border-radius: 14px;
    padding: 18px 20px;
    border: 0.5px solid rgba(0,0,0,0.1);
    box-shadow: 0 1px 8px rgba(74,124,89,0.05);
    height: 100%;
}
.kpi-label { font-size: 11px; font-family: 'DM Mono', monospace; color: #9CA3AF; letter-spacing: 0.07em; text-transform: uppercase; margin-bottom: 8px; }
.kpi-value { font-size: 48px; font-weight: 300; line-height: 1; color: #4A7C59; }
.kpi-value-blue { font-size: 48px; font-weight: 300; line-height: 1; color: #1E40AF; }
.kpi-value-amber { font-size: 48px; font-weight: 300; line-height: 1; color: #B5860A; }
.kpi-sub { font-size: 13px; color: #6B7280; margin-top: 5px; }

.status-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'DM Mono', monospace;
    white-space: nowrap;
}

.section-title { font-size: 16px; font-weight: 500; color: #2C3E35; margin-bottom: 12px; margin-top: 20px; }

.cat-card {
    background: white;
    border-radius: 14px;
    padding: 14px 16px;
    border: 0.5px solid rgba(0,0,0,0.1);
    cursor: pointer;
    transition: transform 0.1s;
    margin-bottom: 8px;
}
.cat-card:hover { transform: translateY(-2px); }
.cat-card-warn { background: #FFFBEB; border-color: #F0D890; }

.idea-card {
    background: white;
    border-radius: 14px;
    padding: 16px 18px;
    border: 0.5px solid rgba(0,0,0,0.1);
    box-shadow: 0 1px 8px rgba(74,124,89,0.05);
    margin-bottom: 12px;
}

.idea-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 0;
    border-top: 0.5px solid rgba(0,0,0,0.07);
}

.vote-score-pos { color: #4A7C59; font-weight: 600; font-family: 'DM Mono', monospace; }
.vote-score-neg { color: #B91C1C; font-weight: 600; font-family: 'DM Mono', monospace; }
.vote-score-neu { color: #9CA3AF; font-family: 'DM Mono', monospace; }

div[data-testid="stHorizontalBlock"] { gap: 0.5rem; }

/* Make tab styling cleaner */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.5);
    border-radius: 10px;
    padding: 3px;
    border: 0.5px solid rgba(0,0,0,0.08);
    gap: 3px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 14px;
}
.stTabs [aria-selected="true"] {
    background: #2C3E35 !important;
    color: #FDFAF4 !important;
}

/* Table styling */
.dataframe { font-family: 'DM Mono', monospace; font-size: 12px; }

/* Hide streamlit branding */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* Progress bar */
.prog-bar-bg {
    height: 4px;
    background: rgba(0,0,0,0.07);
    border-radius: 2px;
    margin-top: 10px;
    overflow: hidden;
}
.prog-bar-fill {
    height: 100%;
    border-radius: 2px;
    background: #7A9E7E;
}

.pill {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
}

.splitwise-link {
    background: rgba(122,158,126,0.2);
    border: 1px solid rgba(122,158,126,0.35);
    border-radius: 20px;
    padding: 6px 16px;
    color: #C8DCC8;
    text-decoration: none;
    font-size: 12px;
    font-family: 'DM Mono', monospace;
}

stProgress > div > div { background: #7A9E7E !important; }
</style>
""", unsafe_allow_html=True)


# DATA LOADING
@st.cache_data(ttl=60)
def load_sheet():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Master%20Tracker"
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        # Find actual header row — look for "Category" column
        if "Category" not in df.columns:
            # Try skipping rows to find real header
            for skip in range(1, 5):
                df2 = pd.read_csv(io.StringIO(r.text), skiprows=skip)
                if "Category" in df2.columns:
                    df = df2
                    break
        df = df.dropna(subset=["Category"])
        df = df[df["Category"].str.strip() != "Category"]
        df = df[df["Category"].str.strip() != ""]
        # Normalize column names
        df.columns = [c.strip() for c in df.columns]
        # Rename to standard names
        rename = {}
        for col in df.columns:
            cl = col.lower()
            if "item name" in cl:       rename[col] = "Item"
            elif "description" in cl:   rename[col] = "Notes"
            elif "splitwise" in cl:     rename[col] = "Splitwise"
            elif "link" in cl and "splitwise" not in cl: rename[col] = "Link"
        df = df.rename(columns=rename)
        # Fill NaN
        for col in ["Status", "Owner", "Priority", "Notes", "Splitwise", "Link"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()
        df["Status"] = df["Status"].replace("", "Not Yet Started")
        return df, True
    except Exception as e:
        return None, False


def get_fallback():
    rows = [
        ("Venue & Logistics","Confirm venue","Apartment vs Box Cafe, Dream Vista","Completed","Jessica","High","Box Cafe JC",""),
        ("Venue & Logistics","Secure booking / reservation","Lock in date and deposits","Completed","Jessica","High","","Jessica"),
        ("Venue & Logistics","Confirm guest capacity","Headcount check against venue max","In Progress","Savitri","High","",""),
        ("Venue & Logistics","Splitwise tracking setup","Create group, add all hosts","Completed","Carly","Medium","",""),
        ("Invitations & Guest Experience","Boarding pass invite design","Digital boarding pass","Completed","Savitri","High","",""),
        ("Invitations & Guest Experience","QR code RSVP setup","QR code to RSVP form","Completed","Savitri","High","",""),
        ("Invitations & Guest Experience","Evite creation","Backup digital send","Completed","Savitri","Medium","",""),
        ("Invitations & Guest Experience","Print keepsake invites","Physical boarding pass invites","Not Yet Started","Savitri","Medium","","Savitri"),
        ("Invitations & Guest Experience","Send invites","Target: early April","Not Yet Started","Savitri","High","","Savitri"),
        ("Keepsakes & Sentimental Touches","Bookstand for Book Tree","Wooden or acrylic stand","In Progress","Savitri","","Book Tree",""),
        ("Food","Define food concept","Mini bites vs full catering","In Progress","Jessica","High","",""),
        ("Food","Incorporate pregnancy cravings","Cantaloupe, uncrustables, queso","In Progress","Jessica","High","",""),
        ("Food","Catering vs self-serve plan","Assign roles or get quotes","In Progress","Jessica","High","",""),
        ("Food","Finalize menu","Full menu locked","Not Yet Started","Jessica","High","",""),
        ("Food","Serving setup","Platters, labels, serving utensils","Not Yet Started","Savitri","Low","",""),
        ("Drinks","Define two signature drinks","Nicole + Zach inspired","Not Yet Started","","Medium","",""),
        ("Drinks","Cocktail bar format","Hugo / Aperol / mimosa bar","Not Yet Started","","Medium","",""),
        ("Drinks","Ice cube detail","Airplane or balloon silicone molds","Not Yet Started","","Medium","",""),
        ("Decor & Styling","Balloon box decision","Giant balloon box","Not Yet Started","","High","","Savitri"),
        ("Decor & Styling","Balloon bouquets (2 large)","Three large helium bouquets","Not Yet Started","","Medium","","Savitri"),
        ("Decor & Styling","Table styling direction","Elevated — no kitschy baby stuff","Not Yet Started","","High","",""),
        ("Decor & Styling","Paper plane drink markers","Paper plane drink stirrers","Not Yet Started","","Low","",""),
        ("Decor & Styling","Table cloths & confetti","Table confetti & cloths","Not Yet Started","","Medium","",""),
        ("Decor & Styling","Baby photo display","Baby photos of Gena & Brian","Not Yet Started","","High","",""),
        ("Decor & Styling","Overall palette consistency check","Final review","Not Yet Started","","Medium","",""),
        ("Activities & Games","Travel trivia — couple's story","10 Qs about Nicole + Zach","Not Yet Started","","High","",""),
        ("Activities & Games","Guess baby traits","Eye color, hair, first word","Not Yet Started","","Medium","",""),
        ("Activities & Games","Guess baby's first trip","Guests write destination","Not Yet Started","","Low","",""),
        ("Keepsakes & Sentimental Touches","Letters to Nicole (before baby)","Advice / memories to Nicole","Not Yet Started","","High","",""),
        ("Keepsakes & Sentimental Touches","Postpartum letters from women","Sealed for postpartum","Not Yet Started","","High","",""),
        ("Favors & Gifts","Travel-themed gift bags","Travel kit, personalized tag","Not Yet Started","","Medium","",""),
    ]
    df = pd.DataFrame(rows, columns=["Category","Item","Notes","Status","Owner","Priority","Link","Splitwise"])
    return df


# SESSION STATE for ideas and votes
if "ideas" not in st.session_state:
    st.session_state.ideas = {k: list(v) for k, v in SEED_IDEAS.items()}
if "next_id" not in st.session_state:
    st.session_state.next_id = 100
if "voted" not in st.session_state:
    st.session_state.voted = {}  # idea_key -> "up"|"down"|None


# HEADER
st.markdown(f"""
<div class="header-bar">
  <div>
    <div class="header-title">✈️ &nbsp; Baby's First Flight</div>
    <div class="header-sub">JESSICA &nbsp;·&nbsp; CARLY &nbsp;·&nbsp; KIRSTEN &nbsp;·&nbsp; SAVITRI</div>
  </div>
  <div class="header-links">
    <a href="{SPLITWISE_URL}" target="_blank" class="splitwise-link">💸 &nbsp; Splitwise</a>
  </div>
</div>
""", unsafe_allow_html=True)


# LOAD DATA
df, live = load_sheet()
if df is None:
    df = get_fallback()
    st.warning("⚠️ Sheet not publicly accessible — showing last known data. Go to **File → Share → Anyone with link → Viewer** in your Google Sheet to enable live sync.", icon="⚠️")
else:
    st.caption(f"✓ Live from Google Sheet · refreshes every 60s · {len(df)} items loaded")


# HELPER: colored badge HTML
def status_badge(s):
    bg = STATUS_COLORS.get(s, "#F3F4F6")
    fg = STATUS_TEXT.get(s, "#374151")
    return f'<span class="status-badge" style="background:{bg};color:{fg}">{s}</span>'

def priority_pill(p):
    if not p:
        return ""
    bg, fg = PRIORITY_COLORS.get(p, ("#F3F4F6", "#374151"))
    return f'<span class="pill" style="background:{bg};color:{fg}">{p}</span>'

def owner_pill(o):
    if not o:
        return '<span style="color:#9CA3AF;font-size:12px">—</span>'
    bg, fg = OWNER_COLORS.get(o, ("#F3F4F6", "#555"))
    return f'<span class="pill" style="background:{bg};color:{fg}">{o}</span>'

def check_icon(status):
    if status == "Completed":
        return "✅"
    elif status == "In Progress":
        return "🔵"
    return "⬜"


# TABS
tab1, tab2, tab3 = st.tabs(["📋 Overview", "✅ Tasks", "💡 Ideas board"])


# ═══ TAB 1: OVERVIEW ═══
with tab1:
    total     = len(df)
    done      = len(df[df["Status"] == "Completed"])
    in_prog   = len(df[df["Status"] == "In Progress"])
    high_open = df[(df["Status"] != "Completed") & (df["Priority"] == "High")]

    # KPIs
    c1, c2, c3 = st.columns(3)
    with c1:
        pct = int(done / total * 100) if total else 0
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-label">Tasks done</div>
          <div class="kpi-value">{done}</div>
          <div class="kpi-sub">of {total} total items</div>
          <div class="prog-bar-bg"><div class="prog-bar-fill" style="width:{pct}%"></div></div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-label">In progress</div>
          <div class="kpi-value-blue">{in_prog}</div>
          <div class="kpi-sub">items actively in motion</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        warn_bg = "#FFFBEB" if len(high_open) > 0 else "white"
        warn_border = "#F0D890" if len(high_open) > 0 else "rgba(0,0,0,0.1)"
        tags_html = ""
        for _, row in high_open.head(3).iterrows():
            label = row["Item"][:22] + "…" if len(row["Item"]) > 22 else row["Item"]
            tags_html += f'<span style="font-size:10px;background:rgba(255,255,255,0.7);padding:2px 8px;border-radius:8px;color:#8a6500;border:0.5px solid #F0D890;margin-right:4px">{label}</span>'
        st.markdown(f"""
        <div class="kpi-card" style="background:{warn_bg};border-color:{warn_border}">
          <div class="kpi-label" style="color:{'#B5860A' if len(high_open)>0 else '#9CA3AF'}">High priority open</div>
          <div class="kpi-value-amber">{len(high_open)}</div>
          <div class="kpi-sub" style="color:#9A7200">need attention before event</div>
          <div style="margin-top:10px">{tags_html}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Status bar
    status_order = ["Completed", "In Progress", "Not Yet Started", "Considering"]
    bar_colors   = {"Completed": "#7A9E7E", "In Progress": "#60A5FA", "Not Yet Started": "#D1D5DB", "Considering": "#FBBF24"}
    counts = df["Status"].value_counts().to_dict()

    bar_html = '<div style="display:flex;border-radius:4px;overflow:hidden;height:10px;margin:12px 0">'
    for s in status_order:
        n = counts.get(s, 0)
        if n > 0:
            pct = n / total * 100
            bar_html += f'<div title="{s}: {n}" style="flex:{pct};background:{bar_colors[s]};border-left:1px solid rgba(255,255,255,0.4)"></div>'
    bar_html += "</div>"

    legend_html = '<div style="display:flex;flex-wrap:wrap;gap:14px;margin-top:8px">'
    for s in status_order:
        n = counts.get(s, 0)
        legend_html += f'<div style="display:flex;align-items:center;gap:5px"><div style="width:10px;height:10px;border-radius:2px;background:{bar_colors[s]}"></div><span style="font-size:12px;color:#6B7280;font-family:\'DM Mono\',monospace">{s} <strong style="color:#1F2937">{n}</strong></span></div>'
    legend_html += "</div>"

    st.markdown(f"""
    <div class="kpi-card" style="margin-bottom:16px">
      <div class="kpi-label">Status overview</div>
      {bar_html}{legend_html}
    </div>""", unsafe_allow_html=True)

    # ── Session state for selected category drilldown ────────────────────────
    if "selected_cat" not in st.session_state:
        st.session_state.selected_cat = None

    st.markdown('<div class="section-title">Categories — click any to see details</div>', unsafe_allow_html=True)

    cats = [c for c in CAT_ICONS.keys() if c in df["Category"].values]
    rows_of_cats = [cats[i:i+3] for i in range(0, len(cats), 3)]

    for row in rows_of_cats:
        cols = st.columns(3)
        for ci, cat in enumerate(row):
            cat_df    = df[df["Category"] == cat]
            cat_done  = len(cat_df[cat_df["Status"] == "Completed"])
            cat_total = len(cat_df)
            cat_high  = len(cat_df[(cat_df["Status"] != "Completed") & (cat_df["Priority"] == "High")])
            icon      = CAT_ICONS.get(cat, "📌")
            pct_cat   = int(cat_done / cat_total * 100) if cat_total else 0
            warn_card = cat_high > 0
            filled    = int(pct_cat / 10)
            bar_str   = "█" * filled + "░" * (10 - filled)
            warn_str  = f"\n⚠ {cat_high} high priority open" if warn_card else ""
            btn_label = f"{icon}  {cat}{warn_str}\n{bar_str}  {cat_done}/{cat_total}"

            with cols[ci]:
                if st.button(btn_label, key=f"cat_btn_{cat}", use_container_width=True):
                    if st.session_state.selected_cat == cat:
                        st.session_state.selected_cat = None
                    else:
                        st.session_state.selected_cat = cat
                    st.rerun()

    # ── Inline drilldown table ────────────────────────────────────────────────
    if st.session_state.selected_cat:
        sel_cat  = st.session_state.selected_cat
        sel_icon = CAT_ICONS.get(sel_cat, "📌")
        sel_df   = df[df["Category"] == sel_cat].copy()

        st.markdown("<br>", unsafe_allow_html=True)

        hdr_col, close_col = st.columns([8, 1])
        with hdr_col:
            n_done = len(sel_df[sel_df["Status"] == "Completed"])
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">'
                f'<span style="font-size:24px">{sel_icon}</span>'
                f'<span style="font-size:18px;font-weight:500;color:#2C3E35">{sel_cat}</span>'
                f'<span style="font-size:12px;color:#9CA3AF;font-family:monospace;margin-left:8px">'
                f'{n_done}/{len(sel_df)} done</span></div>',
                unsafe_allow_html=True,
            )
        with close_col:
            if st.button("✕ Close", key="close_drilldown"):
                st.session_state.selected_cat = None
                st.rerun()

        rows_html = ""
        for _, row in sel_df.iterrows():
            status = str(row.get("Status", ""))
            owner  = str(row.get("Owner", ""))
            prio   = str(row.get("Priority", ""))
            item   = str(row.get("Item", ""))
            notes  = str(row.get("Notes", ""))
            sw     = str(row.get("Splitwise", ""))
            link   = str(row.get("Link", ""))

            chk = check_icon(status)
            item_html = (f'<a href="{link}" target="_blank" style="color:#4A7C59;text-decoration:none">{item} ↗</a>'
                         if link.startswith("http") else item)
            if link and not link.startswith("http"):
                item_html += f'<div style="font-size:10px;color:#9CA3AF;font-family:monospace;margin-top:2px">{link}</div>'

            strike = "text-decoration:line-through;opacity:0.55;" if status == "Completed" else ""
            row_bg = ("rgba(209,250,229,0.2)" if status == "Completed" else
                      "rgba(255,248,225,0.45)" if prio == "High" and status != "Completed" else "#fff")

            rows_html += (
                f'<tr style="background:{row_bg};border-top:0.5px solid rgba(0,0,0,0.07)">'
                f'<td style="padding:10px 12px;width:30px">{chk}</td>'
                f'<td style="padding:10px 12px;font-weight:500;{strike}max-width:200px">{item_html}</td>'
                f'<td style="padding:10px 12px;color:#6B7280;font-size:12px;max-width:220px">{notes or "—"}</td>'
                f'<td style="padding:10px 12px">{status_badge(status)}</td>'
                f'<td style="padding:10px 12px">{owner_pill(owner)}</td>'
                f'<td style="padding:10px 12px">{priority_pill(prio)}</td>'
                f'<td style="padding:10px 12px;font-size:11px;font-family:monospace;'
                f'color:{"#4A7C59" if sw else "#D1D5DB"}">{sw or "—"}</td>'
                f'</tr>'
            )

        def th(label):
            return (f'<th style="padding:9px 12px;text-align:left;font-size:11px;font-family:monospace;'
                    f'color:#9CA3AF;letter-spacing:0.05em;text-transform:uppercase;font-weight:400;'
                    f'background:rgba(0,0,0,0.02);border-bottom:0.5px solid rgba(0,0,0,0.08)">{label}</th>')

        table_html = (
            f'<div style="background:white;border-radius:14px;border:0.5px solid rgba(0,0,0,0.1);'
            f'overflow:hidden;box-shadow:0 1px 8px rgba(74,124,89,0.05)">'
            f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
            f'<thead><tr>{th("")}{th("Item")}{th("Notes")}{th("Status")}{th("Owner")}{th("Priority")}{th("Splitwise")}</tr></thead>'
            f'<tbody>{rows_html}</tbody></table></div>'
        )
        st.markdown(table_html, unsafe_allow_html=True)


# ═══ TAB 2: TASKS ═══
with tab2:
    col_f1, col_f2, col_f3 = st.columns([2, 2, 2])

    all_cats    = ["All"] + sorted(df["Category"].dropna().unique().tolist())
    all_owners  = ["All"] + sorted([o for o in df["Owner"].dropna().unique().tolist() if o])
    all_statuses = ["All", "Completed", "In Progress", "Not Yet Started", "Considering"]

    with col_f1:
        cat_filter = st.selectbox("Category", all_cats, key="cat_f")
    with col_f2:
        owner_filter = st.selectbox("Owner", all_owners, key="owner_f")
    with col_f3:
        status_filter = st.selectbox("Status", all_statuses, key="status_f")

    filtered = df.copy()
    if cat_filter != "All":
        filtered = filtered[filtered["Category"] == cat_filter]
    if owner_filter != "All":
        filtered = filtered[filtered["Owner"] == owner_filter]
    if status_filter != "All":
        filtered = filtered[filtered["Status"] == status_filter]

    st.caption(f"{len(filtered)} items")

    if len(filtered) == 0:
        st.info("No items match the selected filters.")
    else:
        # Render as HTML table for full styling control
        rows_html = ""
        for _, row in filtered.iterrows():
            status  = str(row.get("Status", ""))
            owner   = str(row.get("Owner", ""))
            prio    = str(row.get("Priority", ""))
            item    = str(row.get("Item", ""))
            notes   = str(row.get("Notes", ""))
            sw      = str(row.get("Splitwise", ""))
            link    = str(row.get("Link", ""))

            check = check_icon(status)
            item_html = f'<a href="{link}" target="_blank" style="color:#4A7C59;text-decoration:none">{item} ↗</a>' if link.startswith("http") else item
            if link and not link.startswith("http"):
                item_html += f'<div style="font-size:10px;color:#9CA3AF;font-family:\'DM Mono\',monospace;margin-top:2px">{link}</div>'

            strikethrough = "text-decoration:line-through;opacity:0.5;" if status == "Completed" else ""
            row_bg = "rgba(209,250,229,0.15)" if status == "Completed" else ("rgba(255,248,225,0.4)" if prio == "High" and status != "Completed" else "#fff")

            rows_html += f"""
            <tr style="background:{row_bg};border-top:0.5px solid rgba(0,0,0,0.07)">
              <td style="padding:10px 12px;width:30px">{check}</td>
              <td style="padding:10px 12px;font-weight:500;{strikethrough}max-width:200px">{item_html}</td>
              <td style="padding:10px 12px;color:#6B7280;font-size:12px;max-width:220px">{notes or '—'}</td>
              <td style="padding:10px 12px">{status_badge(status)}</td>
              <td style="padding:10px 12px">{owner_pill(owner)}</td>
              <td style="padding:10px 12px">{priority_pill(prio)}</td>
              <td style="padding:10px 12px;font-size:11px;font-family:'DM Mono',monospace;color:{'#4A7C59' if sw else '#D1D5DB'}">{sw or '—'}</td>
            </tr>"""

        table_html = f"""
        <div style="background:white;border-radius:14px;border:0.5px solid rgba(0,0,0,0.1);overflow:hidden;box-shadow:0 1px 8px rgba(74,124,89,0.05)">
        <table style="width:100%;border-collapse:collapse;font-size:13px;font-family:'Cormorant Garamond',Georgia,serif">
          <thead style="background:rgba(0,0,0,0.02)">
            <tr>
              <th style="padding:9px 12px;text-align:left;font-size:11px;font-family:'DM Mono',monospace;color:#9CA3AF;letter-spacing:0.05em;text-transform:uppercase;font-weight:400;border-bottom:0.5px solid rgba(0,0,0,0.08);width:30px"></th>
              <th style="padding:9px 12px;text-align:left;font-size:11px;font-family:'DM Mono',monospace;color:#9CA3AF;letter-spacing:0.05em;text-transform:uppercase;font-weight:400;border-bottom:0.5px solid rgba(0,0,0,0.08)">Item</th>
              <th style="padding:9px 12px;text-align:left;font-size:11px;font-family:'DM Mono',monospace;color:#9CA3AF;letter-spacing:0.05em;text-transform:uppercase;font-weight:400;border-bottom:0.5px solid rgba(0,0,0,0.08)">Notes</th>
              <th style="padding:9px 12px;text-align:left;font-size:11px;font-family:'DM Mono',monospace;color:#9CA3AF;letter-spacing:0.05em;text-transform:uppercase;font-weight:400;border-bottom:0.5px solid rgba(0,0,0,0.08)">Status</th>
              <th style="padding:9px 12px;text-align:left;font-size:11px;font-family:'DM Mono',monospace;color:#9CA3AF;letter-spacing:0.05em;text-transform:uppercase;font-weight:400;border-bottom:0.5px solid rgba(0,0,0,0.08)">Owner</th>
              <th style="padding:9px 12px;text-align:left;font-size:11px;font-family:'DM Mono',monospace;color:#9CA3AF;letter-spacing:0.05em;text-transform:uppercase;font-weight:400;border-bottom:0.5px solid rgba(0,0,0,0.08)">Priority</th>
              <th style="padding:9px 12px;text-align:left;font-size:11px;font-family:'DM Mono',monospace;color:#9CA3AF;letter-spacing:0.05em;text-transform:uppercase;font-weight:400;border-bottom:0.5px solid rgba(0,0,0,0.08)">Splitwise owed to</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
        </div>"""
        st.markdown(table_html, unsafe_allow_html=True)


# ═══ TAB 3: IDEAS ═══
with tab3:
    st.markdown(
        '<p style="font-size:13px;color:#6B7280;margin-bottom:20px">'
        'Drop suggestions below — anyone can upvote or downvote to help the hosts decide what makes the cut.</p>',
        unsafe_allow_html=True,
    )

    col_l, col_r = st.columns(2)
    col_map = {0: col_l, 1: col_r}

    for cat_idx, (cat_key, cat_icon, cat_label) in enumerate(IDEA_CATS):
        with col_map[cat_idx % 2]:
            # ── Card header ──────────────────────────────────────────────
            st.markdown(
                f'<div style="background:white;border-radius:14px;padding:16px 18px 4px;'
                f'border:0.5px solid rgba(0,0,0,0.1);box-shadow:0 1px 8px rgba(74,124,89,0.05);margin-bottom:4px">'
                f'<div style="font-size:14px;font-weight:500;color:#2C3E35;margin-bottom:2px">'
                f'{cat_icon}&nbsp; {cat_label}</div></div>',
                unsafe_allow_html=True,
            )

            ideas_sorted = sorted(
                st.session_state.ideas.get(cat_key, []),
                key=lambda x: x.get("score", 0),
                reverse=True,
            )

            if not ideas_sorted:
                st.caption("No suggestions yet — be the first!")

            # ── Each idea row ────────────────────────────────────────────
            for idea in ideas_sorted:
                idea_id  = idea.get("id", id(idea))  # fallback to object id
                idea_uid = f"{cat_key}_{idea_id}"
                score    = idea.get("score", 0)
                voted    = st.session_state.voted.get(idea_uid)
                score_color = "#4A7C59" if score > 0 else ("#B91C1C" if score < 0 else "#9CA3AF")

                # Text + score in HTML
                st.markdown(
                    f'<div style="border-top:0.5px solid rgba(0,0,0,0.07);padding:8px 0 4px">'
                    f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">'
                    f'<div style="flex:1">'
                    f'<div style="font-size:13px;color:#1F2937;line-height:1.4">{idea["text"]}</div>'
                    f'<div style="font-size:11px;color:#9CA3AF;margin-top:2px">— {idea["author"]}</div>'
                    f'</div>'
                    f'<div style="font-size:13px;font-weight:600;color:{score_color};'
                    f'font-family:monospace;min-width:28px;text-align:right">{score:+d}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

                # Vote buttons as real Streamlit widgets
                b1, b2, b3 = st.columns([1, 1, 6])
                with b1:
                    label_up = "👍" if voted == "up" else "▲"
                    if st.button(label_up, key=f"up_{idea_uid}"):
                        for item in st.session_state.ideas[cat_key]:
                            if item.get("id", id(item)) == idea_id:
                                if voted == "up":
                                    item["score"] -= 1
                                    st.session_state.voted[idea_uid] = None
                                else:
                                    if voted == "down":
                                        item["score"] += 1
                                    item["score"] += 1
                                    st.session_state.voted[idea_uid] = "up"
                        st.rerun()
                with b2:
                    label_dn = "👎" if voted == "down" else "▼"
                    if st.button(label_dn, key=f"dn_{idea_uid}"):
                        for item in st.session_state.ideas[cat_key]:
                            if item.get("id", id(item)) == idea_id:
                                if voted == "down":
                                    item["score"] += 1
                                    st.session_state.voted[idea_uid] = None
                                else:
                                    if voted == "up":
                                        item["score"] -= 1
                                    item["score"] -= 1
                                    st.session_state.voted[idea_uid] = "down"
                        st.rerun()

            # ── Add idea form ────────────────────────────────────────────
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            with st.form(key=f"form_{cat_key}", clear_on_submit=True):
                new_text   = st.text_input("Suggestion", placeholder="Add a suggestion...", label_visibility="collapsed")
                new_author = st.text_input("Your name",  placeholder="Your name",           label_visibility="collapsed")
                if st.form_submit_button("+ Add idea"):
                    if new_text.strip():
                        nid = st.session_state.next_id
                        st.session_state.next_id += 1
                        if cat_key not in st.session_state.ideas:
                            st.session_state.ideas[cat_key] = []
                        st.session_state.ideas[cat_key].append({
                            "id":     nid,
                            "text":   new_text.strip(),
                            "author": new_author.strip() or "Anonymous",
                            "score":  0,
                        })
                        st.rerun()
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# FOOTER
st.markdown(f"""
<div style="margin-top:40px;padding-top:16px;border-top:0.5px solid #C8DCC8;display:flex;justify-content:space-between;align-items:center">
  <div style="font-size:12px;color:#9CA3AF;font-family:'DM Mono',monospace;letter-spacing:0.05em">✈️ &nbsp; BABY'S FIRST FLIGHT &nbsp;·&nbsp; SOFT GREEN · CREAM · SILVER</div>
  <a href="{SPLITWISE_URL}" target="_blank" style="font-size:12px;color:#7A9E7E;text-decoration:none;font-family:'DM Mono',monospace">💸 Open Splitwise →</a>
</div>""", unsafe_allow_html=True)
