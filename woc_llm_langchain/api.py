import os
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# 配置 GitHub Models 的接入点
os.environ["OPENAI_API_KEY"] = "key"  # 这里填你的 token
os.environ["OPENAI_BASE_URL"] = "endpoint"  # GitHub Models 的 endpoint

# 初始化模型
# 可用模型列表：https://github.com/marketplace/models
llm = ChatOpenAI(
    model="gpt-4o-mini",  # 或者用 "DeepSeek-V3"、"Llama-3.3-70B" 等
    temperature=0.7,
    max_tokens=1000,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_BASE_URL"),
)

# 调用
messages = [
    SystemMessage(content="你是一个乐于助人的助手。"),
    HumanMessage(content="用一句话介绍 LangChain")
]
response = llm.invoke(messages)
print(response.content)