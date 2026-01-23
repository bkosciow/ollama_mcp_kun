from fastmcp import Client as MCPClient
import ollama
import json
import logging
import os

logger = logging.getLogger(__name__)


class AIKun:
    def __init__(self, ollama_url: str, model: str, session_manager=None):
        self.ollama_url = ollama_url
        self.model = model
        self.session_manager = session_manager
        self.ollama_tools = []
        self.url_to_tool = {}
        os.environ["OLLAMA_HOST"] = ollama_url

    async def load_mcps(self, mcps: list=[]):
        for mcp in mcps:
            await self.load_mcp(mcp)

    async def load_mcp(self, mcp_url: str):
        async with MCPClient(mcp_url) as mcp:
            tools_list = await mcp.list_tools()
            for tool in tools_list:
                self.url_to_tool[tool.name] = mcp_url
                self.ollama_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                })

    async def handle_tools(self, tools: list):
        messages = []
        for tool_call in tools:
            tool_response = await self.call_tool(
                self.url_to_tool[tool_call["function"]["name"]],
                tool_call["function"]["name"],
                tool_call["function"]["arguments"]
            )
            messages.append({
                "role": "tool",
                "content": json.dumps(tool_response) if isinstance(tool_response, dict) else str(tool_response),
            })
        return messages

    async def call_tool(self, url: str, tool_name: str, args: dict):
        try:
            async with MCPClient(url) as mcp:
                result = await mcp.call_tool(tool_name, args)
                return result
        except Exception as e:
            logger.error(f"Call failed for {tool_name}: {e}")
            return {"error": str(e)}

    async def parse_response(self, response, session: str=None):
        return response

    async def query(self, prompt: str, session: str=None):
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            tools=self.ollama_tools,
            stream=False,
        )

        if not response.get("message", {}).get("tool_calls"):
            return await self.parse_response(response, session)

        messages = [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response["message"]["content"]}
        ]

        messages += await self.handle_tools(response["message"]["tool_calls"])

        followup_response = ollama.chat(
            model=self.model,
            messages=messages,
        )

        return await self.parse_response(followup_response, session)
