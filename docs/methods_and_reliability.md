# D4 — methods & reliability

## Construct
`D4` records **disclosed** AI adoption: what each listed Brazilian firm *states publicly* about its own
AI use, per firm-year (FY2023, FY2024). It is deliberately separate from AI *exposure* (potential task
overlap with AI, measured elsewhere in the study) and from verified/true adoption.

## Sample
18 firms — 6 per sector (banking, retail/customer service, agribusiness), two per size tercile
(large/mid/small) — selected by size (total assets for banks, net revenue otherwise) from the pool of
CVM-listed firms in each sector×tercile cell. See `data/d4_sampling_frame.csv` (+ `_exclusions.csv`).
The sample is **exploratory and non-representative**; the zeros are kept (a firm with no disclosed AI
stays in the sample at `adopt_level` 0).

## Collection (automated; no LLM)
`code/collect_d4.py` retrieves and parses each firm-year's public documents:
- **CVM** (Brazil): annual/integrated report, Q4 earnings release, and the *Formulário de Referência*
  (FRE), via the CVM open-data IPE index and FRE dataset.
- **SEC** (US): the 20-F, for the one US-listed firm (JBS), via EDGAR.
Text extraction uses PyMuPDF, with (a) an OCR fallback (Apple Vision) for image-only or font-garbled
PDFs, and (b) base64 decoding of the FRE — the FRE "WEB" XML embeds its real content as base64-encoded
PDF sections, which must be decoded to recover the narrative. AI-mention passages are surfaced with
context into `data/d4_candidates.xlsx`; employee **headcount** is read from the FRE structured tables.
Achieved document coverage is recorded per firm-year (FRE 36/36; earnings release 33/36; annual report
23/36 — many firms file no standalone report; 20-F 2/2).

## Coding (LLM)
The codes were assigned by a large language model — **Codex / GPT-5.6-Terra**, reasoning effort xhigh —
applying the fixed instrument in `docs/codebook.md` to the surfaced evidence. This is **not** human
hand-coding. The design mirrors a standard double-coding reliability protocol:

1. **Independent double-coding.** All 36 firm-years were coded twice, by two separate agent runs that
   did not see each other's output (four batches × two passes = eight coder agents).
2. **Adjudication.** The 8 firm-years where the two runs disagreed on a coded field were resolved by a
   third agent that saw both codings plus the evidence and decided per the codebook.
3. **Verbatim-quote verification.** Every `evidence_quote` in the final dataset was checked to be an
   exact substring of the firm-year's collected passages. **100% passed; no fabricated quotes.**

### Inter-coder agreement (the two independent codings, before adjudication)
| Field | Agreement |
|---|---|
| adopt_level | 30/36 = 83% |
| claim_specificity | 32/36 = 88% |
| labor_signal | 35/36 = 97% |

All disagreements were between adjacent categories (0↔1, 1↔2, neutral↔restraint); there were no gross
conflicts. The `coding_method` column marks each row `double-coded (A=B)` or `adjudicated`.

## Caveats
- **Disclosed ≠ true adoption.** Silence is not proof of non-use.
- **Non-representative** listed-firm sample; descriptive/associational reading only.
- **LLM-coded**, with the safeguards above; codes reflect the model's reading under the codebook.
- **Two thin firm-years** (Banco do Nordeste FY2023, Banco Mercantil FY2024): the FRE did not decode to
  readable text and little else was available, so `adopt_level` 0 there means *minimal readable
  disclosure*, not a confident zero (flagged in `notes`). Eight further zeros come from substantial,
  clean documents with genuinely no AI disclosure (e.g. JBS, whose 3 MB of text includes its 20-F).
