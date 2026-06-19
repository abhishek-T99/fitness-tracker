/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: "jsdom",

  // Runs after the test environment is set up — safe to call expect.extend()
  setupFilesAfterEnv: ["<rootDir>/src/test/setup.js"],

  transform: {
    "^.+\\.[jt]sx?$": "babel-jest",
  },

  // Allow babel-jest to process ESM-only packages that ship without CJS builds
  transformIgnorePatterns: [
    "/node_modules/(?!(clsx|lucide-react)/)",
  ],

  moduleNameMapper: {
    "\\.css$": "identity-obj-proxy",
    "\\.(svg|png|jpg|jpeg|gif|ico|woff2?)$": "<rootDir>/src/test/__mocks__/fileMock.cjs",
    "^lucide-react$": "<rootDir>/src/test/__mocks__/lucide-react.cjs",
  },

  testMatch: [
    "<rootDir>/src/__tests__/**/*.[jt]s?(x)",
  ],

  collectCoverageFrom: [
    "src/**/*.{js,jsx}",
    "!src/main.jsx",
    "!src/App.jsx",
    "!src/index.css",
    "!src/test/**",
  ],
};
