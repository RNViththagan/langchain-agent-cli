import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

load_dotenv()

model = ChatAnthropic(model="claude-3-opus-20240229")

server_params = StdioServerParameters(
    command="python",
    args=["math_server.py"],  # adjust if needed
)

# Initialize agent and tools once
async def setup_agent():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(model, tools)
            return agent, tools, session

# Run interactive shell
async def run_chat():
    agent, tools, session = await setup_agent()

    # Display capabilities and greeting
    print("\n🎉 Welcome to the AI Shell!")
    print("Here are the available tools (capabilities):\n")
    for tool in tools:
        print(f"🔧 {tool.name}: {tool.description}")
    print("\nType your question or task below. Type 'exit' or 'quit' to leave.\n")

    # Chat loop
    while True:
        user_input = input("🧑 You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Goodbye!")
            break
        try:
            result = await agent.ainvoke({"messages": user_input})
            if isinstance(result, dict) and "messages" in result:
                last_message = result["messages"][-1]
                content = last_message.content if hasattr(last_message, "content") else str(last_message)
                print(f"🤖 Agent: {content}\n")
            else:
                print(f"🤖 Agent: {result}\n")
        except Exception as e:
            print(f"⚠️ Error: {e}\n")

# Run the chatbot
if __name__ == "__main__":
    asyncio.run(run_chat())
