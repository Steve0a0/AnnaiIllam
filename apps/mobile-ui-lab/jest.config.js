/** @type {import('jest').Config} */
const config = {
  preset: "jest-expo",
  testMatch: ["**/__tests__/**/*.test.ts?(x)"],
  moduleNameMapper: {
    "expo-secure-store": "<rootDir>/__mocks__/expo-secure-store.ts",
  },
  transformIgnorePatterns: [
    "node_modules/(?!(jest-)?react-native|@react-native(-community)?|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg|tamagui|@tamagui/.*)",
  ],
};

module.exports = config;
