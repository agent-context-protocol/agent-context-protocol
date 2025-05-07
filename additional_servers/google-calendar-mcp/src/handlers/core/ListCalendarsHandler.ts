import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { OAuth2Client } from "google-auth-library";
import { BaseToolHandler } from "./BaseToolHandler.js";
import { calendar_v3, google } from "googleapis";

export class ListCalendarsHandler extends BaseToolHandler {
    async runTool(_: any, oauth2Client: OAuth2Client): Promise<CallToolResult> {
        const calendars = await this.listCalendars(oauth2Client);
        return {
            content: [{
                type: "text", // This MUST be a string literal
                text: this.formatCalendarList(calendars),
            }],
        };
    }

    private async listCalendars(client: OAuth2Client): Promise<calendar_v3.Schema$CalendarListEntry[]> {
        try {
            const calendar = this.getCalendar(client);
            const response = await calendar.calendarList.list();
            return response.data.items || [];
        } catch (error) {
            throw this.handleGoogleApiError(error);
        }
    }


    /**
     * Formats a list of calendars into a user-friendly string.
     */
    private formatCalendarList(calendars: calendar_v3.Schema$CalendarListEntry[]): string {
        return calendars
            .map((cal) => `${cal.summary || "Untitled"} (${cal.id || "no-id"})`)
            .join("\n");
    }

}
