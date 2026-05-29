const _apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!_apiBaseUrl && process.env.NEXT_PUBLIC_APP_ENV !== "local" && process.env.NODE_ENV === "production") {
  throw new Error(
    "NEXT_PUBLIC_API_BASE_URL is required in production. " +
      "Set it to your backend API URL, e.g. https://api.yourdomian.com/api/v1"
  );
}

export const env = {
  // Falls back to localhost only in local/development mode.
  apiBaseUrl: _apiBaseUrl ?? "http://127.0.0.1:8000/api/v1",
};
