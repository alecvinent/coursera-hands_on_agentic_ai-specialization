from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

# 1. Initialize Tools & LLM
search_tool = DuckDuckGoSearchRun()
tools = [search_tool]

llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")

# 2. Add Memory Component
memory = ConversationBufferMemory(
    memory_key="chat_history", 
    return_messages=True
)

# 3. Initialize Agent Executor
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

# 4. Execution Example
response_1 = agent.run("What are the key highlights of recent space exploration missions?")
print(response_1)

# Follow-up leveraging memory
response_2 = agent.run("Can you format those highlights into 3 bullet points?")
print(response_2)