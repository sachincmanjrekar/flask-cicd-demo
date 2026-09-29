# Flask Task API — CI/CD Demo

A tiny Flask REST API (in-memory task list) built specifically to demonstrate
a correctly-gated CI/CD pipeline: GitHub Actions runs lint + tests, and only
triggers a Render deployment if they pass.

## Endpoints

| Method | Path          | Description        |
|--------|---------------|---------------------|
| GET    | /health       | Health check        |
| GET    | /tasks        | List all tasks      |
| POST   | /tasks        | Create a task       |
| GET    | /tasks/<id>   | Get one task        |
| PATCH  | /tasks/<id>   | Update a task       |
| DELETE | /tasks/<id>   | Delete a task        |

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

```bash
curl http://127.0.0.1:5000/health
curl -X POST http://127.0.0.1:5000/tasks -H "Content-Type: application/json" -d "{\"title\": \"demo\"}"
```

## Test / lint

```bash
pytest
ruff check .
```

## Deploying (Render)

1. Push this repo to GitHub.
2. On [render.com](https://render.com), sign up free, "New +" → "Web Service"
   → connect this GitHub repo.
3. Render auto-detects `render.yaml`. Build command: `pip install -r
   requirements.txt`. Start command: `gunicorn app:app`.
4. `autoDeploy` is set to `false` in `render.yaml` on purpose — deploys are
   NOT triggered directly by git push. Instead:
   - In Render's dashboard, go to the service → Settings → find the
     **Deploy Hook** URL, copy it.
   - In the GitHub repo, go to Settings → Secrets and variables → Actions →
     New repository secret, name it `RENDER_DEPLOY_HOOK`, paste the URL.
5. Now every push to `main` runs the GitHub Actions workflow
   (`.github/workflows/ci-cd.yml`): lint → test → (only if both pass, and
   only on `main`) → curl the Render deploy hook → Render builds and
   deploys.

---

## Interview cheat sheet: CI/CD, explained properly

### The core idea
CI/CD is not one thing — it's two related but distinct practices:

- **Continuous Integration (CI)**: every time code is pushed, an automated
  pipeline checks it out on a clean machine, installs dependencies, and runs
  lint + tests. This catches breakage immediately instead of at code review
  or (worse) in production.
- **Continuous Deployment (CD)**: if that pipeline passes, the change is
  automatically shipped to production with no human clicking "deploy."
  ("Continuous Delivery" is the softer version — auto-*prepares* a release
  but a human clicks the final button. I'm doing full Deployment here.)

### Why the naive version is wrong (this is the key differentiator to say out loud)
Most people connect their host directly to GitHub and let it auto-deploy on
every push. That's **not actually CD** — it's just "deploy on push." If your
tests would have failed, it ships anyway, because the host doesn't know
about your test suite at all. Two systems (GitHub Actions test runner,
Render's git watcher) fire independently.

### How this repo does it correctly
In `render.yaml`, `autoDeploy: false` disables Render's own git-triggered
deploys. Instead, `.github/workflows/ci-cd.yml` has two jobs:

```
test job:  checkout → install → ruff → pytest
deploy job: needs: test   (only runs if test job succeeded)
            if: branch == main and event == push
            → curl -X POST <Render deploy hook secret>
```

The `deploy` job's `needs: test` is doing the real work — GitHub Actions
will not run it unless `test` exits 0. So broken code is structurally
incapable of reaching production. That's the actual guarantee CI/CD is
supposed to give you, and it's the sentence to say if asked "how does your
pipeline work."

### The deploy hook itself
It's just a unique, secret URL Render generates per-service. A `POST` to it
tells Render "pull latest and rebuild," the same way a webhook would trigger
any other deploy system. It's stored as a GitHub Actions **secret**
(`RENDER_DEPLOY_HOOK`), never committed to the repo — secrets in pipelines
should always live in the CI platform's secret store, not in code.

### Infrastructure as Code
`render.yaml` itself is a small example of Infrastructure as Code — the
service's build command, start command, plan, and health-check path are all
defined in a version-controlled file instead of clicked together by hand in
a dashboard. If the service ever needs to be recreated, the config is
reproducible from git history.

### If asked "what would you add for a real production system"
- A staging environment: deploy to staging automatically, require a manual
  approval gate before promoting to production.
- Rollback: keep the last N deploys and add a one-click/one-command revert.
- Notifications: pipeline posts to Slack on failure.
- More test coverage: integration tests hitting a real (test) database
  instead of in-memory state, since this demo has no persistence.

### Agile / DevOps quick reference
- **Sprint**: fixed time-box (often 2 weeks) for delivering backlog items.
- **Backlog / user story**: prioritized, user-perspective work item.
- **Daily standup**: short sync — did, doing, blockers.
- **Sprint review**: demo completed work to stakeholders.
- **Retrospective**: team reflects on process improvements.
- **Definition of done**: reviewed, tested, CI green, documented.
- **DevOps**: treating infra/deployment as automated and version-controlled
  (this repo's whole pipeline is a small example of that).

## Notes
- Tasks are stored in memory and reset when the app restarts — this is a
  demo, not a production data layer.
