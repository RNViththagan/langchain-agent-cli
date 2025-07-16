import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import re
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, ToolMessage

from client import extract_message_content

# ---------- Configuration ----------

load_dotenv()
LOG_DIR = "chat_logs"
os.makedirs(LOG_DIR, exist_ok=True)

BOT_NAME = os.getenv("BOT_NAME")
model = ChatAnthropic(model="claude-3-opus-20240229")

# Run both math server and file server via MultiServer
server_params = StdioServerParameters(command="python", args=["fileserver.py"])


# ---------- Utility Functions ----------

def log_message(role, content):
    return {
        "timestamp": datetime.now().isoformat(),
        "role": role,
        "content": content
    }

def append_ai_response(chat_history, session_log, ai_messages):
    for msg in ai_messages:
        #print(f"🧠 Message {type(msg).__name__}: {msg}\n\n")

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
    print(f"\n🧠 {BOT_NAME} Reasoning:\n" + "-" * 60)

    if not (isinstance(result, dict) and "messages" in result):
        print(f"🤖 {BOT_NAME}:", result)
        return

    messages = result["messages"]

    # Step 1: Find the final AI message (as string or last text chunk)
    final_ai_msg_obj = None
    final_ai_text = None

    for msg in reversed(messages):
        role = msg.get("role", "") if isinstance(msg, dict) else getattr(msg, "role", getattr(msg, "type", ""))
        content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")

        if role == "ai":
            if isinstance(content, str) and content.strip():
                final_ai_text = content.strip()
                final_ai_msg_obj = msg
                break
            elif isinstance(content, list):
                for part in reversed(content):
                    if isinstance(part, dict) and part.get("type") == "text":
                        text = part.get("text", "").strip()
                        if text:
                            final_ai_text = text
                            final_ai_msg_obj = msg
                            break
            if final_ai_text:
                break

    # Step 2: Display all messages except the final AI one
    for msg in messages:
        if msg is final_ai_msg_obj:
            continue

        role = msg.get("role", "") if isinstance(msg, dict) else getattr(msg, "role", getattr(msg, "type", ""))
        content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")

        if role == "human":
            print(f"🧑 Human Message: {content.strip()}")

        elif role == "tool":
            print(f"🛠️ Tool Response: {content.strip()}")

        elif role == "ai":
            if isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    ctype = part.get("type")
                    if ctype == "text":
                        text = part.get("text", "").strip()
                        if text.startswith("<thinking>"):
                            thought = text.replace("<thinking>", "").replace("</thinking>", "").strip()
                            print(f"🧩 Thought:\n{thought}\n")
                        else:
                            print(f"🤖 AI Response: {text}")
                    elif ctype == "tool_use":
                        tool_name = part.get("name")
                        args = part.get("input", {})
                        arg_str = ", ".join(f"{k}={v}" for k, v in args.items())
                        print(f"🔧 Tool Planned: {tool_name}({arg_str})")
            elif isinstance(content, str):
                print(f"🤖 AI Response: {content.strip()}")

    # Step 3: Final Answer — extract from <result> if it exists
    if final_ai_text:
        match = re.search(r"<result>(.*?)</result>", final_ai_text, re.DOTALL)
        if match:
            result_text = match.group(1).strip()
        else:
            result_text = final_ai_text

        print("\n✅ Final Answer:\n")
        print(f"🤖 {BOT_NAME}: {result_text}\n")
        print("*" * 60)



def print_chat_history(chat_history):
    # print("\n📜 Chat History Debug:\n" + "-" * 60)
    for msg in chat_history:
        if isinstance(msg, HumanMessage):
            print(f"🧑 You: {msg.content}")
        elif isinstance(msg, AIMessage):
            text_parts = [
                c["text"] for c in msg.content
                if isinstance(c, dict) and c.get("type") == "text"
            ]
            if text_parts:
                print(f"🤖 {BOT_NAME}: {' '.join(text_parts)}")
        elif isinstance(msg, ToolMessage):
            status = getattr(msg, "status", "success")
            print(f"🛠️ Tool [{msg.name}]: {msg.content} (Status: {status})")
        else:
            print(f"📦 {type(msg).__name__}: {getattr(msg, 'content', '')}")
    print("-" * 60 + "\n")


def save_session_log(session_log, log_path):
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(session_log, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Failed to save session log: {e}")



# ---------- Main Chat Loop ----------

questions = [
    # "what's (3 + 5) x 12?",
    # "what is 78 x 54?",
    # "multiply it into 10000",
    "list all .py files",
    "read_file('script.py')",
    "create a new file 'test.py' with content 'Hello, World!'",
    "list all .py files"
]

async def run_chat():
    now = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    log_path = os.path.join(LOG_DIR, f"chat_{now}.json")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(model, tools)

            print(f"\n🎉 Welcome to the AI Shell powered by {BOT_NAME}!")
            print("Here are the available tools (capabilities):\n")
            for tool in tools:
                print(f"🔧 {tool.name}: {tool.description}")
            print("\nType your question or task below. Type 'exit' or 'quit' to leave.\n")

            chat_history: list[BaseMessage] = []
            session_log = []

            while True:
                user_input = input("🧑 You: ").strip()
                if user_input.lower() in {"exit", "quit"}:
                    print("👋 Goodbye!")
                    break

                try:
                    chat_history.append(HumanMessage(content=user_input))
                    session_log.append(log_message("user", user_input))

                    result = await agent.ainvoke({"messages": chat_history})
                    readable_output = extract_message_content(result)
                    formatted_result = json.dumps(readable_output, indent=2, ensure_ascii=False)

                    if isinstance(result, dict) and "messages" in result:
                        append_ai_response(chat_history, session_log, result["messages"])

                    print(f"{'+' * 60}\n🤖 {BOT_NAME} Response:\n", formatted_result, "\n" + "+" * 60)
                    display_agent_response(result)

                    # <-- Save session log after each response
                    save_session_log(session_log, log_path)

                except Exception as e:
                    print(f"⚠️ Error: {e}\n")

            # Final save on exit (existing)
            save_session_log(session_log, log_path)
            print(f"\n📝 Session log saved to {log_path}")



# ---------- Entry Point ----------
if __name__ == "__main__":
    asyncio.run(run_chat())
