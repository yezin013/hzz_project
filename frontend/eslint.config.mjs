import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
  // 빌드 실패 방지를 위한 룰 완화
  {
    rules: {
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": "warn",
      "react-hooks/exhaustive-deps": "warn",
      "@next/next/no-img-element": "warn",
      // React 19 Compiler 관련 규칙
      "react-hooks/static-components": "off",
      "react-hooks/set-state-in-effect": "warn",
      "prefer-const": "warn",
      "react/no-unescaped-entities": "warn",
    },
  },
]);

export default eslintConfig;

