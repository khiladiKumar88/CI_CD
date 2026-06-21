# CI/CD Failure Analyzer

Automatically analyzes failed GitHub Actions workflows using a free LLM and provides actionable fix suggestions.

**Cost: $0** — uses free-tier APIs only (Google Gemini or GitHub Models).

## How It Works

1. Any workflow in your repo fails
2. The `failure-analyzer.yml` workflow auto-triggers
3. It fetches the failed job logs via GitHub API
4. Extracts error-relevant sections + mentioned source files
5. Sends them to a free LLM for analysis
6. Prints fix suggestions in the Actions **Summary** tab

## Setup (5 minutes)

### 1. Files are already in place

```
.github/workflows/failure-analyzer.yml   <- auto-triggers on failure
analyze_failure.py                        <- main analysis script
```

### 2. Add your free LLM API key

**Option A - Google Gemini (recommended, 1500 free requests/day):**
1. Go to https://aistudio.google.com/apikey
2. Click "Create API key" (no credit card needed)
3. In your GitHub repo: Settings -> Secrets and variables -> Actions -> New repository secret
4. Name: `GEMINI_API_KEY` - Value: paste your key

**Option B - GitHub Models (no extra key needed):**
1. Edit `.github/workflows/failure-analyzer.yml`
2. Comment out the Gemini lines, uncomment the GitHub Models lines

### 3. Done

Next time any workflow fails, check the "Failure Analyzer" run in the Actions tab.

## Features

- **Auto-triggers** on any workflow failure
- **Smart log extraction** — pulls error-relevant lines, not the full verbose output
- **Source file analysis** — extracts files mentioned in tracebacks for deeper analysis
- **Error classification** — categorizes errors (build, test, dependency, runtime, config, timeout)
- **Rate limit protection** — built-in retry with exponential backoff
- **Log truncation** — handles massive CI outputs gracefully

## Testing Locally

```bash
export GITHUB_TOKEN="ghp_your_personal_access_token"
export GITHUB_REPOSITORY="your-username/your-repo"
export FAILED_RUN_ID="12345678"
export LLM_PROVIDER="gemini"
export GEMINI_API_KEY="your_key"

python analyze_failure.py
```

## Free Tier Limits

| Provider | Model | Free Limit |
|----------|-------|------------|
| Google Gemini | gemini-2.0-flash | 15 req/min, 1500 req/day |
| GitHub Models | gpt-4o-mini | ~150 req/day |
