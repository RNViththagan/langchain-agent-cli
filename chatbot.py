import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, ToolMessage

from client import extract_message_content

# Load environment
load_dotenv()

# Constants
LOG_DIR = "chat_logs"
os.makedirs(LOG_DIR, exist_ok=True)
model = ChatAnthropic(model="claude-3-opus-20240229")
server_params = StdioServerParameters(command="python", args=["math_server.py"])


# ---------- Utility Functions ----------

def log_message(role, content):
    return {
        "timestamp": datetime.now().isoformat(),
        "role": role,
        "content": content
    }

def append_ai_response(chat_history, session_log, ai_messages):
    for msg in ai_messages:
        print(f"🧠 Message {type(msg).__name__}: {msg}\n\n")

        if isinstance(msg, AIMessage):
            chat_history.append(msg)
            text_parts = [
                c["text"] for c in msg.content
                if isinstance(c, dict) and c.get("type") == "text"
            ]
            if text_parts:
                session_log.append(log_message("assistant", "\n".join(text_parts)))

        elif isinstance(msg, ToolMessage):
            chat_history.append(msg)
            session_log.append(log_message(
                "tool",
                f"[{msg.name}] {msg.content} (Status: {getattr(msg, 'status', 'unknown')})"
            ))
def display_agent_response(result):
    print("\n🧠 Agent Reasoning:\n" + "-" * 60)
    if isinstance(result, dict) and "messages" in result:
        messages = result["messages"]
        for msg in messages:
            if isinstance(msg, AIMessage):
                for content in msg.content:
                    if isinstance(content, dict):
                        if content.get("type") == "text":
                            text = content.get("text", "").strip()
                            if text.startswith("<thinking>"):
                                print(f"🧩 Thought:\n{text.replace('<thinking>', '').replace('</thinking>', '').strip()}\n")
                        elif content.get("type") == "tool_use":
                            tool_name = content.get("name")
                            args = content.get("input", {})
                            arg_str = ", ".join(f"{k}={v}" for k, v in args.items())
                            print(f"🔧 Tool Planned: {tool_name}({arg_str})")
            elif msg.type == "tool":
                tool_name = getattr(msg, "name", "")
                status = getattr(msg, "status", "success")
                content = getattr(msg, "content", "").strip()
                print(f"🛠️ Tool Response [{tool_name}]: {content} (Status: {status})")

        final_texts = [
            p["text"]
            for m in messages if isinstance(m, AIMessage)
            for p in m.content
            if isinstance(p, dict) and p.get("type") == "text"
        ]
        if final_texts:
            print("\n✅ Final Answer:\n" + "-" * 60)
            print(f"🤖 Agent: {final_texts[-1].strip()}\n")
    else:
        print("🤖 Agent:", result)


def print_chat_history(chat_history):
    print("\n📜 Chat History Debug:\n" + "-" * 60)
    for msg in chat_history:
        if isinstance(msg, HumanMessage):
            print(f"🧑 You: {msg.content}")
        elif isinstance(msg, AIMessage):
            text_parts = [
                c["text"] for c in msg.content
                if isinstance(c, dict) and c.get("type") == "text"
            ]
            if text_parts:
                print(f"🤖 Agent: {' '.join(text_parts)}")
        elif isinstance(msg, ToolMessage):
            status = getattr(msg, "status", "success")
            print(f"🛠️ Tool [{msg.name}]: {msg.content} (Status: {status})")
        else:
            # Fallback for any other message types
            print(f"📦 {type(msg).__name__}: {getattr(msg, 'content', '')}")
    print("-" * 60 + "\n")


# ---------- Main Chat Loop ----------


questions = ["what's (3 + 5) x 12?","what is 78 x 54?", "multily it into 10000"]
async def run_chat():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(model, tools)

            print("\n🎉 Welcome to the AI Shell!")
            print("Here are the available tools (capabilities):\n")
            for tool in tools:
                print(f"🔧 {tool.name}: {tool.description}")
            print("\nType your question or task below. Type 'exit' or 'quit' to leave.\n")

            chat_history: list[BaseMessage] = []
            session_log = []


            for user_input in questions:
            #while True:
                #user_input = input("🧑 You: ").strip()
                if user_input.lower() in {"exit", "quit"}:
                    print("👋 Goodbye!")
                    break

                try:
                    chat_history.append(HumanMessage(content=user_input))
                    session_log.append(log_message("user", user_input))

                    result = await agent.ainvoke({"messages": chat_history})
                    readable_output = extract_message_content(result)
                    formatted_result = json.dumps(readable_output, indent=2, ensure_ascii=False)

                    # Log AI response
                    if isinstance(result, dict) and "messages" in result:
                        append_ai_response(chat_history, session_log, result["messages"])

                    print("\n🤖 Agent Response:\n", formatted_result)
                    display_agent_response(result)
                    print_chat_history(chat_history)

                except Exception as e:
                    print(f"⚠️ Error: {e}\n")

            # Save session log
            now = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            log_path = os.path.join(LOG_DIR, f"chat_{now}.json")
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(session_log, f, indent=2, ensure_ascii=False)
            print(f"\n📝 Session log saved to {log_path}")


# ---------- Entry Point ----------
if __name__ == "__main__":
    asyncio.run(run_chat())
