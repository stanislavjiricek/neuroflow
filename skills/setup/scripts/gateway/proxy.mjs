/**
 * Model-name proxy for Claude Code → an Anthropic-compatible gateway (legacy).
 *
 * For gateways that speak the Anthropic protocol but reject Claude Code's claude-* model
 * names when the ANTHROPIC_DEFAULT_*_MODEL mapping is not enough. Every request is sent with
 * the target model; the original claude-* name is restored in the response.
 * See skills/setup/references/custom-gateway.md.
 *
 * Usage (the key comes from the environment — never type it into a chat or this file):
 *   GATEWAY_URL=https://llm.example.org GATEWAY_KEY="$(cat ~/.claude-gateway/gateway-key)" \
 *     node proxy.mjs <target-model> [port]      (port defaults to 3456)
 *
 * Then in another terminal:
 *   ANTHROPIC_BASE_URL=http://localhost:3456 ANTHROPIC_AUTH_TOKEN=dummy claude
 */

import http from "http";
import https from "https";

const GATEWAY_URL  = process.env.GATEWAY_URL;
const GATEWAY_KEY  = process.env.GATEWAY_KEY;
const TARGET_MODEL = process.argv[2];
const PORT         = parseInt(process.argv[3] || "3456", 10);

if (!GATEWAY_URL || !GATEWAY_KEY || !TARGET_MODEL) {
  console.error("Set GATEWAY_URL and GATEWAY_KEY, and pass the target model: node proxy.mjs <target-model> [port]");
  process.exit(2);
}

function target_host() {
  return new URL(GATEWAY_URL).host;
}

function forward(req, res, bodyChunks) {
  const body = Buffer.concat(bodyChunks);
  let payload;
  let originalModel = null;

  // Patch the model name in request body; save original so we can restore it in the response.
  // Claude Code validates that the model in the response matches the claude-* name it sent —
  // without this round-trip, it errors with an "unexpected model" message.
  try {
    const json = JSON.parse(body.toString());
    if (json.model) {
      originalModel = json.model;
      console.log(`  [proxy] model override: ${json.model} → ${TARGET_MODEL}`);
      json.model = TARGET_MODEL;
    }
    payload = Buffer.from(JSON.stringify(json));
  } catch {
    payload = body;
  }

  const target = new URL(GATEWAY_URL);
  const secure = target.protocol === "https:";
  const options = {
    hostname: target.hostname,
    port: target.port || (secure ? 443 : 80),
    path: target.pathname.replace(/\/$/, "") + req.url,
    method: req.method,
    headers: {
      "Content-Type": "application/json",
      "Content-Length": payload.length,
      "Authorization": `Bearer ${GATEWAY_KEY}`,
      "anthropic-version": req.headers["anthropic-version"] || "2023-06-01",
    },
  };

  const proxyReq = (secure ? https : http).request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);

    if (originalModel) {
      // Restore the original claude-* model name in each response chunk so Claude Code
      // does not reject the response. Works for both streaming (SSE) and non-streaming.
      proxyRes.on("data", (chunk) => {
        const patched = chunk.toString()
          .replaceAll(`"model":"${TARGET_MODEL}"`, `"model":"${originalModel}"`);
        res.write(Buffer.from(patched));
      });
      proxyRes.on("end", () => res.end());
    } else {
      proxyRes.pipe(res);
    }
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
  console.log(`Gateway proxy running on http://localhost:${PORT} → ${target_host()}`);
  console.log(`Routing all requests → ${TARGET_MODEL}`);
  console.log();
  console.log("In another terminal, launch Claude Code with:");
  console.log(`  ANTHROPIC_BASE_URL=http://localhost:${PORT} ANTHROPIC_AUTH_TOKEN=dummy claude`);
  console.log();
  console.log("Press Ctrl+C to stop.");
});
