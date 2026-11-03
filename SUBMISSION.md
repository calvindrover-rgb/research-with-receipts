# lablab.ai submission draft

**Title (≤50):** Research with Receipts: Sandboxed Records Agent

**Short (≤255):** An AI agent that answers questions across FDA, NHTSA, SEC and federal-spending data by writing and running code in a locked-down Vultr sandbox, then returns a report where every fact links to its government source.

**Long (600–2000):**
Supplier-risk analysts, government-contract sales teams, compliance officers and journalists constantly need answers that span several public databases: "Which food companies with Salmonella recalls also hold federal contracts?" or "Which automakers' recalls spiked after a new NHTSA rule?" Today that means hours of downloading, cleaning and joining data from FDA, NHTSA, SEC EDGAR, USAspending and the Federal Register, and chat AIs just guess.

Research with Receipts plans the query, writes Python, and runs it inside a fresh container on a Vultr VM. Agent reasoning runs on Vultr Serverless Inference. The sandbox is non-root, read-only, capped at 256 MB / 0.5 CPU / 45 s, holds no secrets, sits on an internal-only network, and can reach the internet only through an allowlist proxy that admits public-data hosts. It is destroyed after every task. If the code fails, stderr goes back to the model and it fixes itself. If the code tries to leave the allowlist, the task is halted and the containment event is shown to the user.

The output is a short report built only from executed results, and every number is linked to the exact API call that produced it. That makes it audit-ready rather than "trust me."

Business model: $49/mo per seat for contract-sales and compliance teams, plus API access. Our team already sells these datasets and API actors.

**Tags:** Vultr, Vultr Serverless Inference, Docker, AI Agents, Sandboxing, FastAPI, Open Data, GovTech

## Demo video script (≈2:45)
- 0:00–0:20 Problem: three gov sites, messy joins, and chatbots that hallucinate. "We built an agent that shows its receipts."
- 0:20–0:45 Architecture slide: Vultr VM control plane, Vultr Serverless Inference, per-task Docker sandbox, allowlist proxy.
- 0:45–1:40 Live: ask the Salmonella × contracts question. Show the generated code, the sandbox run (exit 0, seconds), the result table, the cited report, and click a receipt URL that opens the real API.
- 1:40–2:05 Self-heal: a question that makes the first script fail; stderr is fed back and attempt 2 succeeds.
- 2:05–2:35 **Containment moment:** click "🧨 Containment test" (a prompt-injection asks it to exfiltrate to evil.example.com). Status shows CONTAINED because `pubdata` refuses the host before any socket opens, and `docker ps` shows the container is gone. Mention the second layer: a script that uses urllib directly is stopped by the proxy, which logs `DENY evil.example.com`.
- 2:35–2:45 Business value plus the call to action.

## Slides (PDF, 8)
1. Title + one-liner  2. Problem (hours of joins, hallucinated answers)  3. Solution demo screenshot  4. Architecture on Vultr  5. Containment: the 5 controls  6. Market: TAM/SAM (GovCon sales, compliance, supplier risk) + revenue  7. Competitors (ChatGPT ADA, GovSpend, Bloomberg Gov) → USP: cited, sandboxed, cross-agency  8. Roadmap: browser pattern (Playwright), scheduled watchlists, gVisor
