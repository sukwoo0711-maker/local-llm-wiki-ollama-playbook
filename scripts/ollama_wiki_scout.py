from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


SYSTEM_PROMPT = """You are Qwen Wiki Scout.
You produce candidates only.
Do not answer the user's domain question.
Do not edit final wiki pages.
Do not invent facts.
Return valid JSON only.
Every claim-like suggestion must include an evidence phrase from the input when possible.
"""


PROMPTS = {
    "expand-query": """Task: Given a work question, produce search terms for local wiki lookup.
Rules:
- Do not answer the question.
- Return JSON only.
- Include exact terms, synonyms, abbreviations, likely path globs, and negative terms.
- Do not invent exact file names.
- Max 12 terms.
Output schema:
{
  "query_intent": "...",
  "terms": ["..."],
  "negative_terms": ["..."],
  "likely_path_globs": ["docs/**/*.md", "wiki/**/*.md"],
  "followup_questions": ["..."]
}
Question:
{text}
""",
    "suggest-links": """Task: Suggest wiki links and tags for one markdown chunk.
Rules:
- Do not rewrite the source.
- Return JSON only.
- Every candidate must cite a phrase from the input chunk.
Existing page titles: {pages}
Output schema:
{
  "tags": ["..."],
  "wiki_links": [
    {"target": "...", "reason": "...", "evidence_phrase": "..."}
  ],
  "new_page_candidates": []
}
Chunk:
{text}
""",
    "gap-questions": """Task: Generate missing requirement questions from a draft.
Rules:
- Ask questions only.
- Focus on ambiguity, evidence gaps, ownership, timing, rollback, security, monitoring, and verification.
- Do not propose implementation.
- Return JSON only.
Output schema:
{
  "must_ask": ["..."],
  "should_ask": ["..."],
  "evidence_needed": [
    {"question": "...", "likely_source": "..."}
  ]
}
Draft:
{text}
""",
    "context-pack": """Task: Select the smallest set of context items to pass to a stronger coding agent.
Rules:
- Do not answer the task.
- Prefer source-backed wiki pages.
- Max 8 items.
- Return JSON only.
Output schema:
{
  "selected_context": [
    {"path": "...", "section_or_key": "...", "reason": "...", "risk_if_missing": "..."}
  ],
  "excluded": [
    {"path": "...", "reason": "duplicate/low relevance/stale"}
  ]
}
Input:
{text}
""",
}


def call_ollama(host: str, model: str, prompt: str, num_ctx: int) -> dict:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.8,
            "num_ctx": num_ctx,
        },
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{host.rstrip('/')}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to call Ollama at {host}: {exc}") from exc


def parse_json_content(response: dict) -> object:
    content = response.get("message", {}).get("content", "")
    if not content:
        return response
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw_content": content, "parse_error": "model did not return valid JSON"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Ollama local LLM wiki scout")
    parser.add_argument("command", choices=sorted(PROMPTS))
    parser.add_argument("--text", required=True, help="Input text or task")
    parser.add_argument("--pages", default="", help="Comma-separated existing wiki page titles")
    parser.add_argument("--model", default="qwen2.5-coder:7b")
    parser.add_argument("--host", default="http://localhost:11434")
    parser.add_argument("--num-ctx", type=int, default=8192)
    args = parser.parse_args()

    prompt = PROMPTS[args.command].replace("{text}", args.text).replace("{pages}", args.pages)
    response = call_ollama(args.host, args.model, prompt, args.num_ctx)
    parsed = parse_json_content(response)
    json.dump(parsed, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
