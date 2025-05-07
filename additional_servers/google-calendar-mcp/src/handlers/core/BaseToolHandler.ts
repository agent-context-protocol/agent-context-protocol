import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { OAuth2Client } from "google-auth-library";
import { GaxiosError } from 'gaxios';
import { calendar_v3, google } from "googleapis";


export abstract class BaseToolHandler {
    abstract runTool(args: any, oauth2Client: OAuth2Client): Promise<CallToolResult>;

    protected handleGoogleApiError(error: unknown): void {
        if (
            error instanceof GaxiosError &&
            error.response?.data?.error === 'invalid_grant'
        ) {
            throw new Error(
                'Google API Error: Authentication token is invalid or expired. Please re-run the authentication process (e.g., `npm run auth`).'
            );
        }
        throw error;
    }

    protected getCalendar(auth: OAuth2Client): calendar_v3.Calendar {
        return google.calendar({ version: 'v3', auth });
    }
}
