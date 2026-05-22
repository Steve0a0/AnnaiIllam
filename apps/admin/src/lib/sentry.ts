type SentryEventWithRequest = {
  request?: {
    headers?: Record<string, string>;
    cookies?: unknown;
  };
};

const SENSITIVE_HEADER_NAMES = new Set([
  "authorization",
  "cookie",
  "set-cookie",
  "x-api-key",
  "x-auth-token",
  "x-csrf-token",
]);

export function parseSampleRate(value: string | undefined, fallback = 0): number {
  if (!value) {
    return fallback;
  }

  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }

  return Math.min(Math.max(parsed, 0), 1);
}

export function scrubSensitiveRequestData<T extends SentryEventWithRequest>(event: T): T {
  const headers = event.request?.headers;
  if (headers) {
    for (const key of Object.keys(headers)) {
      if (SENSITIVE_HEADER_NAMES.has(key.toLowerCase())) {
        headers[key] = "[Filtered]";
      }
    }
  }

  if (event.request && "cookies" in event.request) {
    event.request.cookies = "[Filtered]";
  }

  return event;
}
