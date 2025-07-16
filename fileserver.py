# fileserver.py

import os
from typing import List
from mcp.server.fastmcp import FastMCP

# Root folder to allow file access (you can change this)
ROOT_DIR = os.path.abspath("workspace")

mcp = FastMCP("FileServer")


@mcp.tool()
def list_files(extension: str = "") -> List[str]:
    """
    List all files with a given extension (.txt, .py, .bal) in the workspace.
    """
    allowed_exts = [".txt", ".py", ".bal"]
    if extension and extension not in allowed_exts:
        raise ValueError(f"Unsupported extension: {extension}. Allowed: {allowed_exts}")

    files = []
    for fname in os.listdir(ROOT_DIR):
        if os.path.isfile(os.path.join(ROOT_DIR, fname)):
            if not extension or fname.endswith(extension):
                files.append(fname)
    return files


@mcp.tool()
def read_file(filename: str) -> str:
    """
    Read the contents of a file from the workspace directory.
    """
    file_path = os.path.join(ROOT_DIR, filename)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {filename}")
    if not filename.endswith((".txt", ".py", ".bal")):
        raise ValueError("Only .txt, .py, and .bal files are allowed.")

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


@mcp.tool()
def write_file(filename: str, content: str) -> str:
    """
    Write content to a file in the workspace directory.
    Overwrites if the file already exists.
    """
    if not filename.endswith((".txt", ".py", ".bal")):
        raise ValueError("Only .txt, .py, and .bal files are allowed.")

    file_path = os.path.join(ROOT_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ File '{filename}' written successfully."


if __name__ == "__main__":
    print(f"📂 FileServer running in workspace: {ROOT_DIR}")
    os.makedirs(ROOT_DIR, exist_ok=True)
    mcp.run(transport="stdio")
