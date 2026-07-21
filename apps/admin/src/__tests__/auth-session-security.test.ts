import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const projectRoot = resolve(process.cwd());

function source(relativePath: string) {
  return readFileSync(resolve(projectRoot, relativePath), "utf8");
}

function sourceFiles(directory: string): string[] {
  return readdirSync(directory).flatMap((name) => {
    const path = resolve(directory, name);
    if (statSync(path).isDirectory()) {
      return name === "__tests__" ? [] : sourceFiles(path);
    }
    return /\.(ts|tsx)$/.test(name) ? [path] : [];
  });
}

describe("admin browser-session security", () => {
  it("has no browser auth-storage module", () => {
    expect(existsSync(resolve(projectRoot, "src/lib/auth-storage.ts"))).toBe(false);
  });

  it("keeps access and CSRF state in memory without a refresh-token field", () => {
    const store = source("src/store/auth-store.ts");
    expect(store).not.toContain("refreshToken");
    expect(store).not.toContain("localStorage");
    expect(store).not.toContain("sessionStorage");
  });

  it("uses credentialed, single-flight cookie refresh", () => {
    const client = source("src/services/api-client.ts");
    expect(client).toContain("withCredentials: true");
    expect(client).toContain("refreshPromise");
    expect(client).toContain('"X-CSRF-Token"');
    expect(client).not.toContain("localStorage");
  });

  it("contains no direct executable HTML or JavaScript sink", () => {
    const allSource = sourceFiles(resolve(projectRoot, "src")).map((path) => readFileSync(path, "utf8")).join("\n");
    expect(allSource).not.toMatch(
      /dangerouslySetInnerHTML|\.innerHTML\s*=|\.outerHTML\s*=|document\.write\s*\(|\beval\s*\(|new Function\s*\(|javascript:/,
    );
  });
});
