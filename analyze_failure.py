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
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "github_models")  # "github_models" or "gemini"
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
