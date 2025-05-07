import { z } from 'zod';

// Zod schemas for input validation

export const ReminderSchema = z.object({
  method: z.enum(['email', 'popup']).default('popup'),
  minutes: z.number(),
});

export const RemindersSchema = z.object({
  useDefault: z.boolean(),
  overrides: z.array(ReminderSchema).optional(),
});

// ISO datetime regex that requires timezone designator (Z or +/-HH:MM)
const isoDateTimeWithTimezone = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$/;

export const ListEventsArgumentsSchema = z.object({
  calendarId: z.string(),
  timeMin: z.string()
    .regex(isoDateTimeWithTimezone, "Must be ISO format with timezone (e.g., 2024-01-01T00:00:00Z)")
    .optional(),
  timeMax: z.string()
    .regex(isoDateTimeWithTimezone, "Must be ISO format with timezone (e.g., 2024-12-31T23:59:59Z)")
    .optional(),
});

export const SearchEventsArgumentsSchema = z.object({
  calendarId: z.string(),
  query: z.string(),
  timeMin: z.string()
    .regex(isoDateTimeWithTimezone, "Must be ISO format with timezone (e.g., 2024-01-01T00:00:00Z)")
    .optional(), 
  timeMax: z.string()
    .regex(isoDateTimeWithTimezone, "Must be ISO format with timezone (e.g., 2024-12-31T23:59:59Z)")
    .optional(),
});

export const CreateEventArgumentsSchema = z.object({
  calendarId: z.string(),
  summary: z.string(),
  description: z.string().optional(),
  start: z.string().regex(isoDateTimeWithTimezone, "Must be ISO format with timezone (e.g., 2024-01-01T00:00:00Z)"), 
  end: z.string().regex(isoDateTimeWithTimezone, "Must be ISO format with timezone (e.g., 2024-01-01T00:00:00Z)"),
  timeZone: z.string(),
  attendees: z
    .array(
      z.object({
        email: z.string(),
      })
    )
    .optional(),
  location: z.string().optional(),
  colorId: z.string().optional(),
  reminders: RemindersSchema.optional(),
  recurrence: z.array(z.string()).optional(),
});

export const UpdateEventArgumentsSchema = z.object({
  calendarId: z.string(),
  eventId: z.string(),
  summary: z.string().optional(),
  description: z.string().optional(),
  start: z.string()
    .regex(isoDateTimeWithTimezone, "Must be ISO format with timezone (e.g., 2024-01-01T00:00:00Z)")
    .optional(),
  end: z.string()
    .regex(isoDateTimeWithTimezone, "Must be ISO format with timezone (e.g., 2024-01-01T00:00:00Z)")
    .optional(),
  timeZone: z.string(), // Required even if start/end don't change, per API docs for patch
  attendees: z
    .array(
      z.object({
        email: z.string(),
      })
    )
    .optional(),
  location: z.string().optional(),
  colorId: z.string().optional(),
  reminders: RemindersSchema.optional(),
  recurrence: z.array(z.string()).optional(),
});

export const DeleteEventArgumentsSchema = z.object({
  calendarId: z.string(),
  eventId: z.string(),
}); 