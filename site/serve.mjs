import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { resolve, extname } from "node:path";
const root = resolve("dist");
const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css",
  ".js": "text/javascript",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".woff2": "font/woff2",
  ".txt": "text/plain",
  ".xml": "application/xml",
};
createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  let file = resolve(root, "." + decodeURIComponent(url.pathname));
  if (file !== root && !file.startsWith(root + "/")) {
    res.writeHead(403);
    res.end();
    return;
  }
  if (!extname(file)) file += "/index.html";
  try {
    const body = await readFile(file);
    res.writeHead(200, {
      "Content-Type": types[extname(file)] || "application/octet-stream",
    });
    res.end(body);
  } catch {
    res.writeHead(404, { "Content-Type": "text/html" });
    res.end(await readFile(root + "/404.html"));
  }
}).listen(Number(process.env.PORT || 4173), "127.0.0.1", () =>
  console.log("Sideword website: http://127.0.0.1:4173"),
);
