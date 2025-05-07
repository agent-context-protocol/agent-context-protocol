import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { OAuth2Client } from "google-auth-library";
import { SearchEventsArgumentsSchema } from "../../schemas/validators.js";
import { BaseToolHandler } from "./BaseToolHandler.js";
import { calendar_v3 } from 'googleapis';
import { z } from 'zod';
import { formatEventList } from "../utils.js";

export class SearchEventsHandler extends BaseToolHandler {
    async runTool(args: any, oauth2Client: OAuth2Client): Promise<CallToolResult> {
        const validArgs = SearchEventsArgumentsSchema.parse(args);
        const events = await this.searchEvents(oauth2Client, validArgs);
        return {
            content: [{
                type: "text",
                text: formatEventList(events),
            }],
        };
    }

    private async searchEvents(
        client: OAuth2Client,
        args: z.infer<typeof SearchEventsArgumentsSchema>
    ): Promise<calendar_v3.Schema$Event[]> {
        try {
            const calendar = this.getCalendar(client);
            const response = await calendar.events.list({
                calendarId: args.calendarId,
                q: args.query,
                timeMin: args.timeMin,
                timeMax: args.timeMax,
                singleEvents: true,
                orderBy: 'startTime',
            });
            return response.data.items || [];
        } catch (error) {
            throw this.handleGoogleApiError(error);
        }
    }
}
