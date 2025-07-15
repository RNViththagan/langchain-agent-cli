from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
import asyncio
import json
import os

# Load environment variables from .env
load_dotenv()

# Initialize Anthropic model
model = ChatAnthropic(model="claude-3-opus-20240229")

# Define server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",
    args=["math_server.py"],  # Adjust this to your actual file path if needed
)

# Utility: Extract readable message contents
def extract_message_content(obj):
    if isinstance(obj, dict) and "messages" in obj:
        return [
            {"role": type(m).__name__.replace("Message", "").lower(), "content": m.content}
            for m in obj["messages"]
            if hasattr(m, "content")
        ]
    elif isinstance(obj, BaseMessage):
        return {"role": type(obj).__name__.replace("Message", "").lower(), "content": obj.content}
    return str(obj)

# Run the agent workflow
async def run_agent():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(model, tools)
            agent_response = await agent.ainvoke({"messages": "what's (3 + 5) x 12?"})
            return agent_response

# Main execution block
if __name__ == "__main__":
    result = asyncio.run(run_agent())

    # Extract readable message content
    readable_output = extract_message_content(result)

    # Format as pretty JSON
    formatted_result = json.dumps(readable_output, indent=2, ensure_ascii=False)

    # Save to file
    output_path = "agent_output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(formatted_result)

    print(f"Agent response saved to {output_path}:\n")
    print(formatted_result)
