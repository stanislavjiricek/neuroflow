"""
Anthropic ↔ OpenAI proxy for Claude Code → e-INFRA CZ (or any OpenAI-compatible API).
Handles text, tool_use, tool_result, streaming, and thinking blocks.

Usage:
  uv run --python 3.12 --with fastapi --with httpx --with uvicorn \\
    uvicorn proxy:app --host 0.0.0.0 --port 4001

Environment variables:
  OPENAI_API_KEY    Your e-INFRA (or other provider) API key
  OPENAI_BASE_URL   API base URL (default: https://llm.ai.e-infra.cz/v1)
  BIG_MODEL         Model for large/smart requests (default: kimi-k2.5)
  SMALL_MODEL       Model for small/fast requests (default: kimi-k2.5)
  PROXY_DEBUG       Set to 1 to print raw streaming chunks to stderr

Then in another terminal:
  ANTHROPIC_BASE_URL=http://localhost:4001 ANTHROPIC_AUTH_TOKEN=dummy claude
"""
import json, os, uuid, httpx, sys
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

DEBUG = os.environ.get("PROXY_DEBUG", "0") == "1"

def dbg(*args):
    if DEBUG:
        print("[DBG]", *args, file=sys.stderr, flush=True)

OPENAI_BASE = os.environ.get("OPENAI_BASE_URL", "https://llm.ai.e-infra.cz/v1")
OPENAI_KEY  = os.environ.get("OPENAI_API_KEY", "")
BIG_MODEL   = os.environ.get("BIG_MODEL", "kimi-k2.5")
SMALL_MODEL = os.environ.get("SMALL_MODEL", "kimi-k2.5")

MODEL_MAP = {
    "claude-sonnet-4-6": BIG_MODEL,
    "claude-opus-4-6": BIG_MODEL,
    "claude-haiku-4-5-20251001": SMALL_MODEL,
    "claude-3-5-sonnet-20241022": BIG_MODEL,
    "claude-3-opus-20240229": BIG_MODEL,
}

app = FastAPI()


def anthropic_to_openai_messages(messages):
    out = []
    for m in messages:
        role = m["role"]
        content = m.get("content", "")

        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue

        # content is a list of blocks
        if role == "assistant":
            text_parts = []
            tool_calls = []
            for block in content:
                if block["type"] == "text":
                    text_parts.append(block["text"])
                elif block["type"] == "tool_use":
                    tool_calls.append({
                        "id": block["id"],
                        "type": "function",
                        "function": {
                            "name": block["name"],
                            "arguments": json.dumps(block["input"]),
                        }
                    })
            msg = {"role": "assistant", "content": " ".join(text_parts) or None}
            if tool_calls:
                msg["tool_calls"] = tool_calls
            out.append(msg)

        elif role == "user":
            tool_results = [b for b in content if b["type"] == "tool_result"]
            text_blocks  = [b for b in content if b["type"] == "text"]

            for tr in tool_results:
                result_content = tr.get("content", "")
                if isinstance(result_content, list):
                    result_content = " ".join(
                        b.get("text", "") for b in result_content if b.get("type") == "text"
                    )
                out.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_use_id"],
                    "content": result_content,
                })

            if text_blocks:
                out.append({
                    "role": "user",
                    "content": " ".join(b["text"] for b in text_blocks),
                })
        else:
            out.append({"role": role, "content": str(content)})

    return out


def anthropic_to_openai_tools(tools):
    return [{
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t.get("description", ""),
            "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
        }
    } for t in tools]


def openai_to_anthropic_response(oai, model_name):
    choice = oai["choices"][0]
    msg = choice["message"]
    finish = choice.get("finish_reason", "stop")

    content = []
    if msg.get("reasoning_content"):
        content.append({"type": "thinking", "thinking": msg["reasoning_content"]})
    if msg.get("content"):
        content.append({"type": "text", "text": msg["content"]})
    for tc in msg.get("tool_calls", []):
        try:
            inp = json.loads(tc["function"]["arguments"])
        except Exception:
            inp = {}
        content.append({
            "type": "tool_use",
            "id": tc["id"],
            "name": tc["function"]["name"],
            "input": inp,
        })

    stop_reason = "tool_use" if finish == "tool_calls" else "end_turn"
    usage = oai.get("usage", {})

    return {
        "id": oai.get("id", str(uuid.uuid4())),
        "type": "message",
        "role": "assistant",
        "model": model_name,
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        }
    }


