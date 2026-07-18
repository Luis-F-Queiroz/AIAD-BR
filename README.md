# AIAD-BR — AI Adoption Disclosures, Brazil (FY2023–2024)

A firm-year dataset of **disclosed** artificial-intelligence adoption by **18 listed Brazilian firms** —
6 each in **banking**, **retail / customer service**, and **agribusiness** (two size terciles per sector) —
across fiscal years **2023 and 2024** (36 firm-years). It is dataset **D4** of the research paper
*"Equalizer or Divider? AI Exposure, Productivity, and the Distribution of Gains Across Brazilian
Banking, Customer Service, and Agribusiness"* (Luis Queiroz & Jameson Augustin, Polygence).

> **What "disclosed adoption" means.** Each row records what a firm **states publicly** about its own
> AI use — not verified or true adoption. AI *exposure* (potential) and AI *adoption* (what firms say
> they do) are kept strictly separate throughout the project. This exhibit is **exploratory** and
> **not statistically representative** (listed-firm sample); read it descriptively, not causally.

## How this dataset was built — please read

- **Collection was automated (no AI/LLM).** The firms' public disclosures were retrieved and parsed by
  a script (`code/collect_d4.py`): Brazilian CVM filings (annual/integrated reports, Q4 earnings
  releases, the *Formulário de Referência*) and, for the one US-listed firm, its SEC 20-F. The script
  downloads each document, extracts the text (including decoding the base64-embedded FRE and OCR for
  image-only pages), and surfaces the passages that mention AI. Employee headcount is read from the
  structured *Formulário de Referência* tables.

- **Coding was performed by a large language model.** Assigning each firm-year's codes
  (`adopt_level`, `claim_specificity`, `labor_signal`, `use_case`) against the fixed codebook was done
  by an LLM (**Codex / GPT-5.6-Terra**), *not* by human hand-coding. To make this rigorous and checkable:
  1. **Independent double-coding** — all 36 firm-years were coded twice, by two separate agent runs.
  2. **Adjudication** — the 8 firm-years where the two runs disagreed were resolved by a third agent
     that saw both codings and the evidence.
  3. **Verbatim-quote verification** — every `evidence_quote` was checked programmatically to be an
     exact substring of the firm's own filing. **Result: 100% verbatim, zero fabricated quotes.**

  Inter-coder agreement between the two independent codings: **adopt_level 83%**, **claim_specificity
  88%**, **labor_signal 97%** (all disagreements were adjacent categories). Full method:
  [`docs/methods_and_reliability.md`](docs/methods_and_reliability.md).

## The data at a glance

- **File:** [`data/d4_coding.csv`](data/d4_coding.csv) (36 rows) — column-by-column meaning in
  [`data/data_dictionary.md`](data/data_dictionary.md).
- **Disclosed-adoption spread** (`adopt_level` 0/1/2): **16 / 11 / 9** firm-years.
- **By sector** (mean adopt_level): **banking 1.08 ≈ retail 1.00 > agribusiness 0.33** — the same
  ordering as the study's AI-*exposure* ranking.
- **Labor framing** (`labor_signal`): mostly **neutral** (32/36), with a few hiring/restraint — firms
  rarely tie AI to their workforce in these disclosures.
- Each coded row carries the supporting **verbatim quote + source URL + access date**, and the firm's
  **headcount**.

## What's in this repository

```
data/
  d4_coding.csv / .xlsx      the coded dataset (the headline) + a reliability sheet
  d4_candidates.xlsx         the AI passages surfaced from filings — the evidence behind each code
  d4_sampling_frame.csv      the 18 firms and how they were selected (+ exclusions)
  d4_frame_exclusions.csv
  data_dictionary.md         every column of d4_coding.csv explained
docs/
  codebook.md                the coding instrument (definitions, decision rules, examples)
  methods_and_reliability.md  how it was collected + coded, agreement stats, caveats
code/
  collect_d4.py              the collection pipeline (reproduces data/d4_candidates.xlsx)
  coding_prompt.txt          the exact instruction the coding LLM received
  coding_schema.json         the structured-output schema the LLM had to fill
  HOW_D4_WAS_CODED.md        step-by-step account of the LLM coding run
```

The ~1.2 GB of raw filings are **not** stored here (they are reproducible with `code/collect_d4.py`).

## Reproduce it

Collection: `python3 code/collect_d4.py` (needs PyMuPDF + openpyxl; macOS Vision OCR fallback for
image-only PDFs) → rebuilds `data/d4_candidates.xlsx` from the public sources. The LLM coding step is
documented in [`code/HOW_D4_WAS_CODED.md`](code/HOW_D4_WAS_CODED.md).

## Cite

A `CITATION.cff` is included (GitHub shows a **"Cite this repository"** button). In short:

> Queiroz, L., & Augustin, J. (2026). *AIAD-BR — AI Adoption Disclosures, Brazil
> (FY2023–2024)* [Data set]. GitHub. https://github.com/Luis-F-Queiroz/AIAD-BR

## Limitations

- **Disclosed, not true, adoption** — firms that say little about AI may still use it, and vice versa.
- **Exploratory, non-representative** — 18 listed firms, chosen by sector × size; not a random sample.
- **LLM-coded** — see the method and agreement statistics above; codes reflect the model's reading of
  the disclosures under a fixed codebook, with the reliability safeguards described.
- **Two thin firm-years** (Banco do Nordeste FY2023, Banco Mercantil FY2024): their *Formulário de
  Referência* was not machine-readable and little other text was available, so their `adopt_level` 0
  means *minimal readable disclosure*, not a confident "no AI." Flagged in the row `notes`.

## License

Data: **CC BY 4.0**. Code: **MIT** (see [`LICENSE`](LICENSE)). Underlying firm disclosures are public
records of CVM (Brazil) and the SEC (US); only short verbatim quotes are reproduced here as evidence.
