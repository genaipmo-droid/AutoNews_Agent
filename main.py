import os
import re
from datetime import datetime, timedelta

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SerpAPIWrapper
from email_sender import send_email


# -----------------------------
# Helper: check if article is recent (≤14 days)
# -----------------------------
def is_recent(text, max_days=14):
    if not text:
        return False

    text = text.lower()

    # Matches: "2 days ago", "5 hours ago"
    if re.search(r"\b\d+\s+(day|hour|minute)s?\s+ago\b", text):
        return True

    # Matches: "Jan 05, 2026"
    try:
        dt = datetime.strptime(text.strip(), "%b %d, %Y")
        return datetime.now() - dt <= timedelta(days=max_days)
    except:
        return False


# -----------------------------
# Main pipeline
# -----------------------------
def run_autonews():
    # 1. Search real articles using SerpAPI
    search = SerpAPIWrapper()

    query = """
    Latest AI advancements in India government startup research MNC
    site:thehindu.com OR site:livemint.com OR site:economictimes.com
    OR site:business-standard.com OR site:pib.gov.in OR site:indiatoday.in
    """

    results = search.results(query)
    organic = results.get("organic_results", [])

    # 2. Filter only recent articles
    fresh_articles = []
    for item in organic:
        date_text = item.get("date", "") or item.get("snippet", "")
        if is_recent(date_text):
            fresh_articles.append(item)

    # Keep top 3
    fresh_articles = fresh_articles[:3]

    # Fallback if nothing fresh found
    if not fresh_articles:
        return "No sufficiently recent AI news found today."

    # 3. Build trusted input for LLM
    sources_text = ""
    for i, item in enumerate(fresh_articles, 1):
        sources_text += f"{i}. {item['title']}\nURL: {item['link']}\n\n"

    # 4. Use LLM ONLY for summarization (not searching)
    llm = ChatOpenAI(
        temperature=0.2,
        model="gpt-3.5-turbo",
        base_url=os.getenv("OPENAI_API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY")
    )

    prompt = f"""
You are a professional AI news editor.

Summarize these real news articles into a daily report.

For each item provide:
- Headline
- 2 Key Points
- Impact on India
- Keep the exact same URL

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
