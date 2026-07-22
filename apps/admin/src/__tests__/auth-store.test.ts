import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "@/store/auth-store";

const MOCK_USER = { id: 1, email: "admin@example.com", name: "Admin", role: "admin" };
const MOCK_TOKENS = {
  accessToken: "access.token.here",
  csrfToken: "csrf.token.here",
};

function resetStore() {
  useAuthStore.setState({
    accessToken: null,
    csrfToken: null,
    user: null,
    isHydrated: false,
    hasHydrated: false,
  });
}

describe("useAuthStore", () => {
  beforeEach(resetStore);

  // ---------------------------------------------------------------------------
  // Initial state
  // ---------------------------------------------------------------------------

  it("starts with null tokens and user", () => {
    const state = useAuthStore.getState();
    expect(state.accessToken).toBeNull();
    expect(state.csrfToken).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isHydrated).toBe(false);
    expect(state.hasHydrated).toBe(false);
  });

  // ---------------------------------------------------------------------------
  // setAuth
  // ---------------------------------------------------------------------------

  it("setAuth stores tokens and user and marks hydrated", () => {
    useAuthStore.getState().setAuth({
      accessToken: MOCK_TOKENS.accessToken,
      csrfToken: MOCK_TOKENS.csrfToken,
      user: MOCK_USER,
    });
    const state = useAuthStore.getState();
    expect(state.accessToken).toBe(MOCK_TOKENS.accessToken);
    expect(state.csrfToken).toBe(MOCK_TOKENS.csrfToken);
    expect(state.user).toEqual(MOCK_USER);
    expect(state.isHydrated).toBe(true);
    expect(state.hasHydrated).toBe(true);
  });

  // ---------------------------------------------------------------------------
  // clearAuth
  // ---------------------------------------------------------------------------

  it("clearAuth removes tokens and user", () => {
    useAuthStore.getState().setAuth({
      accessToken: MOCK_TOKENS.accessToken,
      csrfToken: MOCK_TOKENS.csrfToken,
      user: MOCK_USER,
    });
    useAuthStore.getState().clearAuth();
    const state = useAuthStore.getState();
    expect(state.accessToken).toBeNull();
    expect(state.csrfToken).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isHydrated).toBe(true);
    expect(state.hasHydrated).toBe(true);
  });

  // ---------------------------------------------------------------------------
  // setUser
  // ---------------------------------------------------------------------------

  it("setUser updates user without touching tokens", () => {
    useAuthStore.getState().setAuth({
      accessToken: MOCK_TOKENS.accessToken,
      csrfToken: MOCK_TOKENS.csrfToken,
      user: MOCK_USER,
    });
    const updatedUser = { ...MOCK_USER, name: "Updated Admin" };
    useAuthStore.getState().setUser(updatedUser);
    const state = useAuthStore.getState();
    expect(state.user).toEqual(updatedUser);
    expect(state.accessToken).toBe(MOCK_TOKENS.accessToken);
  });

  it("setUser can set user to null", () => {
    useAuthStore.getState().setAuth({
      accessToken: MOCK_TOKENS.accessToken,
      csrfToken: MOCK_TOKENS.csrfToken,
      user: MOCK_USER,
    });
    useAuthStore.getState().setUser(null);
    expect(useAuthStore.getState().user).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // hydrateAuth
  // ---------------------------------------------------------------------------

  it("hydrateAuth with in-memory session data sets authenticated state", () => {
    useAuthStore.getState().hydrateAuth({
      accessToken: MOCK_TOKENS.accessToken,
      csrfToken: MOCK_TOKENS.csrfToken,
      user: MOCK_USER,
    });
    const state = useAuthStore.getState();
    expect(state.accessToken).toBe(MOCK_TOKENS.accessToken);
    expect(state.user).toEqual(MOCK_USER);
    expect(state.isHydrated).toBe(true);
  });

  it("hydrateAuth with nulls marks hydrated but unauthenticated", () => {
    useAuthStore.getState().hydrateAuth({
      accessToken: null,
      csrfToken: null,
      user: null,
    });
    const state = useAuthStore.getState();
    expect(state.accessToken).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isHydrated).toBe(true);
  });

  // ---------------------------------------------------------------------------
  // setHasHydrated (deprecated alias)
  // ---------------------------------------------------------------------------

  it("setHasHydrated keeps isHydrated in sync", () => {
    useAuthStore.getState().setHasHydrated(true);
    const state = useAuthStore.getState();
    expect(state.hasHydrated).toBe(true);
    expect(state.isHydrated).toBe(true);
  });
});
