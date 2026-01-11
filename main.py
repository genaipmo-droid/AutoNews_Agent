import os
import re
from datetime import datetime, timedelta

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SerpAPIWrapper
from email_sender import send_email


# -----------------------------
# Strong AI keywords
# -----------------------------
AI_KEYWORDS = [
    "ai ", " ai", "artificial intelligence",
    "genai", "generative ai",
    "machine learning", "ml model",
    "llm", "large language model",
    "chatgpt", "openai", "copilot",
    "ai model", "ai startup", "ai funding",
    "ai research", "ai mission",
    "nvidia ai", "ai chip"
]

# -----------------------------
# India relevance keywords
# -----------------------------
INDIA_KEYWORDS = [
    "india", "indian", "bharat",
    "delhi", "mumbai", "bengaluru", "bangalore",
    "hyderabad", "chennai", "pune", "kolkata",
    "startup india", "meity", "government of india",
    "ministry of electronics", "it ministry"
]


def is_ai_relevant(title, snippet):
    title = title.lower()
    snippet = snippet.lower()

    # Strong rule: title must contain AI keyword
    if any(keyword in title for keyword in AI_KEYWORDS):
        return True

    # Fallback: allow if snippet contains at least 2 AI keywords
    keyword_hits = sum(1 for kw in AI_KEYWORDS if kw in snippet)
    return keyword_hits >= 2


def is_india_relevant(title, snippet):
    text = (title + " " + snippet).lower()
    return any(word in text for word in INDIA_KEYWORDS)


# -----------------------------
# Strict recency logic
# -----------------------------
def is_recent(text, max_days=7):
    if not text:
        return False  # Missing date = reject (quality control)

    text = text.lower()

    # Relative dates: "2 days ago"
    match = re.search(r"(\d+)\s+(minute|hour|day|week)s?\s+ago", text)
    if match:
        value = int(match.group(1))
        unit = match.group(2)

        if unit in ["minute", "hour"]:
            return True
        if unit == "day":
            return value <= max_days
        if unit == "week":
            return value * 7 <= max_days

    # Absolute dates: "Jan 5, 2026"
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            dt = datetime.strptime(text.strip(), fmt)

            # Block future dates
            if dt > datetime.now():
                return False

            return datetime.now() - dt <= timedelta(days=max_days)
        except:
            pass

    # If date can't be parsed → reject for quality
    return False


# -----------------------------
# Main pipeline
# -----------------------------
def run_autonews():
    search = SerpAPIWrapper()

    query = """
    Latest AI OR "artificial intelligence" OR GenAI OR "generative AI" OR LLM OR "machine learning"
    India government startup research funding launch partnership Nvidia OpenAI
    site:thehindu.com OR site:livemint.com OR site:economictimes.com
    OR site:business-standard.com OR site:pib.gov.in OR site:indiatoday.in
    OR site:indianexpress.com OR site:hindustantimes.com
    OR site:timesofindia.indiatimes.com OR site:moneycontrol.com
    OR site:analyticsindiamag.com OR site:inc42.com
    OR site:yourstory.com OR site:techcircle.in
    """

    results = search.results(query)
    organic = results.get("organic_results", [])

    # -----------------------------
    # Strict filtering
    # -----------------------------
    selected = []

    for item in organic:
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        date_text = item.get("date", "") or snippet

        if (
            is_ai_relevant(title, snippet)
            and is_india_relevant(title, snippet)
            and is_recent(date_text)
        ):
            selected.append(item)

    # -----------------------------
    # Smart fallback (still enforces India + AI)
    # -----------------------------
    if len(selected) < 3:
        for item in organic:
            title = item.get("title", "")
            snippet = item.get("snippet", "")

            if (
                is_ai_relevant(title, snippet)
                and is_india_relevant(title, snippet)
                and item not in selected
            ):
                selected.append(item)

            if len(selected) >= 3:
                break

    selected = selected[:3]

    if not selected:
        return "<p>No high-quality India AI news found today.</p>"

    # -----------------------------
    # Prepare URLs for LLM
    # -----------------------------
    sources_text = ""
    for i, item in enumerate(selected, 1):
        sources_text += f"{i}. {item['title']}\nURL: {item['link']}\n\n"

    # -----------------------------
    # LLM formatting only
    # -----------------------------
    llm = ChatOpenAI(
        temperature=0.2,
        model="gpt-3.5-turbo",
        base_url=os.getenv("OPENAI_API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY")
    )

    prompt = f"""
You are a professional editor creating a polished email newsletter.

Format the output in clean HTML using this structure for each item:

<div style="margin-bottom:20px;">
  <h3>1. Headline here</h3>
  <ul>
    <li>Key point one</li>
    <li>Key point two</li>
  </ul>
  <p><b>Impact:</b> short impact sentence</p>
  <p>🔗 <a href="URL_HERE">Read full article</a></p>
</div>

Rules:
- Keep headlines concise
- Make key points crisp
- Use the exact same URLs
- Do NOT include markdown, only HTML body content

Articles:
{sources_text}
"""

    response = llm.invoke(prompt)
    return response.content


# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    final_news = run_autonews()
    send_email(final_news)
