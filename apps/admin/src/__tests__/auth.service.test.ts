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
      refresh_token: "refresh.token",
      token_type: "bearer",
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
  // refreshToken
  // ---------------------------------------------------------------------------

  it("refreshToken posts refresh_token and returns new tokens", async () => {
    const mockRefreshResponse = {
      data: {
        success: true,
        data: {
          access_token: "new.access",
          refresh_token: "new.refresh",
          token_type: "bearer",
        },
      },
    };
    mockPost.mockResolvedValueOnce(mockRefreshResponse);
    const result = await authService.refreshToken("old.refresh.token");
    expect(mockPost).toHaveBeenCalledWith("/auth/refresh", {
      refresh_token: "old.refresh.token",
    });
    expect(result).toEqual(mockRefreshResponse.data);
  });

  // ---------------------------------------------------------------------------
  // logout
  // ---------------------------------------------------------------------------

  it("logout posts refresh_token to /auth/logout", async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } });
    await authService.logout("refresh.token");
    expect(mockPost).toHaveBeenCalledWith("/auth/logout", {
      refresh_token: "refresh.token",
    });
  });

  it("logout returns response data", async () => {
    const mockResponse = { data: { success: true, message: "Logged out successfully" } };
    mockPost.mockResolvedValueOnce(mockResponse);
    const result = await authService.logout("refresh.token");
    expect(result).toEqual(mockResponse.data);
  });
});
