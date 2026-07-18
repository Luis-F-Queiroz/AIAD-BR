# D4 codebook — firm-level *disclosed* AI adoption (v1.1, coded)

<!-- v0.2 (2026-07-11): added EN labor co-occurrence keyword list; sharpened labor_signal
     (restraint-vs-neutral decisive test + 3 worked examples); defined the same-paragraph
     context window.
     v1.0 (2026-07-12): mentor-approved and frozen for full coding; automated collection
     complete (Data/scripts/collect_d4.py -> Data/d4_candidates.xlsx).
     v1.1 (2026-07-17): coding executed by LLM agents (Codex / GPT-5.6-Terra, xhigh) rather than
     human coders, at Luis's direction. Independent double-coding + adjudication + verbatim-quote
     verification -> Data/d4_coding.csv/.xlsx; method in Data/d4_coding_reliability.md. -->


> The coding **instrument**, frozen (mentor-approved 2026-07-12).
> Construct = what listed Brazilian firms **state publicly** about their own AI use — *disclosed
> adoption*, not true adoption. One row per **firm-year** (FY2023, FY2024). Every row cites a public
> source URL + access date. Sources: public filings/reports/releases only.
>
> **⚠ Coding was performed by LLM agents, not human hand-coders (v1.1, 2026-07-17, Luis's
> instruction).** Model: Codex / GPT-5.6-Terra (xhigh). Design: independent double-coding of all 36
> firm-years by separate agents, disagreements adjudicated by a third agent, every `evidence_quote`
> verified verbatim against source text. Inter-coder agreement adopt_level 83% / claim_specificity
> 88% / labor_signal 97%. Output: `Data/d4_coding.csv` / `d4_coding.xlsx`; full method +
> reliability: `Data/d4_coding_reliability.md`. **The paper must describe D4 as LLM-coded, not
> hand-coded** — the "double-code ~20%" human-reliability note in §Reliability below is superseded
> by this design. Status: **coded** (guide §11 #1).

## Document set (fixed per firm-year — same for every firm)
1. **Formulário de Referência** (annual) — strategy, risk factors, **employee headcount**.
2. **Annual / integrated / sustainability report** (*Relatório Anual / Integrado*).
3. **Q4 / full-year earnings release** (*Divulgação de Resultados* 4T).
4. **20-F / 6-K** — only for US-listed firms (e.g. cross-listed names).

Retrieved by CLI (CVM IPE index / CVM FRE dataset / SEC EDGAR), snapshotted with access date under `Data/raw/d4_firms/<cd_cvm>/<fiscal_year>/`. Record `doc_type` per evidence row; log which of the four were found.

**Automated collection (run 2026-07-12, `Data/scripts/collect_d4.py`).** All 18 core firms × FY2023–FY2024 collected in one pass → `Data/d4_candidates.xlsx` (sheets: `candidates` | `coverage` | `headcount` | `firms`). Achieved coverage, **stated honestly** — the `coverage` sheet is per firm-year:

| Doc | Found | Note |
|---|---|---|
| Formulário de Referência | **36/36** | every firm-year; also yields the `headcount` field automatically (FRE RH table, latest version, summed across locations) |
| Q4 earnings release | **33/36** | banks file this as *Relatório de Análise Gerencial* or *Press-release* |
| Annual/integrated report | **23/36** | genuinely absent from IPE for several firm-years; announcement notices ("Lançamento do Relatório…") and *Agente Fiduciário* reports are excluded as false matches, not counted as found |
| 20-F | **2/2** | JBS only (the one US-listed core firm; its annual report *is* the 20-F, so its CVM annual-report gap is expected) |

Result: **730 candidate passages, 34/36 firm-years have AI candidates to read.** The 2 with none (Banco do Nordeste FY2023, Banco Mercantil FY2024) are a *finding*, not a collection failure — a firm with zero AI content stays in the sample at `adopt_level` 0. Fiscal-year keying: earnings release by `Data_Referencia` (period end); annual report by `Data_Referencia`, since firms date reports inconsistently — each row carries `doc_date`/`doc_filed` so the coder can verify the year before coding. The collector **surfaces only**; it codes nothing.

## Keyword list (frozen; identical PT+EN protocol for every firm)
**AI terms — PT:** inteligência artificial, IA, aprendizado de máquina, aprendizado profundo, IA
generativa, GenAI, modelos de linguagem, LLM, ciência de dados, análise preditiva, algoritmo(s) de,
automação, automação de processos, RPA, chatbot, assistente virtual/digital, reconhecimento de voz,
visão computacional, processamento de linguagem natural, PLN, agentes de IA, copiloto.
**AI terms — EN:** artificial intelligence, machine learning, deep learning, generative AI, large
language model, LLM, data science, predictive analytics, automation, chatbot, virtual assistant,
computer vision, natural language processing, NLP.
**Labor co-occurrence (for `labor_signal`) — PT:** eficiência, produtividade, quadro de funcionários,
número de colaboradores, headcount, efetivo, reestruturação, redução de custos, otimização,
requalificação/reskilling/upskilling, capacitação, contratação, vagas, demissão, corte de pessoal,
realocação, postos de trabalho.
**Labor co-occurrence (for `labor_signal`) — EN:** efficiency, productivity, workforce, headcount, staff,
number of employees, full-time equivalents / FTEs, restructuring, cost reduction, cost savings,
cost-to-income, efficiency ratio, operating leverage, optimization, streamline, reskilling / upskilling,
training, hiring, recruiting, job openings / vacancies / positions, layoffs, job cuts, redundancies,
workforce reduction, downsizing, redeployment / reallocation, attrition, roles, "do more with less".

**Inclusion rules (apply consistently):**
- Precision agriculture / "agricultura digital" / IoT counts as AI **only when the firm itself ties it
  to AI/ML/analytics** — bare "sensores", "GPS", "drones" without AI framing does **not** count.
- Generic "transformação digital" / "digitalização" without AI language does **not** count as AI adoption.
- Rules-based automation / RPA **counts** but is tagged in `use_case` (flag as non-ML automation).

## Fields & anchored definitions

**`adopt_level`** — level of *disclosed* AI adoption (code the highest the disclosures support):
- **0 = none disclosed** — no AI mention, OR only aspiration/intent with no described use ("*pretendemos investir em IA*"). A firm with zero AI content stays in the sample at 0.
- **1 = piloting / partial** — a described AI use at pilot / limited / testing stage, or one narrow deployment.
- **2 = deployed at scale** — a **named, operating** AI system in production across operations or customers ("*o assistente virtual BIA atende…*"). Never awarded for aspiration.

**`claim_specificity`** — how concrete the strongest claim is (guards against AI-washing):
- **0 = vague** (AI mentioned, no named use/system) · **1 = named** (specific use case/system named) ·
  **2 = quantified** (named use **with** a number: users served, % automated, cost/time saved).

**`use_case`** — short tag(s): customer-service/chatbot · credit/underwriting/risk · fraud/AML ·
process-automation/RPA · precision-ag · supply-chain/logistics · marketing/personalization · HR/people ·
data-analytics · other (free text). Multiple allowed.

**`labor_signal`** — the firm's framing of AI's workforce implication, **in the same context** as the AI
disclosure (a *stated stance*, not a measured employment change):
- **hiring** — AI linked to new/growing roles (AI teams, hiring data scientists, AI talent).
- **neutral** — AI mentioned with no workforce framing, or framed as *augmenting/assisting* workers or a *process*, with no link to headcount size, growth, or personnel cost.
- **restraint** — AI efficiency/productivity/cost framing **tied to the workforce** (headcount, staffing, operating leverage, cost-to-income/efficiency ratio, or "without adding people"), implying slower headcount growth — no explicit cuts.
- **cuts** — AI/automation linked to reducing headcount/roles (layoffs, eliminating or redeploying-out positions).
- Decision rule: code the **dominant** signal in the AI-labor context; if none present → **neutral**; log ambiguous cases in `notes`.

**Restraint vs neutral — the decisive call** (the main reliability risk; efficiency/productivity language *alone does not* make it restraint). Apply one test: **does the passage tie AI to the size, growth, or cost of the workforce?**
- Tied to headcount / staffing / personnel cost / operating leverage / cost-to-income → **restraint**.
- Tied only to output, quality, speed, or a *worker's* own productivity (augmentation) → **neutral**.
- Explicit reduction of roles/headcount → **cuts**.

**Worked examples.**
1. *"Os ganhos de eficiência com IA sustentaram a expansão do banco **sem aumento proporcional do quadro de funcionários**."* → **restraint** — efficiency explicitly tied to headcount not growing with the business.
2. *"Nossos assistentes virtuais de IA **aumentam a produtividade dos atendentes** e elevam a satisfação do cliente."* → **neutral** — worker productivity = augmentation, no headcount/cost-of-labor link. (The classic trap: *produtividade/*productivity on its own ≠ restraint.)
3. *(20-F, EN)* "AI-based process automation reduced our cost-to-serve and **enabled a reduction of roles** in back-office operations." → **cuts** — explicit role reduction. *(By contrast, **hiring** is the unambiguous case: "we expanded our data-science team to build our AI platform.")*

**Context window (co-occurrence unit).** The labor framing and the AI mention must fall in the **same paragraph** — or a directly adjacent sentence that continues the same AI statement (its subject is the AI system/initiative). Co-occurrence at the **section or whole-report level does not count**: a workforce/headcount statement in a different paragraph is general HR commentary, not a `labor_signal`. If no qualifying same-paragraph passage exists → **neutral**. For tables/bulleted lists, a bullet plus its parent heading counts as one paragraph. Confirm co-occurrence **in the source document**, never from the CLI snippet alone.

**`evidence_quote`** — one brief verbatim quote (≤ ~40 words) supporting the codes. **`source_url`**,
**`access_date`**, **`doc_type`**. **`headcount`** — total employees from the Formulário de Referência
(objective companion variable). **`notes`** — ambiguities, competing signals, coder uncertainty.

## Procedure
1. CLI downloads the fixed document set + surfaces candidate passages (keyword hits with context) → `Data/raw/d4_firms/…` + a candidates file.
2. Coder reads candidates **in the source document** (never code from the snippet alone), assigns fields, selects the quote, records source + date.
3. **Ambiguity logged**, not silently resolved. **Pilot** on 2 firms (1 bank, 1 ag) → adjust once → **freeze** this codebook.

## Reliability & robustness
- **Double-code ~20%** (≈4 firms): second coder *(mentor — pending)* or blind self-re-code after ≥2 weeks; report percent agreement in Limitations.
- **Robustness:** report T4 tallies twice — all AI mentions vs. `claim_specificity ≥ 1` only — to show AI-washing isn't driving the pattern.

## Integrity (binding)
Public sources only; brief quote + URL + access date every row; sample reported **complete** (zeros kept);
exhibit labeled **exploratory**, non-representative (listed-firm bias). Associational language only. No COI.
