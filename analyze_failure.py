"""
GitHub Actions Failure Analyzer
================================
Monitors failed GitHub Actions workflows, fetches logs, and uses a free LLM
(Google Gemini or GitHub Models) to analyze root causes and suggest fixes.

Cost: $0 — uses free-tier APIs only.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error

# --- Configuration ---

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "")  # e.g. "owner/repo"
RUN_ID = os.environ.get("FAILED_RUN_ID", "")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")  # "gemini" or "github_models"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# --- GitHub API helpers ---

def gh_api(path):
    """Call GitHub REST API."""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def gh_api_text(path):
    """Call GitHub REST API and return plain text."""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8", errors="replace")


# --- Fetch failure details ---

def get_failed_run_info(run_id):
    """Get metadata about the failed workflow run."""
    return gh_api(f"/repos/{REPO}/actions/runs/{run_id}")


def get_failed_jobs(run_id):
    """Get all failed jobs from a workflow run."""
    data = gh_api(f"/repos/{REPO}/actions/runs/{run_id}/jobs")
    return [j for j in data.get("jobs", []) if j["conclusion"] == "failure"]


def get_job_logs(job_id):
    """Download logs for a specific job."""
    url = f"https://api.github.com/repos/{REPO}/actions/jobs/{job_id}/logs"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError:
        return "(Could not fetch logs for this job)"


def extract_error_lines(logs, context_lines=30):
    """Extract the most relevant error portions from verbose logs."""
    lines = logs.splitlines()
    error_patterns = re.compile(
        r"(error|fail|exception|traceback|panic|fatal|FAILED|"
        r"cannot find|not found|permission denied|exit code [1-9])",
        re.IGNORECASE,
    )

    error_indices = set()
    for i, line in enumerate(lines):
        if error_patterns.search(line):
            for j in range(max(0, i - context_lines), min(len(lines), i + context_lines + 1)):
                error_indices.add(j)

    if not error_indices:
        return "\n".join(lines[-100:])

    result = "\n".join(lines[i] for i in sorted(error_indices))
    return result[:4000]


# --- Source file extraction (for function-level errors) ---

def extract_mentioned_files(logs):
    """Find file paths mentioned in error logs."""
    patterns = [
        r'File "([^"]+)"',
        r'at (\S+\.(?:js|ts)):\d+',
        r'(\S+\.(?:go|rs)):\d+:\d+',
        r'in (\S+\.(?:java|kt))',
    ]
    files = set()
    for p in patterns:
        files.update(re.findall(p, logs))
    project_files = [
        f for f in files
        if not any(skip in f for skip in ["/usr/", "site-packages", "node_modules", ".venv"])
    ]
    return project_files[:5]


def read_local_file(file_path):
    """Read a local file if it exists."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return content[:3000]
    except (FileNotFoundError, PermissionError):
        return ""


# --- LLM Integration ---

SYSTEM_PROMPT = (
    "You are a senior DevOps engineer analyzing a GitHub Actions workflow failure.\n\n"
    "Given the workflow metadata and error logs, provide:\n\n"
    "1. **Root Cause** -- What exactly failed and why (be specific, cite log lines).\n"
    "2. **Fix Suggestions** -- 2-3 concrete, actionable fixes ranked by likelihood.\n"
    "   For each fix, show the exact code/config change needed.\n"
    "3. **Prevention** -- One tip to prevent this class of failure in the future.\n\n"
    "Classify the error into one of these categories and tailor your response:\n"
    "- BUILD_ERROR: Compilation/transpilation failure\n"
    "- TEST_FAILURE: Test assertion failed\n"
    "- DEPENDENCY_ERROR: Package install failed\n"
    "- RUNTIME_ERROR: Code crashes at runtime\n"
    "- CONFIG_ERROR: YAML/env/permissions issue\n"
    "- TIMEOUT/OOM: Resource exhaustion\n\n"
    "Be concise. No fluff. Reference specific file paths, commands, or error messages."
)


