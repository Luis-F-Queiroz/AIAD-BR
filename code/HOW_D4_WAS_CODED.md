# How the D4 codes were produced (LLM coding run)

This documents the exact process behind `data/d4_coding.csv`, for transparency and (partial)
reproducibility. Coding was done by an LLM (Codex / GPT-5.6-Terra, xhigh), not human hand-coding.

## Inputs the model saw
- **The instrument:** `code/coding_prompt.txt` — the verbatim instruction given to every coder,
  containing the full codebook (definitions, inclusion rules, the restraint-vs-neutral test, worked
  examples) and hard output rules (code only from the provided evidence; quote verbatim; a firm-year
  with no AI passages → `adopt_level` 0).
- **The evidence:** for each firm-year, the AI-mention passages surfaced by `collect_d4.py` (the same
  content as `data/d4_candidates.xlsx`), grouped by firm-year and appended to the instrument.
- **The output contract:** `code/coding_schema.json` — a JSON schema the model's answer had to satisfy
  (one object per firm-year with all coded fields), enforced via the runner's structured-output mode.

## Procedure
1. **Double-coding.** The 36 firm-years were split into 4 batches of 9. Each batch was coded twice, by
   two independent agent runs (8 runs total) — read-only, no web access, coding only from the evidence.
2. **Merge + agreement.** The two codings were compared field-by-field to compute inter-coder agreement
   and locate disagreements (see `docs/methods_and_reliability.md`).
3. **Adjudication.** The 8 disagreeing firm-years were sent to a 9th agent with both codings + the
   evidence; it chose the final codes per the codebook.
4. **Quote verification.** Every final `evidence_quote` was checked programmatically to be an exact
   substring of that firm-year's collected passages; the one adjudicator quote that failed was replaced
   with the verified quote from the coder it sided with. Final dataset: 100% verbatim.

## Reproducibility note
The collection step (`collect_d4.py`) is fully deterministic from the public sources. The LLM coding
step is not bit-for-bit reproducible (model outputs vary), but the instrument, evidence, schema, and
this procedure are all provided so the coding can be re-run or audited. The agreement statistics and
verbatim-quote guarantee are the checks on that step.
