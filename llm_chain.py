

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", api_key=GEMINI_API_KEY)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful, friendly assistant."),
    ("placeholder", "{history}"),  
    ("user", "{input}")            
])

chain = prompt | llm | StrOutputParser()


def get_ai_response(history: list[tuple[str, str]], user_input: str) -> str:
  
    langchain_history = []
    for role, content in history:
        if role == "user":
            langchain_history.append(HumanMessage(content=content))
        else:
            langchain_history.append(AIMessage(content=content))

    response = chain.invoke({
        "history": langchain_history,
        "input": user_input
    })
    return response
