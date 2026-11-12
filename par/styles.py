"""Broadsheet styling: CSS injected over Streamlit's defaults, plus small HTML helpers."""
from datetime import date
from html import escape
from urllib.parse import quote

import streamlit as st

PAPER = "#f5f1e8"
INK = "#1a1a1a"
MUTED = "#5c5850"
RULE = "#1a1a1a"
ACCENT = "#8b1a1a"  # oxblood, used sparingly for feedback and the streak

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Playfair+Display:ital,wght@0,600;0,800;1,600&family=UnifrakturMaguntia&display=swap');

/* ---------- page ---------- */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
    background: {PAPER};
    color: {INK};
}}
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
#MainMenu, footer, [data-testid="stStatusWidget"] {{ display: none !important; }}
.block-container, [data-testid="stMainBlockContainer"] {{
    max-width: 680px;
    padding: 1.25rem 1rem 4rem;
}}
html, body, p, li, label, input, textarea, button, [data-testid="stMarkdownContainer"] {{
    font-family: 'Libre Baskerville', Georgia, serif;
}}
p, li {{ color: {INK}; }}
h1, h2, h3, h4 {{ font-family: 'Playfair Display', Georgia, serif !important; color: {INK} !important; }}
a {{ color: {INK}; text-decoration: underline; text-underline-offset: 2px; }}
hr {{ border: none; border-top: 1px solid {RULE}; margin: 1.1rem 0; }}

/* ---------- masthead ---------- */
.masthead {{ text-align: center; border-bottom: 3px double {RULE}; padding-bottom: .4rem; margin-bottom: .5rem; }}
.masthead .name {{
    font-family: 'UnifrakturMaguntia', serif; font-size: 4.2rem; line-height: 1; margin: 0;
    color: {INK};
}}
.masthead .motto {{ font-style: italic; font-size: .78rem; color: {MUTED}; margin-top: .15rem; }}
.dateline {{
    display: flex; justify-content: space-between; flex-wrap: wrap; gap: .25rem;
    font-size: .72rem; letter-spacing: .06em; text-transform: uppercase;
    border-bottom: 1px solid {RULE}; padding: .3rem 0; margin-bottom: .6rem;
}}
.dateline .streak {{ color: {ACCENT}; font-weight: 700; }}

/* ---------- story cards ---------- */
.kicker {{
    font-size: .68rem; letter-spacing: .14em; text-transform: uppercase; color: {ACCENT};
    font-weight: 700; margin: .2rem 0;
}}
.lead img, .lead .ph {{ width: 100%; aspect-ratio: 16 / 9; object-fit: cover; display: block; border: 1px solid {RULE}; }}
.lead h1 {{ font-size: 2.1rem !important; line-height: 1.15; margin: .5rem 0 .4rem; padding: 0; font-weight: 800; }}
.lead .trail {{ font-size: 1rem; line-height: 1.6; color: {MUTED}; }}
.story {{ display: flex; gap: .9rem; align-items: flex-start; }}
.story img, .story .ph {{ width: 132px; min-width: 132px; aspect-ratio: 4 / 3; object-fit: cover; border: 1px solid {RULE}; }}
.story h3 {{ font-size: 1.12rem !important; line-height: 1.25; margin: 0 0 .25rem; padding: 0; font-weight: 600; }}
.story .trail {{ font-size: .82rem; line-height: 1.5; color: {MUTED}; margin: 0; }}
.section-label {{
    font-family: 'Playfair Display', serif; font-weight: 800; font-size: .85rem; letter-spacing: .18em;
    text-transform: uppercase; text-align: center; border-top: 1px solid {RULE}; border-bottom: 1px solid {RULE};
    padding: .3rem 0; margin: 1.2rem 0 .8rem;
}}
.read-badge {{ font-size: .68rem; letter-spacing: .1em; text-transform: uppercase; color: {MUTED}; }}

