# LangChain Agent CLI

An interactive AI agent CLI built using LangChain, Model Context Protocol (MCP), and Anthropic's API.
It supports multi-tool workflows via MCP and runs a math tool server over stdio.

---

## Features

- Interactive CLI shell powered by Anthropic’s Claude model
- Supports multi-tool workflows (addition, multiplication) using MCP
- Efficient agent-tool communication via stdio
- Easy to extend with new tools and capabilities

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/RNViththagan/langchain-agent-cli.git
cd langchain-agent-cli
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv MCP_Demo
source MCP_Demo/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## API Key Setup

This project uses Anthropic's API for the language model.

Create a `.env` file in the project root with your API key:

```bash
echo "ANTHROPIC_API_KEY=your-anthropic-api-key" > .env
```

Alternatively, export the key in your shell session:

```bash
export ANTHROPIC_API_KEY=your-anthropic-api-key
```

**Note:** `.env` is included in `.gitignore` to keep your API key secure.

---

## Running the Project

### Start the math tool server

This server provides addition and multiplication tools over stdio.

```bash
python math_server.py
```

### Run the interactive chatbot CLI

Interact with the agent that uses the math tools.

```bash
python chatbot.py
```

---

## Project Structure

```
.
├── agent_output.json        # Sample agent output
├── chatbot.py              # Interactive CLI chatbot
├── client.py               # (Optional) Client code if any
├── math_server.py          # Math tools server
├── requirements.txt        # (Optional) List of dependencies
├── .env                    # Environment variables (API keys)
└── .gitignore              # Files ignored by git
```

---

## Reference

This project is based on the tutorial and concepts introduced by Cobus Greyling:

[Using LangChain with Model Context Protocol (MCP)](https://cobusgreyling.medium.com/using-langchain-with-model-context-protocol-mcp-e89b87ee3c4c)
