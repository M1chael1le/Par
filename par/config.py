"""App-wide constants and secret lookup."""
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Par"
DB_PATH = os.getenv("PAR_DB_PATH") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "par.db"
)

CLAUDE_MODEL = "claude-opus-5-5"
GUARDIAN_URL = "https://content.guardianapis.com/search"
GUARDIAN_SECTIONS = "business|money"
FEED_TTL_MINUTES = 30
MAX_TOPICS = 3

# Topic -> Guardian search query (searched within the business/money sections).
TOPICS = {
    "Markets": '"stock market" OR stocks OR shares OR "Wall Street" OR FTSE',
    "Fed & Rates": '"Federal Reserve" OR "interest rates" OR "Bank of England" OR "central bank"',
    "M&A & Deals": "merger OR acquisition OR takeover OR buyout",
    "Tech & AI": '"artificial intelligence" OR AI OR Nvidia OR "tech stocks"',
    "Economy & Policy": "inflation OR GDP OR tariffs OR recession OR budget",
    "Crypto": "bitcoin OR crypto OR cryptocurrency OR stablecoin",
}

# Fixed vocabulary so concepts recur across articles.
CONCEPTS = [
    "Interest rates",
    "Inflation",
    "Central banks",
    "Bond yields",
    "Tariffs & trade",
    "Earnings expectations",
    "Stock valuation",
    "Mergers & acquisitions",
    "IPOs",
    "Antitrust & regulation",
    "Exchange rates",
    "Commodities & oil",
    "Labor market",
    "GDP & growth",
    "Recession risk",
    "Consumer spending",
    "Government debt & deficits",
    "Corporate debt",
    "Cryptocurrency",
    "Tech & AI investment",
    "Housing market",
    "Supply chains",
]

MASTERY_PER_CORRECT = 10
MASTERY_LEVELS = [(0, "Novice"), (30, "Familiar"), (60, "Proficient"), (90, "Mastered")]


def get_secret(name):
    """st.secrets (Streamlit Cloud) first, then environment / .env."""
    try:
        if name in st.secrets:
            return st.secrets[name] or None
    except Exception:
        pass  # no secrets.toml present
    return os.getenv(name) or None


def mastery_level(score):
    label = MASTERY_LEVELS[0][1]
    for threshold, name in MASTERY_LEVELS:
        if score >= threshold:
            label = name
    return label
