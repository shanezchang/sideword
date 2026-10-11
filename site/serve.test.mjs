import { test } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { once } from "node:events";
import { fileURLToPath } from "node:url";

test("server reports its actual port and serves its own build", async () => {
  const dir = await mkdtemp(join(tmpdir(), "sideword-site-"));
  await mkdir(join(dir, "dist"));
  await writeFile(join(dir, "dist/index.html"), "Sideword isolated fixture");
  const server = spawn(
    process.execPath,
    [fileURLToPath(new URL("serve.mjs", import.meta.url))],
    {
      cwd: dir,
      env: { ...process.env, PORT: "0" },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  try {
    const [line] = await once(server.stdout, "data", {
      signal: AbortSignal.timeout(5000),
    });
    const match = String(line).match(/http:\/\/127\.0\.0\.1:(\d+)/);
    assert.ok(match, String(line));
    assert.notEqual(
      Number(match[1]),
      4173,
      "PORT=0 must report the assigned port, not the default",
    );
    assert.ok(Number(match[1]) > 0);
    const response = await fetch(match[0]);
    assert.equal(response.status, 200);
    assert.equal(await response.text(), "Sideword isolated fixture");
  } finally {
    const exited = once(server, "exit");
    server.kill();
    await exited;
    await rm(dir, { recursive: true, force: true });
  }
});
