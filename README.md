# workeragentcowork

`workeragentcowork` is a planner-worker research briefing system focused on Claude Cowork and Claude Code cost optimization.

It is adapted from the existing working Intelligence Briefing System. The architecture, command-line flow, SQLite storage, optional email delivery, Docker support, and GitHub Actions workflow are preserved. The research topic, source list, report framing, examples, and deployment target have been refocused for Claude Cowork and Claude Code cost optimization.

## What The App Does

You give the app a research topic such as `Claude Cowork and Claude Code cost optimization`. It then:

1. Reads editable source URLs from `sources.txt`.
2. Collects article or page content from those sources.
3. Creates a research plan.
4. Summarizes collected content.
5. Extracts important claims.
6. Cross-verifies claims against independent collected sources.
7. Writes a professional plain-text briefing report.
8. Saves the run, articles, summaries, verifications, and report to SQLite.
9. Optionally emails the report.

The intended readers are CFOs, AI consultants, DevOps teams, managers, knowledge workers, AI governance leads, and mid-market companies with 50-1000 employees.

## What Changed From The Original

The original system was a general Intelligence Briefing System. This copy keeps the working planner-worker pipeline and changes the focus to:

- Claude Cowork cost optimization
- Claude Code cost optimization
- token usage and context management
- tool-call, MCP, skill, workflow, and automation overhead
- repository, folder, connector, and workflow scoping
- DevOps, management, and knowledge-worker usage patterns
- AI FinOps, governance controls, and cost predictability

It is not a new framework or rebuild.

## Architecture

```text
You run a topic
        |
        v
Planner
  Creates focus areas and execution steps
        |
        v
Orchestrator
  Runs each worker in order
        |
        +--> Web Collector reads sources.txt and fetches content
        +--> Summarizer condenses collected content
        +--> Verifier extracts and cross-checks claims
        +--> Writer creates the final briefing report
        +--> Emailer optionally sends the report
        +--> SQLite Store saves results in briefing.db
```

Key files:

```text
workeragentcowork/
  orchestrator.py
  planner.py
  emailer.py
  sources.txt
  requirements.txt
  Dockerfile
  .env.example
  .gitignore
  workers/
    web_collector.py
    summarizer.py
    verifier.py
    writer.py
  store/
    sqlite_store.py
  utils/
    ai_client.py
    retry.py
  .github/workflows/daily-briefing.yml
```

## Install Dependencies

From PowerShell:

```powershell
cd "C:\Users\msell\OneDrive\AIAlchemy\workeragentcowork"
pip install -r requirements.txt
```

Python 3.11 or newer is recommended.

## Configure `.env`

Copy `.env.example` to `.env` and fill in your real values:

```text
OPENAI_API_KEY=sk-your-real-key-here
OPENAI_MODEL=gpt-4o-mini
MAX_ARTICLES_PER_SOURCE=2
MAX_TOTAL_ARTICLES=0
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_APP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_TO=recipient@example.com
```

Only `OPENAI_API_KEY` is required for normal report generation. Email settings are optional.

`MAX_ARTICLES_PER_SOURCE` limits how many items are collected from each URL. `MAX_TOTAL_ARTICLES=0` means no global cap.

Never commit `.env`.

## Edit `sources.txt`

`sources.txt` contains one URL per line. Lines that begin with `#` are ignored.

The default source list is focused on Anthropic, Claude documentation and support, AI FinOps, enterprise AI governance, management research, cloud cost guidance, and developer productivity.

Example:

```text
https://www.anthropic.com
https://docs.anthropic.com
https://support.anthropic.com
https://www.mckinsey.com
https://www.nist.gov/artificial-intelligence
```

You can add, remove, or reorder sources at any time.

## Run The App

Default target topic:

```powershell
python orchestrator.py "Claude Cowork and Claude Code cost optimization"
```

Related supported topics:

```powershell
python orchestrator.py "Claude Cowork cost optimization"
python orchestrator.py "Claude Code cost optimization"
```

Quiet mode:

```powershell
python orchestrator.py "Claude Cowork and Claude Code cost optimization" --quiet
```

Send to a specific email recipient:

```powershell
python orchestrator.py "Claude Cowork and Claude Code cost optimization" --email you@example.com
```

## Report Focus

The writer is framed to produce sections close to:

