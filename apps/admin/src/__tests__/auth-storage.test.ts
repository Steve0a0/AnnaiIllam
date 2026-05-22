import { describe, it, expect, beforeEach } from "vitest";
import { authStorage } from "@/lib/auth-storage";

// jsdom provides localStorage; reset before each test
beforeEach(() => {
  localStorage.clear();
});

describe("authStorage", () => {
  const ACCESS = "access.token";
  const REFRESH = "refresh.token";
  const USER = { id: 1, phone: "9876543210", role: "admin" };

  // ---------------------------------------------------------------------------
  // setTokens / getAccessToken / getRefreshToken
  // ---------------------------------------------------------------------------

  it("stores and retrieves access and refresh tokens", () => {
    authStorage.setTokens(ACCESS, REFRESH);
    expect(authStorage.getAccessToken()).toBe(ACCESS);
    expect(authStorage.getRefreshToken()).toBe(REFRESH);
  });

  it("getAccessToken returns null when not set", () => {
    expect(authStorage.getAccessToken()).toBeNull();
  });

  it("getRefreshToken returns null when not set", () => {
    expect(authStorage.getRefreshToken()).toBeNull();
  });

  it("setTokens overwrites previous tokens", () => {
    authStorage.setTokens("old.access", "old.refresh");
    authStorage.setTokens(ACCESS, REFRESH);
    expect(authStorage.getAccessToken()).toBe(ACCESS);
    expect(authStorage.getRefreshToken()).toBe(REFRESH);
  });

  // ---------------------------------------------------------------------------
  // setUser / getUser
  // ---------------------------------------------------------------------------

  it("stores and retrieves user as JSON", () => {
    authStorage.setUser(USER);
    expect(authStorage.getUser()).toEqual(USER);
  });

  it("getUser returns null when not set", () => {
    expect(authStorage.getUser()).toBeNull();
  });

  it("handles complex user objects", () => {
    const complex = { ...USER, is_active: true };
    authStorage.setUser(complex);
    expect(authStorage.getUser()).toEqual(complex);
  });

  // ---------------------------------------------------------------------------
  // clear
  // ---------------------------------------------------------------------------

  it("clear removes all stored auth data", () => {
    authStorage.setTokens(ACCESS, REFRESH);
    authStorage.setUser(USER);
    authStorage.clear();
    expect(authStorage.getAccessToken()).toBeNull();
    expect(authStorage.getRefreshToken()).toBeNull();
    expect(authStorage.getUser()).toBeNull();
  });

  it("clear on empty storage does not throw", () => {
    expect(() => authStorage.clear()).not.toThrow();
  });
});
