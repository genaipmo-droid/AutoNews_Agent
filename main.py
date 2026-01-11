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
        return True  # Important: don't reject if date is missing

    text = text.lower()

    # Handles: "2 days ago", "5 hours ago", "1 week ago"
    match = re.search(r"(\d+)\s+(minute|hour|day|week)s?\s+ago", text)
    if match:
        value = int(match.group(1))
        unit = match.group(2)

        if unit == "minute" or unit == "hour":
            return True
        if unit == "day":
            return value <= max_days
        if unit == "week":
            return value * 7 <= max_days

    # Handles: "Jan 05, 2026" and "January 5, 2026"
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            dt = datetime.strptime(text.strip(), fmt)
            return datetime.now() - dt <= timedelta(days=max_days)
        except:
            pass

    # If we can't understand the date, keep the article instead of dropping it
    return True

# -----------------------------
# Main pipeline
# -----------------------------
def run_autonews():
    # 1. Search real articles using SerpAPI
    search = SerpAPIWrapper()

    query = """
    Latest AI news India government startup research MNC funding launch partnership
    site:thehindu.com OR site:livemint.com OR site:economictimes.com
    OR site:business-standard.com OR site:pib.gov.in OR site:indiatoday.in
    OR site:indianexpress.com OR site:hindustantimes.com
    OR site:timesofindia.indiatimes.com OR site:moneycontrol.com
    OR site:analyticsindiamag.com OR site:inc42.com
    OR site:yourstory.com OR site:techcircle.in
    OR site:techcrunch.com/tag/india
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
    if len(fresh_articles) < 3:
    fresh_articles = organic[:3]

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
