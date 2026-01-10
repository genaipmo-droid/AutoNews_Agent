import os
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, load_tools
from langchain.prompts import PromptTemplate

def run_autonews_agent():
    llm = ChatOpenAI(
        temperature=0.2,
        model="gpt-3.5-turbo",
        base_url="https://openai.vocareum.com/v1",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    tools = load_tools(
        ["serpapi"],
        llm=llm
    )

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent="zero-shot-react-description",
        verbose=False,
        handle_parsing_errors=True
    )

    prompt = PromptTemplate(
    input_variables=["question"],
    template="""
You are a professional news analyst.

Task:
Find the TOP 3 most important AI-related news items in India from the last 14 days.

Sources can include:
- Government announcements
- Indian startups
- Indian research institutes
- Indian offices of global tech companies

STRICT OUTPUT FORMAT (must follow exactly):

1) Headline: <news headline>
   Source: <full clickable URL>
   Key Points:
   - Point 1
   - Point 2
   Impact:
   - 1–2 lines on why this matters for India

2) Headline: ...
   Source: ...
   Key Points:
   - ...
   - ...
   Impact: ...

3) Headline: ...
   Source: ...
   Key Points:
   - ...
   - ...
   Impact: ...

Rules:
- Every item MUST contain a valid URL.
- Do NOT invent sources.
- Use the search tool to fetch real links.

Question:
{question}
"""
)


    question = "Latest AI advancements in India"

    final_prompt = prompt.format(question=question)
    result = agent.run(final_prompt)

    return result
