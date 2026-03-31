/**
 * e-INFRA LLM Proxy for Claude Code
 *
 * Sits between Claude Code and https://llm.ai.e-infra.cz
 * Claude Code sends requests with claude-* model names → proxy maps them to real e-infra IDs.
 *
 * Usage:
 *   node proxy.mjs              (default: qwen3.5-122b on port 3456)
 *   node proxy.mjs kimi-k2.5    (use a different model)
 *   node proxy.mjs deepseek-v3.2 8080  (custom model + port)
 *
 * Then in another terminal:
 *   ANTHROPIC_BASE_URL=http://localhost:3456 ANTHROPIC_API_KEY=any claude
 */

import http from "http";
import https from "https";

const EINFRA_API   = "https://llm.ai.e-infra.cz";
const EINFRA_KEY   = "<YOUR_API_KEY>";    // replace with your e-INFRA API key
const TARGET_MODEL = process.argv[2] || "qwen3.5-122b";
const PORT         = parseInt(process.argv[3] || "3456", 10);

// ── Available models ──────────────────────────────────────────────────────────
// General / best overall:  qwen3.5-122b
// Coding:                  qwen3-coder-next, deepseek-v3.2
// Reasoning/thinking:      deepseek-v3.2-thinking
// Agentic / tool use:      kimi-k2.5
// Fast / small:            mini, mistral-small-4, qwen3-coder-30b
// ─────────────────────────────────────────────────────────────────────────────

function forward(req, res, bodyChunks) {
  const body = Buffer.concat(bodyChunks);
  let payload;

  // Patch the model name in request body if it's JSON
  try {
    const json = JSON.parse(body.toString());
    if (json.model) {
      console.log(`  [proxy] model override: ${json.model} → ${TARGET_MODEL}`);
      json.model = TARGET_MODEL;
    }
    payload = Buffer.from(JSON.stringify(json));
  } catch {
    payload = body;
  }

  const target = new URL(EINFRA_API);
  const options = {
    hostname: target.hostname,
    port: 443,
    path: req.url,
    method: req.method,
    headers: {
      "Content-Type": "application/json",
      "Content-Length": payload.length,
      "Authorization": `Bearer ${EINFRA_KEY}`,
      "anthropic-version": req.headers["anthropic-version"] || "2023-06-01",
    },
  };

  const proxyReq = https.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res);
  });

  proxyReq.on("error", (err) => {
    console.error("[proxy] upstream error:", err.message);
    res.writeHead(502);
    res.end(JSON.stringify({ error: err.message }));
  });

  proxyReq.write(payload);
  proxyReq.end();
}

const server = http.createServer((req, res) => {
  const chunks = [];
  req.on("data", (c) => chunks.push(c));
  req.on("end", () => {
    console.log(`→ ${req.method} ${req.url}`);
    forward(req, res, chunks);
  });
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`e-INFRA proxy running on http://localhost:${PORT}`);
  console.log(`Routing all requests → ${TARGET_MODEL}`);
  console.log();
  console.log("In another terminal, launch Claude Code with:");
  console.log(`  ANTHROPIC_BASE_URL=http://localhost:${PORT} ANTHROPIC_API_KEY=any claude`);
  console.log();
  console.log("Press Ctrl+C to stop.");
});