async def stream_openai_to_anthropic(response, model_name):
    """Convert OpenAI SSE stream → Anthropic SSE stream.

    Block index tracking rules:
    - thinking block (if any): index 0
    - text block: next available index after thinking
    - tool blocks: each gets next_idx at creation time, stored in tool_block_started dict

    IMPORTANT: tool_block_started is a dict (openai_idx → assigned_block_index), NOT a set.
    Block indices must be assigned once and stored — never recalculated — to avoid
    "Content block not found" errors in Claude Code's streaming parser.
    """
    msg_id = str(uuid.uuid4())
    yield f"event: message_start\ndata: {json.dumps({'type':'message_start','message':{'id':msg_id,'type':'message','role':'assistant','content':[],'model':model_name,'stop_reason':None,'stop_sequence':None,'usage':{'input_tokens':0,'output_tokens':0}}})}\n\n"

    thinking_block_started = False
    thinking_block_closed = False
    text_block_idx = None
    tool_calls_buf = {}
    tool_block_started = {}  # openai_tool_idx -> assigned anthropic block index
    finish_reason = "stop"
    next_idx = 0

    async for line in response.aiter_lines():
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        try:
            chunk = json.loads(data)
        except Exception:
            continue

        choice = chunk.get("choices", [{}])[0]
        delta = choice.get("delta", {})
        finish_reason = choice.get("finish_reason") or finish_reason
        dbg("chunk delta:", json.dumps(delta)[:200], "finish:", finish_reason)

        # thinking delta
        if delta.get("reasoning_content"):
            if not thinking_block_started:
                thinking_block_started = True
                next_idx = 0
                yield f"event: content_block_start\ndata: {json.dumps({'type':'content_block_start','index':0,'content_block':{'type':'thinking','thinking':''}})}\n\n"
            yield f"event: content_block_delta\ndata: {json.dumps({'type':'content_block_delta','index':0,'delta':{'type':'thinking_delta','thinking':delta['reasoning_content']}})}\n\n"

        # text delta
        if delta.get("content"):
            if thinking_block_started and not thinking_block_closed:
                thinking_block_closed = True
                yield f"event: content_block_stop\ndata: {json.dumps({'type':'content_block_stop','index':0})}\n\n"
                next_idx = 1
            if text_block_idx is None:
                text_block_idx = next_idx
                next_idx += 1
                yield f"event: content_block_start\ndata: {json.dumps({'type':'content_block_start','index':text_block_idx,'content_block':{'type':'text','text':''}})}\n\n"
            yield f"event: content_block_delta\ndata: {json.dumps({'type':'content_block_delta','index':text_block_idx,'delta':{'type':'text_delta','text':delta['content']}})}\n\n"

        # tool call deltas
        for tc in delta.get("tool_calls", []):
            idx = tc.get("index", 0)

            if thinking_block_started and not thinking_block_closed:
                thinking_block_closed = True
                yield f"event: content_block_stop\ndata: {json.dumps({'type':'content_block_stop','index':0})}\n\n"
                next_idx = 1

            if idx not in tool_calls_buf:
                tool_calls_buf[idx] = {"id": tc.get("id", ""), "name": "", "args": ""}

            if tc.get("id"):
                tool_calls_buf[idx]["id"] = tc["id"]
            fn = tc.get("function", {})
            if fn.get("name"):
                tool_calls_buf[idx]["name"] += fn["name"]
            if fn.get("arguments"):
                tool_calls_buf[idx]["args"] += fn["arguments"]

            if idx not in tool_block_started:
                if text_block_idx is not None:
                    yield f"event: content_block_stop\ndata: {json.dumps({'type':'content_block_stop','index':text_block_idx})}\n\n"
                    text_block_idx = None
                tool_idx = next_idx
                next_idx += 1
                tool_block_started[idx] = tool_idx
                yield f"event: content_block_start\ndata: {json.dumps({'type':'content_block_start','index':tool_idx,'content_block':{'type':'tool_use','id':tool_calls_buf[idx]['id'],'name':tool_calls_buf[idx]['name'],'input':{}}})}\n\n"
            else:
                tool_idx = tool_block_started[idx]

            if fn.get("arguments"):
                yield f"event: content_block_delta\ndata: {json.dumps({'type':'content_block_delta','index':tool_idx,'delta':{'type':'input_json_delta','partial_json':fn['arguments']}})}\n\n"

    # close any open blocks
    if thinking_block_started and not thinking_block_closed:
        yield f"event: content_block_stop\ndata: {json.dumps({'type':'content_block_stop','index':0})}\n\n"
    if text_block_idx is not None:
        yield f"event: content_block_stop\ndata: {json.dumps({'type':'content_block_stop','index':text_block_idx})}\n\n"
    for idx, block_idx in tool_block_started.items():
        yield f"event: content_block_stop\ndata: {json.dumps({'type':'content_block_stop','index':block_idx})}\n\n"

    stop_reason = "tool_use" if finish_reason == "tool_calls" else "end_turn"
    yield f"event: message_delta\ndata: {json.dumps({'type':'message_delta','delta':{'stop_reason':stop_reason,'stop_sequence':None},'usage':{'output_tokens':0}})}\n\n"
    yield f"event: message_stop\ndata: {json.dumps({'type':'message_stop'})}\n\n"


