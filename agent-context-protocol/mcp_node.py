import os
import yaml
from typing import Optional, Dict, List
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os
import sys

class MCPServerClient:
    def __init__(self, name, server_config, defaults):
        self.name = name
        self.config = server_config
        self.defaults = defaults
        self.exit_stack = AsyncExitStack()
        self.session: Optional[ClientSession] = None
        self.tools = {}

    async def initialize(self):
        server_type = self.config["type"]
        server_path = self.config["path"]
        env = {**os.environ, **self.config.get("env", {})}
        args = self.config.get("args", [])

        command = (
            # self.defaults.get("python_env_path", "python") if server_type == "python"
            self.defaults.get("python_env_path") or sys.executable if server_type == "python"
            else self.defaults.get("node_command", "node")
        )

        server_params = StdioServerParameters(
            command=command,
            args=[server_path, *args],
            env=env
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        tool_list = await self.session.list_tools()
        for tool in tool_list.tools:
            self.tools[tool.name] = {
                "description": tool.description,
                "inputSchema": tool.inputSchema
            }

    async def call_tool(self, tool_name: str, tool_args: dict):
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found in server '{self.name}'")
        return await self.session.call_tool(tool_name, tool_args)

    async def cleanup(self):
        await self.exit_stack.aclose()


class MCPToolManager:
    def __init__(self):
        self.server_clients: List[MCPServerClient] = []
        self.tool_to_server: Dict[str, MCPServerClient] = {}

    async def load_from_config(self, config_path: str):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        defaults = config.get("defaults", {})
        servers = config.get("servers", [])

        for server_cfg in servers:
            client = MCPServerClient(server_cfg["name"], server_cfg, defaults)
            await client.initialize()
            self.server_clients.append(client)
            for tool in client.tools:
                self.tool_to_server[tool] = client

    def list_all_tools(self):
        return {
            tool: {
                "description": client.tools[tool]["description"],
                "server": client.name
            }
            for tool, client in self.tool_to_server.items()
        }

    def return_documentation(self):
            return {
                tool: {
                    "documentation": f"""Description: {client.tools[tool]["description"]}""",
                    "parameters": f"""{client.tools[tool]["inputSchema"]}""",
                    "server": client.name,
                    "parameters_dict": client.tools[tool]["inputSchema"],
                }
                for tool, client in self.tool_to_server.items()
            }

    async def call_tool(self, tool_name: str, tool_args: dict):
        if tool_name not in self.tool_to_server:
            raise ValueError(f"Tool '{tool_name}' not found in any registered server.")
        
        client = self.tool_to_server[tool_name]
        try:
            output = await client.call_tool(tool_name, tool_args)
            return True, output
        except Exception as e:
            return False, {"error": str(e)}

    async def cleanup(self):
        for client in self.server_clients:
            await client.cleanup()