import { useAuthStore } from "../shared/store/auth.store";

const MOCK_USER = { id: 1, phone: "9876543210", role: "client" as const };
const MOCK_TOKENS = {
  accessToken: "access.token",
  refreshToken: "refresh.token",
};

function resetStore() {
  useAuthStore.setState({
    accessToken: null,
    refreshToken: null,
    user: null,
    isHydrated: false,
    isProfileComplete: null,
    onboardingStep: null,
    biometricSetupDone: false,
  });
}

describe("useAuthStore (mobile)", () => {
  beforeEach(resetStore);

  // ---------------------------------------------------------------------------
  // Initial state
  // ---------------------------------------------------------------------------

  it("has correct initial state", () => {
    const s = useAuthStore.getState();
    expect(s.accessToken).toBeNull();
    expect(s.refreshToken).toBeNull();
    expect(s.user).toBeNull();
    expect(s.isHydrated).toBe(false);
    expect(s.isProfileComplete).toBeNull();
    expect(s.onboardingStep).toBeNull();
    expect(s.biometricSetupDone).toBe(false);
  });

  // ---------------------------------------------------------------------------
  // setAuth
  // ---------------------------------------------------------------------------

  it("setAuth stores tokens, user, and marks hydrated", () => {
    useAuthStore.getState().setAuth({
      accessToken: MOCK_TOKENS.accessToken,
      refreshToken: MOCK_TOKENS.refreshToken,
      user: MOCK_USER,
    });
    const s = useAuthStore.getState();
    expect(s.accessToken).toBe(MOCK_TOKENS.accessToken);
    expect(s.refreshToken).toBe(MOCK_TOKENS.refreshToken);
    expect(s.user).toEqual(MOCK_USER);
    expect(s.isHydrated).toBe(true);
  });

  it("setAuth stores optional fields with defaults", () => {
    useAuthStore.getState().setAuth({
      accessToken: MOCK_TOKENS.accessToken,
      refreshToken: MOCK_TOKENS.refreshToken,
      user: MOCK_USER,
    });
    const s = useAuthStore.getState();
    expect(s.isProfileComplete).toBeNull();
    expect(s.onboardingStep).toBeNull();
    expect(s.biometricSetupDone).toBe(false);
  });

  it("setAuth stores explicit optional fields", () => {
    useAuthStore.getState().setAuth({
      accessToken: MOCK_TOKENS.accessToken,
      refreshToken: MOCK_TOKENS.refreshToken,
      user: MOCK_USER,
      isProfileComplete: true,
      onboardingStep: "identity_uploaded",
      biometricSetupDone: true,
    });
    const s = useAuthStore.getState();
    expect(s.isProfileComplete).toBe(true);
    expect(s.onboardingStep).toBe("identity_uploaded");
    expect(s.biometricSetupDone).toBe(true);
  });

  // ---------------------------------------------------------------------------
  // hydrateAuth
  // ---------------------------------------------------------------------------

  it("hydrateAuth restores session from storage", () => {
    useAuthStore.getState().hydrateAuth({
      accessToken: MOCK_TOKENS.accessToken,
      refreshToken: MOCK_TOKENS.refreshToken,
      user: MOCK_USER,
      onboardingStep: "profile_submitted",
    });
    const s = useAuthStore.getState();
    expect(s.accessToken).toBe(MOCK_TOKENS.accessToken);
    expect(s.onboardingStep).toBe("profile_submitted");
    expect(s.isHydrated).toBe(true);
  });

  it("hydrateAuth with nulls marks hydrated but unauthenticated", () => {
    useAuthStore.getState().hydrateAuth({
      accessToken: null,
      refreshToken: null,
      user: null,
    });
    const s = useAuthStore.getState();
    expect(s.accessToken).toBeNull();
    expect(s.isHydrated).toBe(true);
  });

  // ---------------------------------------------------------------------------
  // clearAuth
  // ---------------------------------------------------------------------------

  it("clearAuth resets all auth state", () => {
    useAuthStore.getState().setAuth({
      accessToken: MOCK_TOKENS.accessToken,
      refreshToken: MOCK_TOKENS.refreshToken,
      user: MOCK_USER,
      isProfileComplete: true,
      onboardingStep: "approved",
      biometricSetupDone: true,
    });
    useAuthStore.getState().clearAuth();
    const s = useAuthStore.getState();
    expect(s.accessToken).toBeNull();
    expect(s.refreshToken).toBeNull();
    expect(s.user).toBeNull();
    expect(s.isProfileComplete).toBeNull();
    expect(s.onboardingStep).toBeNull();
    expect(s.biometricSetupDone).toBe(false);
    expect(s.isHydrated).toBe(true);
  });

  // ---------------------------------------------------------------------------
  // setOnboardingStep
  // ---------------------------------------------------------------------------

  it("setOnboardingStep updates step without touching tokens", () => {
    useAuthStore.getState().setAuth({
      accessToken: MOCK_TOKENS.accessToken,
      refreshToken: MOCK_TOKENS.refreshToken,
      user: MOCK_USER,
    });
    useAuthStore.getState().setOnboardingStep("identity_uploaded");
    const s = useAuthStore.getState();
    expect(s.onboardingStep).toBe("identity_uploaded");
    expect(s.accessToken).toBe(MOCK_TOKENS.accessToken);
  });

  it("setOnboardingStep can clear step to null", () => {
    useAuthStore.getState().setOnboardingStep("identity_uploaded");
    useAuthStore.getState().setOnboardingStep(null);
    expect(useAuthStore.getState().onboardingStep).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // setProfileComplete
  // ---------------------------------------------------------------------------

  it("setProfileComplete updates flag without touching tokens", () => {
    useAuthStore.getState().setAuth({
      accessToken: MOCK_TOKENS.accessToken,
      refreshToken: MOCK_TOKENS.refreshToken,
      user: MOCK_USER,
    });
    useAuthStore.getState().setProfileComplete(true);
    expect(useAuthStore.getState().isProfileComplete).toBe(true);
    expect(useAuthStore.getState().accessToken).toBe(MOCK_TOKENS.accessToken);
  });

  // ---------------------------------------------------------------------------
  // setBiometricSetupDone
  // ---------------------------------------------------------------------------

  it("setBiometricSetupDone toggles the flag", () => {
    useAuthStore.getState().setBiometricSetupDone(true);
    expect(useAuthStore.getState().biometricSetupDone).toBe(true);
    useAuthStore.getState().setBiometricSetupDone(false);
    expect(useAuthStore.getState().biometricSetupDone).toBe(false);
  });
});