1. Executive Summary
2. Key Cost Drivers
3. Claude Cowork Cost Optimization Findings
4. Claude Code Cost Optimization Findings
5. Shared Cost Optimization Patterns
6. Governance and Policy Controls
7. DevOps Implications
8. Management and Knowledge Worker Implications
9. Risk and Limitation Analysis
10. Recommended Operating Model
11. Source Evidence Table
12. Claim Verification Table
13. Action Checklist

The report should help readers understand where Claude costs increase, which behaviors create waste, what controls reduce exposure, what metrics to track, and how to turn findings into an operating model.

## Optional Email Delivery

Email is handled by `emailer.py` through SMTP. Gmail users should create a Gmail App Password rather than using a normal account password.

Set these values in `.env`:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_APP_PASSWORD=your-app-password
EMAIL_TO=recipient@example.com
```

If `EMAIL_TO` is blank and no `--email` argument is supplied, the app still runs and prints the report locally.

## SQLite Storage

Each run creates or updates `briefing.db` in the project folder. The database is generated locally and ignored by Git.

Tables include:

| Table | Purpose |
| --- | --- |
| `runs` | One row per briefing run |
| `articles` | Collected article/page content |
| `summaries` | Summaries generated from collected content |
| `verifications` | Extracted claims and verification verdicts |
| `reports` | Final briefing report text |

## Docker

Build the image:

```powershell
docker build -t workeragentcowork .
```

Run it:

```powershell
docker run --rm --env-file .env workeragentcowork "Claude Cowork and Claude Code cost optimization"
```

Persist the local source list and database:

```powershell
docker run --rm `
  --env-file .env `
  -v "${PWD}/sources.txt:/app/sources.txt" `
  -v "${PWD}/briefing.db:/app/briefing.db" `
  workeragentcowork "Claude Cowork and Claude Code cost optimization"
```

## GitHub Actions

The workflow at `.github/workflows/daily-briefing.yml` supports:

- weekly scheduled runs
- manual runs from the GitHub Actions tab
- a default topic of `Claude Cowork and Claude Code cost optimization`

The schedule is Saturday morning Phoenix time:

```yaml
0 14 * * 6
```

Use GitHub Secrets for sensitive values:

- `OPENAI_API_KEY`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_APP_PASSWORD`
- `EMAIL_TO`

Optional GitHub Variables:

- `OPENAI_MODEL`
- `MAX_ARTICLES_PER_SOURCE`
- `MAX_TOTAL_ARTICLES`

## Deploy To GitHub

Repository name:

```text
workeragentcowork
```

Destination:

```text
https://github.com/draialchemy/workeragentcowork
```

Initial deployment commands:

```powershell
cd "C:\Users\msell\OneDrive\AIAlchemy\workeragentcowork"
git init
git add .
git commit -m "Refocus working briefing agent for Claude cost optimization"
git branch -M main
git remote add origin https://github.com/draialchemy/workeragentcowork.git
git push -u origin main
```

If a remote already exists:

```powershell
git remote set-url origin https://github.com/draialchemy/workeragentcowork.git
git push -u origin main
```

## Troubleshooting

**`OPENAI_API_KEY is not set`**

Create `.env` from `.env.example`, add your key, and run again from the same folder as `orchestrator.py`.

**`sources.txt not found`**

Confirm `sources.txt` exists in `C:\Users\msell\OneDrive\AIAlchemy\workeragentcowork`.

**No articles were collected**

Some sources may block scraping or have no discoverable articles. Add more specific Anthropic, Claude Code, AI FinOps, governance, or DevOps URLs to `sources.txt`.

**OpenAI authentication failed**

Check that `OPENAI_API_KEY` is real and that `OPENAI_MODEL` is available to the account.

**Email does not arrive**

Check spam, confirm SMTP settings, and use a Gmail App Password if using Gmail.

## Security Checklist

- [ ] `.env` is present locally but not committed.
- [ ] `.gitignore` includes `.env`, `*.db`, `__pycache__/`, and `*.pyc`.
- [ ] No API keys or SMTP credentials are hardcoded.
- [ ] GitHub Secrets are used for credentials.
- [ ] `briefing.db` and generated output folders are not committed.
- [ ] The GitHub remote is `https://github.com/draialchemy/workeragentcowork.git`.
