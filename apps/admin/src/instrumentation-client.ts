import * as Sentry from "@sentry/nextjs";
import { parseSampleRate, scrubSensitiveRequestData } from "@/lib/sentry";

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || process.env.NODE_ENV,
    release: process.env.NEXT_PUBLIC_SENTRY_RELEASE,
    tracesSampleRate: parseSampleRate(process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE),
    sendDefaultPii: false,
    beforeSend: scrubSensitiveRequestData,
  });
}

export const onRouterTransitionStart = Sentry.captureRouterTransitionStart;
