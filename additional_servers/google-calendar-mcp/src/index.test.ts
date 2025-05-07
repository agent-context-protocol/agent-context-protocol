/**
 * @jest-environment node
 */
// Tell TypeScript to ignore type errors in this file
// @ts-nocheck - Removing this as Vitest should handle types better
import { describe, it, expect, vi, beforeEach, beforeAll, afterAll } from 'vitest';

// Import the types we need to mock properly
import type { google as GoogleApis } from 'googleapis';
import type * as FsPromises from 'fs/promises';
import type { Server as MCPServerType } from '@modelcontextprotocol/sdk/server/index.js';
import type { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import type { TokenManager } from './auth/tokenManager.js';

// --- Mocks ---

// Mock process.exit
const mockProcessExit = vi.spyOn(process, 'exit').mockImplementation((() => {}) as (code?: number) => never);

// Mock googleapis
vi.mock('googleapis', async (importOriginal) => {
  const actual = await importOriginal<typeof GoogleApis>();
  return {
    google: {
      ...actual.google,
      calendar: vi.fn().mockReturnValue({
        calendarList: {
          list: vi.fn()
        },
        events: {
          list: vi.fn(),
          insert: vi.fn(),
          patch: vi.fn(),
          delete: vi.fn()
        },
        colors: {
          get: vi.fn()
        },
      })
    }
  };
});

// Mock fs/promises
vi.mock('fs/promises', async (importOriginal) => {
  const actual = await importOriginal<typeof FsPromises>();
  return {
    ...actual,
    readFile: vi.fn(),
    writeFile: vi.fn(),
    access: vi.fn(),
  };
});

// Mock AuthServer
vi.mock('./auth/server.js', () => ({
  AuthServer: vi.fn().mockImplementation(() => ({
    start: vi.fn().mockResolvedValue(true),
    stop: vi.fn().mockResolvedValue(undefined),
  })),
}));

// Mock TokenManager with the same mockValidateTokens
const mockValidateTokens = vi.fn().mockResolvedValue(true);

// Create a more detailed mock implementation that preserves the mock function
vi.mock('./auth/tokenManager.js', () => ({
  TokenManager: vi.fn().mockImplementation(() => ({
    validateTokens: mockValidateTokens,
    loadSavedTokens: vi.fn().mockResolvedValue(true),
    clearTokens: vi.fn(),
  })),
}));

// Mock OAuth2Client
vi.mock('google-auth-library', () => ({
    OAuth2Client: vi.fn().mockImplementation(() => ({
        setCredentials: vi.fn(),
        refreshAccessToken: vi.fn().mockResolvedValue({ credentials: { access_token: 'mock_access_token' } }),
        on: vi.fn(),
        generateAuthUrl: vi.fn().mockReturnValue('http://mockauthurl.com'),
        getToken: vi.fn().mockResolvedValue({ tokens: { access_token: 'mock_access_token' } }),
    }))
}));

// Mock utils
vi.mock('./utils.js', () => ({
    getSecureTokenPath: vi.fn().mockReturnValue('/fake/path/token.json'),
}));

// Mock MCP Server - Store handlers on the instance
vi.mock('@modelcontextprotocol/sdk/server/index.js', () => {
  return {
    Server: vi.fn().mockImplementation(() => {
      const instance = {
        setRequestHandler: vi.fn((schema: any, handler: any) => {
          // Store handlers in a map on the instance
          if (!instance.capturedHandlerMap) {
            instance.capturedHandlerMap = new Map();
          }
          instance.capturedHandlerMap.set(schema, handler);
        }),
        connect: vi.fn().mockResolvedValue(undefined),
        capturedHandlerMap: null as Map<any, Function> | null, // Property to store handlers
      };
      return instance;
    }),
  };
});

// Mock StdioServerTransport
vi.mock('@modelcontextprotocol/sdk/server/stdio.js', () => ({
  StdioServerTransport: vi.fn().mockImplementation(() => ({})), // Simple mock
}));

// Import necessary modules AFTER mocks are set up
const { google } = await import('googleapis');
const fs = await import('fs/promises');

// Need to dynamically import the schema *after* mocking the SDK
const { CallToolRequestSchema } = await import('@modelcontextprotocol/sdk/types.js');

// Import the module to be tested AFTER mocks
// It won't run main automatically due to the check we added
const indexModule = await import('./index.js');
const main = indexModule.main;
const server = indexModule.server as unknown as MCPServerType & { capturedHandlerMap: Map<any, Function> | null }; // Get exported server

// --- Test Suite ---

describe('Google Calendar MCP Tool Calls', () => {
  let mockCalendarApi: ReturnType<GoogleApis['calendar']>;
  let callToolHandler: ((request: any) => Promise<any>) | null = null;

  beforeAll(async () => {
    // Reset mocks that might have been called during import
    vi.clearAllMocks();

    // Setup mocks needed JUST for main() to run without errors
    const mockKeys = JSON.stringify({ installed: { client_id: 'mock', client_secret: 'mock', redirect_uris: ['mock'] } });
    const mockTokens = JSON.stringify({ access_token: 'mock', refresh_token: 'mock', expiry_date: Date.now() + 999999 });
    
    // Make the mock return sequentially
    (fs.readFile as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockKeys) // For initializeOAuth2Client
        .mockResolvedValue(mockTokens);  // For subsequent calls like loadSavedTokens
        
    (fs.access as ReturnType<typeof vi.fn>).mockResolvedValue(true);
    
    // Make sure validateTokens returns true for setup
    mockValidateTokens.mockResolvedValue(true);
    mockProcessExit.mockClear(); // Clear exit mock before running main

    // Run main once to set up the actual handler
    await main();

    // Capture the handler from the map on the mocked server instance
    if (server && server.capturedHandlerMap) {
        // Dynamically get the actual schema object after mocks ran
        const { CallToolRequestSchema } = await import('@modelcontextprotocol/sdk/types.js');
        callToolHandler = server.capturedHandlerMap.get(CallToolRequestSchema);
    } 

    if (!callToolHandler) {
        console.error('capturedHandlerMap on server instance:', server?.capturedHandlerMap);
        throw new Error('CallTool handler not captured from server instance after main run.');
    }
  });

  beforeEach(() => {
    // Reset mocks before each specific test
    vi.clearAllMocks();
    mockProcessExit.mockClear(); // Clear exit mock

    // IMPORTANT: Re-apply default mock implementations needed for the tests
    mockCalendarApi = google.calendar('v3') as unknown as ReturnType<GoogleApis['calendar']>;
    
    // Ensure validateTokens returns true for each test
    mockValidateTokens.mockResolvedValue(true);
    
    (fs.access as ReturnType<typeof vi.fn>).mockResolvedValue(true); // Assume token file access ok
    // readFile needs to be mocked specifically if a test case needs it beyond initialization
    (fs.readFile as ReturnType<typeof vi.fn>).mockClear(); // Clear initial readFile mocks
  });

  it('should reject if authentication is invalid (simulated)', async () => {
    // Arrange: Simulate invalid/missing tokens
    mockValidateTokens.mockResolvedValueOnce(false);

    const request = {
      params: {
        name: 'list-calendars',
        arguments: {},
      },
    };

    // Act & Assert: Expect the handler to reject because we mocked validateTokens to return false
    if (!callToolHandler) throw new Error('callToolHandler not captured');
    await expect(callToolHandler(request)).rejects.toThrow("Authentication required. Please run 'npm run auth' to authenticate."); 
  });

  it('should handle "list-calendars" tool call', async () => {
    // Arrange
    const mockCalendarList = [
      { id: 'cal1', summary: 'Work Calendar' },
      { id: 'cal2', summary: 'Personal' },
    ];
    // Use type assertion for the mocked API calls
    (mockCalendarApi.calendarList.list as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { items: mockCalendarList },
    });

    const request = {
      params: {
        name: 'list-calendars',
        arguments: {},
      },
    };

    // Act
    if (!callToolHandler) throw new Error('callToolHandler not captured');
    const result = await callToolHandler(request);

    // Assert
    expect(mockCalendarApi.calendarList.list).toHaveBeenCalled();
    expect(result).toEqual({
      content: [
        {
          type: 'text',
          text: 'Work Calendar (cal1)\nPersonal (cal2)',
        },
      ],
    });
  });

   it('should handle "create-event" tool call with valid arguments', async () => {
        // Arrange
        const mockEventArgs = {
            calendarId: 'primary',
            summary: 'Team Meeting',
            description: 'Discuss project progress',
            start: '2024-08-15T10:00:00-07:00',
            end: '2024-08-15T11:00:00-07:00',
            timeZone: 'America/Los_Angeles',
            attendees: [{ email: 'test@example.com' }],
            location: 'Conference Room 4',
            colorId: '5', // Example color ID
            reminders: { useDefault: false, overrides: [{ method: 'popup', minutes: 15 }] },
            recurrence: ['RRULE:FREQ=WEEKLY;COUNT=5'],
        };
        const mockApiResponse = {
            id: 'eventId123',
            summary: mockEventArgs.summary,
        };
        (mockCalendarApi.events.insert as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockApiResponse });

        const request = {
            params: {
                name: 'create-event',
                arguments: mockEventArgs,
            },
        };

        // Act
        if (!callToolHandler) throw new Error('callToolHandler not captured');
        const result = await callToolHandler(request);

        // Assert
        expect(mockCalendarApi.events.insert).toHaveBeenCalledWith({
            calendarId: mockEventArgs.calendarId,
            requestBody: {
                summary: mockEventArgs.summary,
                description: mockEventArgs.description,
                start: { dateTime: mockEventArgs.start, timeZone: mockEventArgs.timeZone },
                end: { dateTime: mockEventArgs.end, timeZone: mockEventArgs.timeZone },
                attendees: mockEventArgs.attendees,
                location: mockEventArgs.location,
                colorId: mockEventArgs.colorId,
                reminders: mockEventArgs.reminders,
                recurrence: mockEventArgs.recurrence,
            },
        });
        expect(result).toEqual({
            content: [
                {
                    type: 'text',
                    text: `Event created: ${mockApiResponse.summary} (${mockApiResponse.id})`,
                },
            ],
        });
    });

     it('should handle "create-event" argument validation failure (missing required field)', async () => {
        // Arrange: Missing 'start' which is required
        const invalidEventArgs = {
            calendarId: 'primary',
            summary: 'Incomplete Meeting',
            end: '2024-08-15T11:00:00-07:00',
            timeZone: 'America/Los_Angeles',
        };

        const request = {
            params: {
                name: 'create-event',
                arguments: invalidEventArgs,
            },
        };

        // Act & Assert: Expect Zod validation error
        if (!callToolHandler) throw new Error('callToolHandler not captured');
        await expect(callToolHandler(request)).rejects.toThrow();
    });

    it('should handle "list-events" with timeMin and timeMax', async () => {
        // Arrange
        const listEventsArgs = {
            calendarId: 'primary',
            timeMin: '2024-08-01T00:00:00Z',
            timeMax: '2024-08-31T23:59:59Z',
        };

        const mockEvents = [
            { id: 'event1', summary: 'Meeting', start: { dateTime: '2024-08-15T10:00:00Z' }, end: { dateTime: '2024-08-15T11:00:00Z' } },
            { id: 'event2', summary: 'Lunch', start: { dateTime: '2024-08-15T12:00:00Z' }, end: { dateTime: '2024-08-15T13:00:00Z' }, location: 'Cafe' }
        ];

        (mockCalendarApi.events.list as ReturnType<typeof vi.fn>).mockResolvedValue({
            data: { items: mockEvents }
        });

        const request = {
            params: {
                name: 'list-events',
                arguments: listEventsArgs
            }
        };

        // Act
        if (!callToolHandler) throw new Error('callToolHandler not captured');
        const result = await callToolHandler(request);

        // Assert
        expect(mockCalendarApi.events.list).toHaveBeenCalledWith({
            calendarId: listEventsArgs.calendarId,
            timeMin: listEventsArgs.timeMin,
            timeMax: listEventsArgs.timeMax,
            singleEvents: true,
            orderBy: 'startTime'
        });

        expect(result.content[0].text).toContain('Meeting (event1)');
        expect(result.content[0].text).toContain('Lunch (event2)');
        expect(result.content[0].text).toContain('Location: Cafe');
    });

    it('should handle "search-events" tool call', async () => {
        // Arrange
        const searchEventsArgs = {
            calendarId: 'primary',
            query: 'meeting',
            timeMin: '2024-08-01T00:00:00Z'
        };

        const mockEvents = [
            { id: 'event1', summary: 'Team Meeting', start: { dateTime: '2024-08-15T10:00:00Z' }, end: { dateTime: '2024-08-15T11:00:00Z' } }
        ];

        (mockCalendarApi.events.list as ReturnType<typeof vi.fn>).mockResolvedValue({
            data: { items: mockEvents }
        });

        const request = {
            params: {
                name: 'search-events',
                arguments: searchEventsArgs
            }
        };

        // Act
        if (!callToolHandler) throw new Error('callToolHandler not captured');
        const result = await callToolHandler(request);

        // Assert
        expect(mockCalendarApi.events.list).toHaveBeenCalledWith({
            calendarId: searchEventsArgs.calendarId,
            q: searchEventsArgs.query,
            timeMin: searchEventsArgs.timeMin,
            timeMax: undefined,
            singleEvents: true,
            orderBy: 'startTime'
        });

        expect(result.content[0].text).toContain('Team Meeting (event1)');
    });

    it('should handle "delete-event" tool call', async () => {
        // Arrange
        const deleteEventArgs = {
            calendarId: 'primary',
            eventId: 'event123'
        };

        (mockCalendarApi.events.delete as ReturnType<typeof vi.fn>).mockResolvedValue({});

        const request = {
            params: {
                name: 'delete-event',
                arguments: deleteEventArgs
            }
        };

        // Act
        if (!callToolHandler) throw new Error('callToolHandler not captured');
        const result = await callToolHandler(request);

        // Assert
        expect(mockCalendarApi.events.delete).toHaveBeenCalledWith({
            calendarId: deleteEventArgs.calendarId,
            eventId: deleteEventArgs.eventId
        });

        expect(result.content[0].text).toBe('Event deleted successfully');
    });

    it('should handle "list-colors" tool call', async () => {
        // Arrange
        const mockColorsResponse = {
            event: {
                '1': { background: '#a4bdfc', foreground: '#1d1d1d' },
                '2': { background: '#7ae7bf', foreground: '#1d1d1d' },
            }
        };
        (mockCalendarApi.colors.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockColorsResponse });

        const request = {
            params: {
                name: 'list-colors',
                arguments: {}
            }
        };

        // Act
        if (!callToolHandler) throw new Error('callToolHandler not captured');
        const result = await callToolHandler(request);

        // Assert
        expect(mockCalendarApi.colors.get).toHaveBeenCalled();
        expect(result.content[0].text).toContain('Available event colors:');
        expect(result.content[0].text).toContain('Color ID: 1 - #a4bdfc (background) / #1d1d1d (foreground)');
        expect(result.content[0].text).toContain('Color ID: 2 - #7ae7bf (background) / #1d1d1d (foreground)');
    });

    it('should handle "update-event" tool call', async () => {
        // Arrange
        const updateEventArgs = {
            calendarId: 'primary',
            eventId: 'eventToUpdate123',
            summary: 'Updated Team Meeting',
            location: 'New Conference Room',
            start: '2024-08-15T10:30:00-07:00', 
            // Missing end, but timezone provided
            timeZone: 'America/Los_Angeles',
            colorId: '9',
        };
        const mockApiResponse = {
            id: updateEventArgs.eventId,
            summary: updateEventArgs.summary, 
            location: updateEventArgs.location,
            start: { dateTime: updateEventArgs.start, timeZone: updateEventArgs.timeZone },
            colorId: updateEventArgs.colorId
        };
        (mockCalendarApi.events.patch as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockApiResponse });

        const request = {
            params: {
                name: 'update-event',
                arguments: updateEventArgs
            }
        };

        // Act
        if (!callToolHandler) throw new Error('callToolHandler not captured');
        const result = await callToolHandler(request);

        // Assert
        expect(mockCalendarApi.events.patch).toHaveBeenCalledWith({
            calendarId: updateEventArgs.calendarId,
            eventId: updateEventArgs.eventId,
            requestBody: {
                summary: updateEventArgs.summary,
                location: updateEventArgs.location,
                start: { dateTime: updateEventArgs.start, timeZone: updateEventArgs.timeZone },
                end: { timeZone: updateEventArgs.timeZone }, // Service layer adds timezone to end
                colorId: updateEventArgs.colorId,
            },
        });
        expect(result.content[0].text).toBe(`Event updated: ${mockApiResponse.summary} (${mockApiResponse.id})`);
    });
    
     it('should handle "update-event" argument validation failure (missing eventId)', async () => {
        // Arrange: Missing 'eventId' which is required
        const invalidEventArgs = {
            calendarId: 'primary',
            summary: 'Update without ID',
            timeZone: 'America/Los_Angeles', // timezone is also required by schema
        };

        const request = {
            params: {
                name: 'update-event',
                arguments: invalidEventArgs,
            },
        };

        // Act & Assert: Expect Zod validation error
        if (!callToolHandler) throw new Error('callToolHandler not captured');
        await expect(callToolHandler(request)).rejects.toThrow(); // ZodError
    });

    it('should use the mocked validateTokens function', async () => {
      // Arrange
      mockValidateTokens.mockReset();
      mockValidateTokens.mockResolvedValueOnce(true);
      
      const request = {
        params: {
          name: 'list-calendars',
          arguments: {},
        },
      };
      
      // Mock the calendar list call
      (mockCalendarApi.calendarList.list as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { items: [] },
      });
      
      // Act
      await callToolHandler(request);
      
      // Assert
      expect(mockValidateTokens).toHaveBeenCalledTimes(1);
    });

  // TODO: Add more tests for:
  // - Argument validation failures for other tools
}); 