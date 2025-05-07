# Overview

## BaseToolHandler

The `BaseToolHandler` class provides a foundation for all tool handlers in this project. It encapsulates common functionality such as:

- **Error Handling:**  A centralized `handleGoogleApiError` method to gracefully handle errors returned by the Google Calendar API, specifically addressing authentication issues.
- **Authentication:** Receives an OAuth2Client instance for authenticated API calls.
- **Abstraction:**  Defines the `runTool` abstract method that all handlers must implement to execute their specific logic.

By extending `BaseToolHandler`, each tool handler benefits from consistent error handling and a standardized structure, promoting code reusability and maintainability.  This approach ensures that all handlers adhere to a common pattern for interacting with the Google Calendar API and managing authentication.

### How ListEventsHandler Uses BaseToolHandler

The `ListEventsHandler` extends the `BaseToolHandler` to inherit its common functionalities. Specifically, this inheritance promotes code reuse and maintainability, as common functionalities are centralized in the `BaseToolHandler` class.

Here is an example from `ListEventsHandler`

```typescript
export class ListEventsHandler extends BaseToolHandler {
    async runTool(args: any, oauth2Client: OAuth2Client): Promise<CallToolResult> {
        const validArgs = ListEventsArgumentsSchema.parse(args);
        const events = await this.listEvents(oauth2Client, validArgs);
        return {
            content: [{
                type: "text",
                text: this.formatEventList(events),
            }],
        };
    }

    // Additional helper methods...
}
```

### Registration with handlerMap

Finally, add the tool name (as defined in `ToolDefinitions`) and a new instance of the corresponding handler (e.g., `ListEventsHandler`) to the `handlerMap` in `callTool.ts`. This map enables the tool invocation system to automatically route incoming tool calls to the correct handler implementation.

```typescript
const handlerMap: Record<string, BaseToolHandler> = {
    "list-calendars": new ListCalendarsHandler(),
    "list-events": new ListEventsHandler(),
    "search-events": new SearchEventsHandler(),
    "list-colors": new ListColorsHandler(),
    "create-event": new CreateEventHandler(),
    "update-event": new UpdateEventHandler(),
    "delete-event": new DeleteEventHandler(),
};
```