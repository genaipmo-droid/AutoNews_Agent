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
# Strict recency logic (≤ 7 days only)
# -----------------------------
def is_recent(text, max_days=7):
    if not text:
        return False  # Strict: no date = reject

    text = text.lower()

    # Relative dates: "2 days ago", "5 hours ago"
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

        return False

    # Absolute dates: "Jan 5, 2026" / "January 5, 2026"
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            dt = datetime.strptime(text.strip(), fmt)

            # Reject future dates
            if dt > datetime.now():
                return False

            # Strict 7-day window
            return (datetime.now() - dt) <= timedelta(days=max_days)
        except:
            pass

    # If format not recognized → reject
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
    # Strict filtering (no compromises)
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
    # Strict fallback (still enforces all rules)
    # -----------------------------
    if len(selected) < 3:
        for item in organic:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            date_text = item.get("date", "") or snippet

            if (
                is_ai_relevant(title, snippet)
                and is_india_relevant(title, snippet)
                and is_recent(date_text)
                and item not in selected
            ):
                selected.append(item)

            if len(selected) >= 3:
                break

    selected = selected[:3]

    if not selected:
        return "<p>No India-specific AI articles found from the last 7 days.</p>"

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

Output a complete HTML email body using email-safe table layout.

Use this structure:

<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6fb; padding:20px;">
  <tr>
    <td align="center">
      <table width="600" cellpadding="0" cellspacing="0">

        <!-- Repeat this card block for each article -->
        <tr>
          <td style="padding-bottom:15px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff; border:1px solid #e6e9f0; border-radius:12px;">
              <tr>
                <td style="padding:18px;">
                  <h3 style="color:#1a73e8; margin:0 0 10px 0;">1. Headline here</h3>
                  <ul style="padding-left:18px; margin:0 0 10px 0;">
                    <li>Key point one</li>
                    <li>Key point two</li>
                  </ul>
                  <p style="margin:0 0 10px 0;"><b>Impact:</b> short impact sentence</p>
                  <p style="margin:0;">🔗 <a href="URL_HERE" style="color:#8e44ad; text-decoration:none;">Read full article</a></p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>

Rules:
- Keep headlines concise
- Make key points crisp
- Use the exact same URLs
- Do NOT include markdown
- Output only HTML

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
