import axios from "axios";

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    const message = error.response?.data?.message;
    if (typeof detail === "object" && detail !== null && "message" in detail) {
      return String(detail.message);
    }
    return String(detail ?? message ?? "Something went wrong");
  }

  if (error instanceof Error) {
    return error.message || "Something went wrong";
  }

  return "Something went wrong";
}
