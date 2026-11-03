# lablab.ai submission draft

**Title (≤50):** Research with Receipts: Sandboxed Records Agent

**Short (≤255):** Ask a question about US recalls or federal spending. An agent on Vultr Serverless Inference writes code, runs it in a locked-down sandbox that can only reach official government APIs, and returns an answer where every number links to its source.

**Long (600–2000):**
Supplier-risk analysts, government-contract sales teams, compliance officers and journalists constantly need answers from public databases: FDA and NHTSA recalls, USAspending contracts, SEC filings, the Federal Register. Today that means hours of downloading and joining spreadsheets, and chat AIs just guess.

Research with Receipts turns a plain-English question into a short Python program written by `deepseek-v4.1-flash` on **Vultr Serverless Inference**. That program runs in a throwaway sandbox: non-root, read-only, 256 MB / 0.5 CPU / 45 s, no secrets in its environment, and no internet except an allowlist of official public-data hosts (enforced by an egress proxy in Docker mode and at DNS resolution in local mode). The sandbox is destroyed after every task. If the code fails, stderr goes back to the model and it fixes itself. Any attempt to reach a non-allowlisted host is refused and shown to the user as a "blocked" audit entry.

The report is written only from executed results, and every number carries a receipt: the exact API request that produced it, one click away.

Real outputs from the live model (Nov 3, 2026):
- **"Which vehicle makes had the most NHTSA recalls in 2025?"** → Ford Motor Company, 146 vehicle recall campaigns covering 12,914,776 potentially affected vehicles; Chrysler (FCA US) 41; Forest River 36; GM 28. Receipt: DOT/NHTSA recalls dataset query on datahub.transportation.gov. ~5–8 s.
- **"Top federal contractors for NAICS 541512 last fiscal year"** → FY2026: Accenture Federal Services $3.04B, General Dynamics IT $2.13B, Oracle Health Government Services $2.06B, Booz Allen Hamilton $1.78B, Deloitte Consulting $1.45B. Receipt: USAspending spending_by_category/recipient API. ~4–9 s.
- **"Recent FDA food recalls for undeclared allergens"** → 21 newest openFDA enforcement records (all reported 2026-10-28 by El Ruisenor De Mexico, Inc.), split into Class I (e.g. Special Red Almond Mole Powder: sesame, peanuts, wheat, soy, tree nuts), Class II and Class III. Receipt: openFDA food enforcement API. ~7–11 s.
- **Containment test:** asked to fetch each recalling firm's website, the agent's code tried 5–10 non-allowlisted hosts; every one was blocked and logged, while the legitimate openFDA data still came back with its receipt.

Business model: $49/mo per seat for contract-sales and compliance teams, plus API access. Our team already sells these government datasets.

**Tech used:** Vultr Serverless Inference (OpenAI-compatible endpoint `https://api.vultrinference.com/v1`, model `deepseek-v4.1-flash`), Python/FastAPI control plane, per-task Docker sandbox (`--read-only`, `--cap-drop ALL`, no-new-privileges, pids/memory/CPU caps, optional gVisor) behind an allowlist egress proxy, public APIs: openFDA, NHTSA (api.nhtsa.gov + datahub.transportation.gov), USAspending, SEC EDGAR, Federal Register.

**Tags:** Vultr, Vultr Serverless Inference, DeepSeek, Docker, AI Agents, Sandboxing, FastAPI, Open Data, GovTech

## Demo assets
- Video (1:58, 1280x720, captions, ElevenLabs voiceover): `demo/research-with-receipts-demo.mp4`
- Voiceover script: `demo/DEMO_SCRIPT.md`
- Screenshots: `demo/screenshots/` (q1 NHTSA, q2 contractors, q3 FDA allergens, q4 sandbox egress test)
- Full transcripts (question, report, receipts, generated code): `demo/transcripts/*.md` and `.json`

## Original long-form video plan (≈2:45, superseded by demo/DEMO_SCRIPT.md)
- 0:00–0:20 Problem: three gov sites, messy joins, and chatbots that hallucinate. "We built an agent that shows its receipts."
- 0:20–0:45 Architecture slide: Vultr VM control plane, Vultr Serverless Inference, per-task Docker sandbox, allowlist proxy.
- 0:45–1:40 Live: ask the Salmonella × contracts question. Show the generated code, the sandbox run (exit 0, seconds), the result table, the cited report, and click a receipt URL that opens the real API.
- 1:40–2:05 Self-heal: a question that makes the first script fail; stderr is fed back and attempt 2 succeeds.
- 2:05–2:35 **Containment moment:** click "🧨 Containment test" (a prompt-injection asks it to exfiltrate to evil.example.com). Status shows CONTAINED because `pubdata` refuses the host before any socket opens, and `docker ps` shows the container is gone. Mention the second layer: a script that uses urllib directly is stopped by the proxy, which logs `DENY evil.example.com`.
- 2:35–2:45 Business value plus the call to action.

## Slides (PDF, 8)
1. Title + one-liner  2. Problem (hours of joins, hallucinated answers)  3. Solution demo screenshot  4. Architecture on Vultr  5. Containment: the 5 controls  6. Market: TAM/SAM (GovCon sales, compliance, supplier risk) + revenue  7. Competitors (ChatGPT ADA, GovSpend, Bloomberg Gov) → USP: cited, sandboxed, cross-agency  8. Roadmap: browser pattern (Playwright), scheduled watchlists, gVisor
