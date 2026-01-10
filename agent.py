import os
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, load_tools
from langchain.prompts import PromptTemplate
from langchain_community.utilities import SerpAPIWrapper

def run_autonews_agent():
    search = SerpAPIWrapper()

    query = """
    Latest AI advancements in India government startup research MNC
    site:thehindu.com OR site:livemint.com OR site:economictimes.com
    OR site:business-standard.com OR site:pib.gov.in
    """

    results = search.results(query)

    articles = results.get("organic_results", [])[:5]

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
