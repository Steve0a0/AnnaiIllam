import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the http module before importing authService
vi.mock("@/lib/http", () => ({
  http: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

import { http } from "@/lib/http";
import { authService } from "@/services/auth.service";

const mockPost = vi.mocked(http.post);
const mockGet = vi.mocked(http.get);

const MOCK_AUTH_RESPONSE = {
  data: {
    success: true,
    message: "Login successful",
    data: {
      access_token: "access.token",
      token_type: "bearer",
      csrf_token: "csrf.token",
      user: { id: 1, email: "admin@example.com", name: "Test Admin", role: "admin" },
    },
  },
};

const MOCK_ME_RESPONSE = {
  data: {
    success: true,
    message: "OK",
    data: { id: 1, email: "admin@example.com", name: "Test Admin", role: "admin" },
  },
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("authService", () => {
  // ---------------------------------------------------------------------------
  // requestOtp / verifyOtp — disabled in admin
  // ---------------------------------------------------------------------------

  it("requestOtp throws — OTP is not enabled for admin", async () => {
    await expect(authService.requestOtp({ phone: "9876543210" })).rejects.toThrow(
      "OTP login is not enabled"
    );
  });

  it("verifyOtp throws — OTP is not enabled for admin", async () => {
    await expect(
      authService.verifyOtp({ phone: "9876543210", code: "123456" })
    ).rejects.toThrow("OTP login is not enabled");
  });

  // ---------------------------------------------------------------------------
  // login
  // ---------------------------------------------------------------------------

  it("login posts to /auth/admin/login and returns response", async () => {
    mockPost.mockResolvedValueOnce(MOCK_AUTH_RESPONSE);
    const result = await authService.login({
      email: "admin@example.com",
      password: "AdminPass123!",
    });
    expect(mockPost).toHaveBeenCalledWith("/auth/admin/login", {
      email: "admin@example.com",
      password: "AdminPass123!",
    });
    expect(result).toEqual(MOCK_AUTH_RESPONSE.data);
  });

  it("login propagates network errors", async () => {
    mockPost.mockRejectedValueOnce(new Error("Network error"));
    await expect(
      authService.login({ email: "admin@example.com", password: "AdminPass123!" })
    ).rejects.toThrow("Network error");
  });

  // ---------------------------------------------------------------------------
  // getMe
  // ---------------------------------------------------------------------------

  it("getMe sends GET to /me and returns data", async () => {
    mockGet.mockResolvedValueOnce(MOCK_ME_RESPONSE);
    const result = await authService.getMe();
    expect(mockGet).toHaveBeenCalledWith("/me");
    expect(result).toEqual(MOCK_ME_RESPONSE.data);
  });

  // ---------------------------------------------------------------------------
  // browser session bootstrap and rotation
  // ---------------------------------------------------------------------------

  it("getCsrfToken reads the server-issued CSRF token", async () => {
    const response = { data: { success: true, data: { csrf_token: "csrf.token" } } };
    mockGet.mockResolvedValueOnce(response);
    const result = await authService.getCsrfToken();
    expect(mockGet).toHaveBeenCalledWith("/auth/admin/csrf");
    expect(result).toEqual(response.data);
  });

  it("refreshSession uses the HttpOnly cookie and CSRF header", async () => {
    const mockRefreshResponse = {
      data: {
        success: true,
        data: {
          access_token: "new.access",
          token_type: "bearer",
          csrf_token: "new.csrf",
          user: { id: 1, email: "admin@example.com", name: "Test Admin", role: "admin" },
        },
      },
    };
    mockPost.mockResolvedValueOnce(mockRefreshResponse);
    const result = await authService.refreshSession("csrf.token");
    expect(mockPost).toHaveBeenCalledWith("/auth/admin/refresh", undefined, {
      headers: { "X-CSRF-Token": "csrf.token" },
    });
    expect(result).toEqual(mockRefreshResponse.data);
  });

  // ---------------------------------------------------------------------------
  // logout
  // ---------------------------------------------------------------------------

  it("logout uses the cookie session and CSRF header", async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } });
    await authService.logout("csrf.token");
    expect(mockPost).toHaveBeenCalledWith("/auth/admin/logout", undefined, {
      headers: { "X-CSRF-Token": "csrf.token" },
    });
  });

  it("logout returns response data", async () => {
    const mockResponse = { data: { success: true, message: "Logged out successfully" } };
    mockPost.mockResolvedValueOnce(mockResponse);
    const result = await authService.logout("csrf.token");
    expect(result).toEqual(mockResponse.data);
  });
});
