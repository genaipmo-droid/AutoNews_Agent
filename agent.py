import os
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, load_tools
from langchain.prompts import PromptTemplate
from langchain_community.utilities import SerpAPIWrapper

def run_autonews_agent():
    # Step 1: Use SerpAPI directly (structured results)
    search = SerpAPIWrapper(params={
        "q": "AI advancements in India government startup MNC site:thehindu.com OR site:livemint.com OR site:economictimes.com",
        "num": 10,
        "recency": 14
    })

    results = search.results()

    # Extract top organic results safely
    articles = results.get("organic_results", [])[:5]

    # Build clean source list
    sources_text = ""
    for i, item in enumerate(articles[:3], 1):
        sources_text += f"{i}. {item['title']}\nURL: {item['link']}\n\n"

    # Step 2: Now summarize using LLM
    llm = ChatOpenAI(
        temperature=0.2,
        model="gpt-3.5-turbo",
        base_url=os.getenv("OPENAI_API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY")
    )

    prompt = f"""
You are a professional analyst.

Summarize the following real news articles into a clean report.

For each item provide:
- Headline
- 2 Key Points
- Impact on India
- Keep the same URL

Articles:
{sources_text}
"""

    response = llm.invoke(prompt)

    return response.content
