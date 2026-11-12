"""Claude calls: article analysis (overview, section breaks, quiz, concepts) and takeaway feedback."""
import json

import anthropic

from par.config import CLAUDE_MODEL, CONCEPTS, get_secret


class AIError(Exception):
    """User-presentable failure from the AI service."""


def has_ai_key():
    return bool(get_secret("ANTHROPIC_API_KEY"))


def _client():
    return anthropic.Anthropic(api_key=get_secret("ANTHROPIC_API_KEY"), timeout=90, max_retries=2)


ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "overview": {"type": "string"},
        "section_starts": {"type": "array", "items": {"type": "integer"}},
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section": {"type": "integer"},
                    "question": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "answer_index": {"type": "integer"},
                    "explanation": {"type": "string"},
                },
                "required": ["section", "question", "options", "answer_index", "explanation"],
                "additionalProperties": False,
            },
        },
        "concepts": {"type": "array", "items": {"type": "string", "enum": CONCEPTS}},
    },
    "required": ["overview", "section_starts", "questions", "concepts"],
    "additionalProperties": False,
}

ANALYSIS_SYSTEM = """You help college students build financial literacy by reading real finance news.
You never rewrite or summarize the article body for display; the app shows the original paragraphs.
Your job is to add a study layer on top of the article."""

ANALYSIS_PROMPT = """Below is a news article split into numbered paragraphs.

Produce:
1. overview: ONE plain-English sentence (max 30 words) saying what happened and why it matters.
2. section_starts: exactly two paragraph numbers where section 2 and section 3 begin, splitting the
   article into three coherent, roughly even sections. Each section must contain at least one paragraph.
3. questions: 1-2 multiple-choice questions per section ("section" is 0, 1 or 2). Each has exactly
   4 options, one correct answer (answer_index 0-3), and a one-sentence explanation. Questions must be
   answerable from that section's text and should test the finance concept behind the news
   (why markets reacted, what a term means, cause and effect), not trivia like exact dates.
   Vary the position of the correct answer.
4. concepts: the 2-3 finance concepts from the allowed list that this article best teaches.

Title: {title}

{numbered}"""

FEEDBACK_PROMPT = """A college student just read this finance article and wrote a takeaway in their own words.

Article title: {title}

Article:
{body}

Student's takeaway:
\"\"\"{takeaway}\"\"\"

Reply in 3-4 short sentences, speaking directly to the student ("you"):
- Say what they got right and flag anything inaccurate.
- Name the most important point or finance concept they missed, if any.
Be warm but precise. Plain text, no headings or bullet points."""


def _call(**kwargs):
    try:
        response = _client().messages.create(model=CLAUDE_MODEL, **kwargs)
    except anthropic.AuthenticationError:
        raise AIError("the Anthropic API key was rejected")
    except anthropic.RateLimitError:
        raise AIError("the AI service is rate limited; try again in a minute")
    except anthropic.APIStatusError as e:
        raise AIError(f"the AI service returned an error ({e.status_code})")
    except anthropic.APIConnectionError:
        raise AIError("couldn't connect to the AI service")
    if response.stop_reason == "refusal":
        raise AIError("the AI declined to process this article")
    if response.stop_reason == "max_tokens":
        raise AIError("the AI response was cut off")
    text = next((b.text for b in response.content if b.type == "text"), "")
    if not text:
        raise AIError("the AI returned an empty response")
    return text


def analyze_article(title, paragraphs):
    """Returns dict(overview, breaks, questions, concepts). Raises AIError."""
    numbered = "\n\n".join(f"[{i}] {p}" for i, p in enumerate(paragraphs))
    text = _call(
        max_tokens=16000,
        system=ANALYSIS_SYSTEM,
        output_config={
            "effort": "low",
            "format": {"type": "json_schema", "schema": ANALYSIS_SCHEMA},
        },
        messages=[{"role": "user", "content": ANALYSIS_PROMPT.format(title=title, numbered=numbered)}],
    )
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise AIError("the AI returned malformed data")
    return _validate(data, len(paragraphs))


def _validate(data, n_paragraphs):
    breaks = sorted(set(int(b) for b in data.get("section_starts", [])))
    breaks = [b for b in breaks if 0 < b < n_paragraphs][:2]
    if len(breaks) != 2:
        breaks = even_breaks(n_paragraphs)

    questions, per_section = [], {0: 0, 1: 0, 2: 0}
    for q in data.get("questions", []):
        section = q.get("section")
        options = [o for o in q.get("options", []) if str(o).strip()]
        if section not in per_section or per_section[section] >= 2:
            continue
        if len(options) < 2 or not 0 <= q.get("answer_index", -1) < len(options):
            continue
        per_section[section] += 1
        questions.append({
            "section": section,
            "question": q["question"],
            "options": options,
            "answer_index": q["answer_index"],
            "explanation": q.get("explanation", ""),
        })

    concepts = list(dict.fromkeys(c for c in data.get("concepts", []) if c in CONCEPTS))[:3]
    overview = " ".join(str(data.get("overview", "")).split())
    if not overview:
        raise AIError("the AI returned no overview")
    return {"overview": overview, "breaks": breaks, "questions": questions, "concepts": concepts}


def even_breaks(n_paragraphs):
    """Fallback split into three roughly equal sections."""
    if n_paragraphs < 3:
        return [min(1, n_paragraphs), n_paragraphs]
    third = n_paragraphs / 3
    return [round(third), round(2 * third)]


def takeaway_feedback(title, paragraphs, takeaway):
    """Returns short feedback text. Raises AIError."""
    return _call(
        max_tokens=4000,
        output_config={"effort": "low"},
        messages=[{
            "role": "user",
            "content": FEEDBACK_PROMPT.format(title=title, body="\n\n".join(paragraphs), takeaway=takeaway),
        }],
    ).strip()
