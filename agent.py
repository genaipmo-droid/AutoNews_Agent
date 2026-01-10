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
Search for AI advancements in India.

Rules:
- News must be within last 14 days
- Include government, startups, MNCs, or research
- Pick TOP 3 impactful items

For each news provide:
• Headline
• Two key points
• Impact
• Full source URL

Question:
{question}
"""
    )

    question = "Latest AI advancements in India"

    final_prompt = prompt.format(question=question)
    result = agent.run(final_prompt)

    return result