TOOL_DIRECTIVE = (
    "\n\n# CRITICAL BEHAVIORAL RULES\n"
    "- You are operating as an autonomous coding agent inside Claude Code.\n"
    "- When you need to read a file, run a command, or take any action: DO IT IMMEDIATELY using the appropriate tool. Do NOT describe what you are about to do.\n"
    "- Never say 'I will...' or 'Let me...' before a tool call. Just call the tool.\n"
    "- Always complete the full task using tools before writing any summary.\n"
    "- If a skill or command tells you to run steps, execute ALL steps with tool calls.\n"
)


@app.post("/v1/messages")
async def messages(request: Request):
    body = await request.json()

    anthropic_model = body.get("model", "claude-sonnet-4-6")
    oai_model = MODEL_MAP.get(anthropic_model, BIG_MODEL)
    stream = body.get("stream", False)

    oai_body = {
        "model": oai_model,
        "max_tokens": body.get("max_tokens", 4096),
        "messages": anthropic_to_openai_messages(body.get("messages", [])),
        "stream": stream,
    }
    if body.get("tools"):
        oai_body["tools"] = anthropic_to_openai_tools(body["tools"])
        oai_body["tool_choice"] = "auto"

    if body.get("system"):
        sys_content = body["system"]
        if isinstance(sys_content, list):
            sys_content = " ".join(b.get("text", "") for b in sys_content if b.get("type") == "text")
        oai_body["messages"].insert(0, {"role": "system", "content": sys_content + TOOL_DIRECTIVE})
    else:
        oai_body["messages"].insert(0, {"role": "system", "content": TOOL_DIRECTIVE.strip()})

    if body.get("temperature") is not None:
        oai_body["temperature"] = body["temperature"]

    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json",
    }

    if stream:
        async def generate():
            async with httpx.AsyncClient(timeout=300) as client:
                async with client.stream("POST", f"{OPENAI_BASE}/chat/completions", json=oai_body, headers=headers) as resp:
                    async for chunk in stream_openai_to_anthropic(resp, anthropic_model):
                        yield chunk
        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(f"{OPENAI_BASE}/chat/completions", json=oai_body, headers=headers)
            oai = resp.json()
            if "error" in oai:
                return Response(content=json.dumps(oai), status_code=resp.status_code, media_type="application/json")
            return Response(content=json.dumps(openai_to_anthropic_response(oai, anthropic_model)), media_type="application/json")


@app.head("/")
@app.get("/")
async def health():
    return {"status": "ok"}