/* ---------- reader ---------- */
.reader-head h1 {{ font-size: 2.2rem !important; line-height: 1.15; font-weight: 800; margin: .3rem 0 .5rem; padding: 0; }}
.reader-head img, .reader-head .ph {{ width: 100%; aspect-ratio: 16 / 9; object-fit: cover; border: 1px solid {RULE}; display: block; }}
.byline {{ font-size: .75rem; color: {MUTED}; letter-spacing: .05em; text-transform: uppercase; margin-bottom: .8rem; }}
.overview {{
    border-top: 2px solid {RULE}; border-bottom: 1px solid {RULE}; padding: .7rem 0; margin: 1rem 0 1.2rem;
}}
.overview .label {{ font-size: .65rem; letter-spacing: .16em; text-transform: uppercase; font-weight: 700; color: {MUTED}; }}
.overview p {{ font-style: italic; font-size: 1.08rem; line-height: 1.55; margin: .25rem 0 0; }}
.article-body p {{ font-size: 1.03rem; line-height: 1.8; margin: 0 0 1.05rem; text-align: left; }}
.article-body p:first-child::first-letter {{
    font-family: 'Playfair Display', serif; float: left; font-size: 3.4rem; line-height: .9;
    padding: .25rem .4rem 0 0; font-weight: 800;
}}
.sec-head {{ display: flex; align-items: center; gap: .6rem; margin: 1.6rem 0 .9rem; }}
.sec-head .num {{ font-family: 'Playfair Display', serif; font-weight: 800; font-size: 1.3rem; }}
.sec-head .line {{ flex: 1; border-top: 1px solid {RULE}; }}
.sec-head .of {{ font-size: .68rem; letter-spacing: .14em; text-transform: uppercase; color: {MUTED}; }}
.quiz-label {{ font-size: .65rem; letter-spacing: .16em; text-transform: uppercase; font-weight: 700; margin-bottom: .2rem; }}
.quiz-q {{ font-family: 'Playfair Display', serif; font-weight: 600; font-size: 1.12rem; line-height: 1.35; margin: 0 0 .3rem; }}
.verdict {{ border-left: 3px solid {INK}; padding: .45rem .75rem; margin: .4rem 0 1rem; font-size: .9rem; line-height: 1.55; background: rgba(0,0,0,.025); }}
.verdict.wrong {{ border-left-color: {ACCENT}; }}
.verdict b {{ letter-spacing: .04em; }}
.feedback-box {{ border: 1px solid {RULE}; padding: .9rem 1rem; margin: .8rem 0; line-height: 1.65; font-size: .95rem; }}
.concept-tag {{
    display: inline-block; border: 1px solid {INK}; padding: .1rem .5rem; margin: 0 .3rem .3rem 0;
    font-size: .7rem; letter-spacing: .08em; text-transform: uppercase;
}}

/* ---------- concepts ---------- */
.concept-row {{ padding: .7rem 0; border-bottom: 1px solid {RULE}; }}
.concept-row .top {{ display: flex; justify-content: space-between; align-items: baseline; gap: .5rem; }}
.concept-row .name {{ font-family: 'Playfair Display', serif; font-weight: 600; font-size: 1.15rem; }}
.concept-row .level {{ font-size: .7rem; letter-spacing: .12em; text-transform: uppercase; color: {MUTED}; white-space: nowrap; }}
.bar {{ height: 6px; border: 1px solid {INK}; margin: .4rem 0 .35rem; background: transparent; }}
.bar span {{ display: block; height: 100%; background: {INK}; }}
.concept-row .taught {{ font-size: .8rem; color: {MUTED}; line-height: 1.5; }}
.muted {{ color: {MUTED}; font-size: .85rem; }}

