# Par: the daily finance reader for students

Par is like Duolingo for finance news. Each day you read a real business story from the Guardian, split into three sections. After each section you answer a couple of questions with instant feedback. At the end you write the takeaway in your own words and get AI feedback. Every article teaches 2–3 recurring finance concepts (interest rates, earnings expectations, M&A and so on), and your mastery of each one builds over time. A daily streak keeps the habit going.

Built with Python, Streamlit, SQLite, the Guardian Open Platform API and the Anthropic API (Claude).

## Features

- **Accounts.** Username and password, stored in SQLite as salted PBKDF2-SHA256 hashes.
- **Onboarding.** Pick up to 3 topics: Markets, Fed & Rates, M&A & Deals, Tech & AI, Economy & Policy, Crypto.
- **Today.** A lead story with a large image, today's top finance stories, and a tab for each of your topics. The streak and articles-read count sit in the masthead.
- **Reader.** A one-sentence AI overview, then the **original article text**, unedited, in 3 sections. The next section unlocks after you answer that section's questions. There's a link to the full article on the Guardian.
- **In your own words.** You write a 2–3 sentence takeaway and get short feedback from Claude on accuracy and anything you missed.
- **Concepts.** Each concept's mastery (0–100, from Novice to Mastered) and the articles that taught it. Each correct first-try answer adds 10 to every concept the article covers.
- **Always runs.** Without API keys, or if an API call fails, the app shows a clear notice and falls back to 3 bundled sample articles. These come with ready-made sections, quizzes and concepts.

### How the article is split without rewriting it

Claude gets the article as numbered paragraphs and returns only the **paragraph numbers** where sections 2 and 3 begin. The app then slices the original paragraphs itself, so the body text you read never passes through the model's output. In the same structured-JSON call, Claude also writes the overview and the quiz, and tags concepts from a fixed list of 22, so concepts recur across articles. Results are cached in SQLite, so each article is processed once and shared by all users.

## Project structure

```
app.py                 entry point: page config, CSS, session-state router, nav
par/config.py          constants, topics, concept vocabulary, secret lookup
par/db.py              SQLite schema and queries
par/auth.py            password hashing, sign up / sign in
par/news.py            Guardian client, HTML → paragraphs, feed cache, fallbacks
par/ai.py              Claude calls (analysis + takeaway feedback)
par/processing.py      cache → sample → Claude → plain-reading fallback
par/progress.py        streaks, answers, mastery
par/styles.py          newspaper CSS and HTML helpers
par/sample_data.py     3 bundled demo articles (fictional companies)
views/                 login, onboarding, today, reader, concepts
```

## Run locally

You need **Python 3.10 or newer**. The Anthropic SDK and recent Streamlit releases don't support 3.9, which is what macOS ships with.

```bash
# macOS: install a newer Python if you need one
brew install python@3.12

cd Par
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # then paste in your keys (optional)
streamlit run app.py
```

The app opens at http://localhost:8501. Click **Create account** to get started.

### API keys (both optional)

| Key | Where to get it | Without it |
|---|---|---|
| `GUARDIAN_API_KEY` | Free developer key at https://open-platform.theguardian.com/access/ | Sample articles only |
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/ | Guardian articles are readable but have no overview, quiz, concepts or feedback. Sample articles still work fully. |

You can provide keys in `.env` or in `.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`). If a key is in both, `st.secrets` wins.

## Deploy to Streamlit Community Cloud

1. Push this folder to a GitHub repository. `.gitignore` already keeps `.env`, `secrets.toml` and the database out of it.
2. Go to https://share.streamlit.io, sign in with GitHub, and click **Create app**.
3. Choose your repo and branch, and set **Main file path** to `app.py`.
4. Open **Advanced settings**:
   - Set **Python version** to 3.12.
   - Paste your keys into **Secrets**:
     ```toml
     GUARDIAN_API_KEY = "..."
     ANTHROPIC_API_KEY = "sk-ant-..."
     ```
5. Click **Deploy**. Later changes to the secrets take effect within a minute, without redeploying.

> **Note on storage:** Community Cloud's filesystem is temporary. The SQLite database (`par.db`) resets whenever the app restarts or sleeps, which wipes accounts, progress and the article cache. That's fine for a class demo. To keep data, point `db.py` at a hosted database. You can also set `PAR_DB_PATH` to change where the SQLite file is stored.

## Notes

- Claude model: `claude-opus-5-5` at `low` effort for fast, inexpensive analysis (set in `par/config.py`).
- Guardian results come from the `business` and `money` sections only, filtered to standard articles, and refresh at most every 30 minutes per feed.
- Companies in the sample articles are fictional.
