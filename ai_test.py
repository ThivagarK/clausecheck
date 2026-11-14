import os
from langchain_openai import ChatOpenAI

# Grab API key from the environment variable
api_key = os.getenv("INFERENCE_API_KEY")

if not api_key:
    raise ValueError("INFERENCE_API_KEY environment variable is missing!")

# Initialize LangChain configured for Vultr's OpenAI-compatible endpoint
llm = ChatOpenAI(
    model="deepseek-v4.1-flash-1017",
    openai_api_key=api_key,
    openai_api_base="https://api.vultrinference.com/v1",
    temperature=0.2
)

# Test prompt mimicking an AP reconciliation task
response = llm.invoke("You are an AP reconciliation agent. Briefly explain what an invoice discrepancy is.")

print("\n--- LangChain AI Agent Response ---")
print(response.content)
