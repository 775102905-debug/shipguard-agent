import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.integrations.mcp_server import run_mcp_server

if __name__ == "__main__":
    run_mcp_server(host="127.0.0.1", port=8100)