/* ---------- widgets ---------- */
.stButton > button, .stFormSubmitButton > button, .stLinkButton > a {{
    border-radius: 0 !important; border: 1px solid {INK} !important; background: transparent !important;
    color: {INK} !important; font-family: 'Libre Baskerville', serif !important; font-size: .8rem !important;
    letter-spacing: .05em; box-shadow: none !important;
}}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stLinkButton > a:hover {{
    background: {INK} !important; color: {PAPER} !important;
}}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primaryFormSubmit"] {{
    background: {INK} !important; color: {PAPER} !important;
}}
.stButton > button[kind="tertiary"] {{
    border: none !important; padding: 0 !important; min-height: 0 !important; text-decoration: underline;
    text-underline-offset: 3px; font-size: .78rem !important;
}}
.stButton > button[kind="tertiary"] {{ justify-content: flex-start; text-align: left; }}
.stButton > button[kind="tertiary"] p {{ text-align: left; }}
.stButton > button[kind="tertiary"]:hover {{ background: transparent !important; color: {ACCENT} !important; }}
.stButton > button p, .stFormSubmitButton > button p {{ font-family: inherit; color: inherit; }}
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="base-input"] {{
    border-radius: 0 !important; background: #fbf9f3 !important; border-color: {INK} !important;
}}
textarea, input {{ color: {INK} !important; }}
[data-testid="stForm"] {{ border: 1px solid {RULE}; border-radius: 0; padding: 1rem 1.1rem; }}
[data-baseweb="tab-list"] {{ gap: 1.2rem; border-bottom: 1px solid {RULE}; }}
[data-baseweb="tab"] {{ font-family: 'Playfair Display', serif !important; background: transparent !important; padding-left: 0; padding-right: 0; }}
[data-baseweb="tab"] p {{ font-family: 'Playfair Display', serif; font-weight: 600; font-size: .95rem; }}
[data-baseweb="tab-highlight"] {{ background: {INK} !important; }}
[data-baseweb="tab-border"] {{ display: none; }}
[data-testid="stRadio"] label p {{ font-size: .93rem; line-height: 1.45; }}
[data-testid="stAlert"], [data-testid="stAlertContainer"] {{ border-radius: 0 !important; background: #eee8da !important; }}
[data-testid="stAlert"] {{ border: 1px solid {RULE}; }}
[data-testid="stAlertContainer"] svg {{ display: none; }}

/* nav: keep the four buttons on one row, even on phones */
.st-key-nav [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: .4rem !important; }}
.st-key-nav [data-testid="stColumn"] {{ min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }}
.st-key-nav button {{ min-height: 2rem !important; padding: .2rem .3rem !important; }}
.st-key-nav button p {{ font-size: .74rem !important; white-space: nowrap; }}
[data-testid="stAlert"] p {{ font-size: .82rem; color: {INK}; }}
[data-testid="stPills"] button {{ border-radius: 0 !important; font-family: 'Libre Baskerville', serif; }}
[data-testid="stPills"] button[kind="pillsActive"] {{ background: {INK} !important; color: {PAPER} !important; border-color: {INK} !important; }}
[data-testid="stPills"] button[kind="pillsActive"] p {{ color: {PAPER} !important; }}

@media (max-width: 520px) {{
    .masthead .name {{ font-size: 3.2rem; }}
    .lead h1, .reader-head h1 {{ font-size: 1.65rem !important; }}
    .story img, .story .ph {{ width: 96px; min-width: 96px; }}
    .story h3 {{ font-size: 1rem !important; }}
    .story .trail {{ display: none; }}
}}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def placeholder_src(label):
    """An engraving-style crosshatch SVG for stories without a photo."""
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 225'>
<defs><pattern id='h' width='7' height='7' patternUnits='userSpaceOnUse' patternTransform='rotate(45)'>
<line x1='0' y1='0' x2='0' y2='7' stroke='#1a1a1a' stroke-width='0.7' opacity='0.35'/></pattern></defs>
<rect width='400' height='225' fill='#e6dfcf'/><rect width='400' height='225' fill='url(#h)'/>
<rect x='110' y='88' width='180' height='50' fill='#f5f1e8' stroke='#1a1a1a'/>
<text x='200' y='119' font-family='Georgia, serif' font-size='15' letter-spacing='3' text-anchor='middle' fill='#1a1a1a'>{escape(label.upper())}</text>
</svg>"""
    return "data:image/svg+xml;utf8," + quote(svg)


def image_tag(url, label="Par"):
    src = url or placeholder_src(label)
    return f'<img src="{escape(src, quote=True)}" alt="" loading="lazy">'


def masthead(stats=None):
    d = date.today()
    today = f"{d:%A, %B} {d.day}, {d.year}"
    html('<div class="masthead"><div class="name">Par</div>'
         '<div class="motto">The daily finance reader for students</div></div>')
    if stats is not None:
        streak = stats["streak"]
        streak_txt = f"{streak}-day streak" if streak else "Start your streak today"
        html(f'<div class="dateline"><span>{today}</span>'
             f'<span class="streak">{streak_txt}</span>'
             f'<span>{stats["articles_read"]} read</span></div>')


def kicker_for(article):
    return "Sample edition" if article["id"].startswith("sample/") else "Business"