def call_gemini(prompt):
    """Call Google Gemini API (free tier)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {"maxOutputTokens": 2048, "temperature": 0.3},
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["candidates"][0]["content"]["parts"][0]["text"]


def call_github_models(prompt):
    """Call GitHub Models API (free tier with GitHub PAT)."""
    url = "https://models.inference.ai.azure.com/chat/completions"
    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2048,
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def analyze_with_llm(prompt, max_retries=3):
    """Route to the configured LLM provider with retry logic."""
    import time
    for attempt in range(max_retries):
        try:
            if LLM_PROVIDER == "github_models":
                return call_github_models(prompt)
            else:
                if not GEMINI_API_KEY:
                    print("ERROR: GEMINI_API_KEY not set.")
                    print("Get a free key at https://aistudio.google.com/apikey")
                    sys.exit(1)
                return call_gemini(prompt)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 2 ** attempt * 10
                print(f"Rate limited. Waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                raise
    return "Analysis failed after retries. Check your API quota."


# --- Main ---

MAX_PROMPT_CHARS = 6000

def main():
    if not GITHUB_TOKEN:
        print("ERROR: GITHUB_TOKEN not set")
        sys.exit(1)
    if not REPO:
        print("ERROR: GITHUB_REPOSITORY not set")
        sys.exit(1)
    if not RUN_ID:
        print("ERROR: FAILED_RUN_ID not set")
        sys.exit(1)

    print(f"Analyzing failed run #{RUN_ID} in {REPO}...")

    run_info = get_failed_run_info(RUN_ID)
    workflow_name = run_info.get("name", "Unknown")
    branch = run_info.get("head_branch", "unknown")
    commit_msg = run_info.get("head_commit", {}).get("message", "N/A")
    commit_sha = run_info.get("head_sha", "HEAD")
    trigger_event = run_info.get("event", "unknown")

    failed_jobs = get_failed_jobs(RUN_ID)
    if not failed_jobs:
        print("No failed jobs found in this run.")
        sys.exit(0)

    job_summaries = []
    all_mentioned_files = []

    for job in failed_jobs:
        job_name = job["name"]
        job_id = job["id"]
        failed_steps = [
            s["name"] for s in job.get("steps", [])
            if s.get("conclusion") == "failure"
        ]
        logs = get_job_logs(job_id)
        error_excerpt = extract_error_lines(logs)
        mentioned = extract_mentioned_files(error_excerpt)
        all_mentioned_files.extend(mentioned)
        job_summaries.append({
            "job_name": job_name,
            "failed_steps": failed_steps,
            "error_logs": error_excerpt,
        })

    prompt = f"## Failed Workflow Run\n\n"
    prompt += f"- **Workflow**: {workflow_name}\n"
    prompt += f"- **Branch**: {branch}\n"
    prompt += f"- **Trigger**: {trigger_event}\n"
    prompt += f"- **Commit**: {commit_sha[:8]}\n"
    prompt += f"- **Commit message**: {commit_msg}\n\n"
    prompt += "## Failed Jobs\n\n"

    for js in job_summaries:
        steps_str = ', '.join(js['failed_steps']) or 'N/A'
        prompt += f"### Job: {js['job_name']}\n"
        prompt += f"**Failed steps**: {steps_str}\n\n"
        prompt += f"**Error logs**:\n```\n{js['error_logs']}\n```\n\n"

    for fp in all_mentioned_files[:3]:
        source = read_local_file(fp)
        if source:
            prompt += f"\n### Source: {fp}\n```\n{source}\n```\n"

    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[:MAX_PROMPT_CHARS] + "\n\n[... truncated for length ...]"

    print(f"Sending to {LLM_PROVIDER} for analysis...\n")
    analysis = analyze_with_llm(prompt)

    separator = "=" * 60
    print(separator)
    print("  FAILURE ANALYSIS & FIX SUGGESTIONS")
    print(separator)
    print()
    print(analysis)
    print()
    print(separator)

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write(f"## Failure Analysis for `{workflow_name}` on `{branch}`\n\n")
            f.write(analysis)
            f.write("\n\n---\n*Auto-generated by failure-analyzer*\n")
        print("Analysis written to GitHub Actions step summary.")


if __name__ == "__main__":
    main()
