import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { OAuth2Client } from "google-auth-library";
import { fileURLToPath } from "url";

// Import modular components
import { initializeOAuth2Client } from './auth/client.js';
import { AuthServer } from './auth/server.js';
import { TokenManager } from './auth/tokenManager.js';
import { getToolDefinitions } from './handlers/listTools.js';
import { handleCallTool } from './handlers/callTool.js';

// --- Global Variables --- 
// Create server instance (global for export)
const server = new Server(
  {
    name: "google-calendar",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

let oauth2Client: OAuth2Client;
let tokenManager: TokenManager;
let authServer: AuthServer;

// --- Main Application Logic --- 
async function main() {
  try {
    // 1. Initialize Authentication
    oauth2Client = await initializeOAuth2Client();
    tokenManager = new TokenManager(oauth2Client);
    authServer = new AuthServer(oauth2Client);

    // 2. Start auth server if authentication is required
    // The start method internally validates tokens first
    const authSuccess = await authServer.start();
    if (!authSuccess) {
      process.exit(1);
    }

    // 3. Set up MCP Handlers
    
    // List Tools Handler
    server.setRequestHandler(ListToolsRequestSchema, async () => {
      // Directly return the definitions from the handler module
      return getToolDefinitions();
    });

    // Call Tool Handler
    server.setRequestHandler(CallToolRequestSchema, async (request) => {
      // Check if tokens are valid before handling the request
      if (!(await tokenManager.validateTokens())) {
        throw new Error("Authentication required. Please run 'npm run auth' to authenticate.");
      }
      
      // Delegate the actual tool execution to the specialized handler
      return handleCallTool(request, oauth2Client);
    });

    // 4. Connect Server Transport
    const transport = new StdioServerTransport();
    await server.connect(transport);

    // 5. Set up Graceful Shutdown
    process.on("SIGINT", cleanup);
    process.on("SIGTERM", cleanup);

  } catch (error: unknown) {
    process.exit(1);
  }
}

// --- Cleanup Logic --- 
async function cleanup() {
  try {
    if (authServer) {
      // Attempt to stop the auth server if it exists and might be running
      await authServer.stop();
    }
    process.exit(0);
  } catch (error: unknown) {
    process.exit(1);
  }
}

// --- Exports & Execution Guard --- 
// Export server and main for testing or potential programmatic use
export { main, server };

// Run main() only when this script is executed directly
const isDirectRun = import.meta.url.startsWith('file://') && process.argv[1] === fileURLToPath(import.meta.url);
if (isDirectRun) {
  main().catch(() => {
    process.exit(1);
  });
}
