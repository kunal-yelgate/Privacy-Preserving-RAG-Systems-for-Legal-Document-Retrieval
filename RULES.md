# RULES — Engineering, Security and AI-Assistant Rules

> Applies to every contributor and to any AI coding assistant working in this repo. Read before changing code.

## 1. Security Rules (non-negotiable)
1. **Default deny.** Missing, malformed or unknown permission or metadata means no access and quarantine.
2. **The LLM is not a security boundary.** Authorization is enforced in application code.
3. **Two checks:** filter in the retrieval query, then validate again in app code before context building.
4. **Revalidate before prompting:** re-read `policy_version` immediately before building the prompt. If it changed, restart or abort.
5. **Relevance never overrides permission.** A high score cannot allow a denied chunk.
6. **Private data never enters the public (Tier 1) index** and is never used to improve shared results.
7. **No external calls with user data:** no cloud LLM, embedding, OCR, analytics or telemetry in v1.
8. **No raw text in logs:** log request IDs, policy decisions, document IDs, timestamps and error categories only.
9. **Secrets** live in environment variables or a secrets file outside source control. Never log or commit them.
10. **Fail closed:** on any error in the security path, return a generic error and no content.
11. **Retrieved documents are untrusted data**, never instructions.
12. **Unprotected baselines** (Baseline A/B) run only on synthetic fictional data in an isolated environment, never on real documents or real users.

## 2. Data Rules
- Never commit real client documents, real case files, or personal data.
- Use synthetic matters for tests and evaluation.
- Check licence and terms of use for each public data source before bulk ingestion; record the source and date in MEMORY.md.
- Every chunk needs `tier`, `document_id`, and for Tier 2 a `matter_id`. Otherwise quarantine.

## 3. Code Rules
- Python 3.11+, type hints, `ruff` and `black` formatting.
- Security code (`app/security`, `app/auth`) needs unit tests before merge; target full branch coverage there.
- Every new retrieval path must go through the authorization filter. No bypass helpers.
- Vector store access only through the store interface, never directly from routes.
- Keep functions small; no hidden global state in the security path.
- Config (model names, `k`, `alpha`, thresholds) lives in `configs/`, not in code.

## 4. Testing Rules
- Required test types: positive (authorized passes), negative (unauthorized denied), malformed/missing metadata, permission revoked mid-request, prompt-injection documents, indirect queries.
- A change that touches retrieval or generation must re-run the security test suite.
- Evaluation: fixed config, record model versions, hardware, and sample counts. Report counts and 95% confidence intervals.
- Do not tune on the test split. Failed tests are documented, never silently removed.

## 5. Accuracy and Honesty Rules
- No result numbers in the paper or docs unless produced by a documented, reproducible run.
- Never say "verified" to mean "legally correct". It means traceable to an authorized source passage.
- Prefer abstention over a guess when evidence is weak.
- Do not relax permissions to improve utility. Investigate metadata and retrieval quality instead.
- Do not change the model mid-comparison without recording the configuration.

## 6. Git and Workflow Rules
- Branches: `feature/<name>`, `fix/<name>`. Small PRs.
- Commit format: `type(scope): message` (e.g. `feat(auth): add default-deny policy`).
- No direct commits to `main`. Security-path PRs need a second reviewer.
- Update TRACKER.md when a task changes status; record decisions in MEMORY.md.

## 7. AI Assistant Rules
- Read PRD.md, ARCHITECTURE.md, RULES.md and MEMORY.md before starting a task.
- Do not weaken or remove any security check, even to make a test pass. Ask first.
- Do not add dependencies that call external services without approval.
- State assumptions explicitly; mark unverified claims as such.
- Never invent citations, benchmarks or results.
- After a task: update TRACKER.md and add any new decision to MEMORY.md.

## 8. Definition of Done
- [ ] Code reviewed, formatted, typed
- [ ] Security and unit tests pass
- [ ] No raw text in logs (checked)
- [ ] Docs, TRACKER.md and MEMORY.md updated
- [ ] Works under the recorded hardware and config
