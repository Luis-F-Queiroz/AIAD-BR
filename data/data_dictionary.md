# D4 coded dataset — data dictionary (`d4_coding.csv`)

One row per **firm-year** (18 firms × FY2023 and FY2024 = 36 rows). The unit is a
listed Brazilian firm's *disclosed* AI adoption in a fiscal year — what the firm
**states publicly** about its own AI use, not verified true adoption.

| Column | Type | Meaning |
|---|---|---|
| `firm` | text | Company name (as in the CVM registry). |
| `sector` | text | Study sector: `banking` · `retail` · `agribusiness`. |
| `size_tercile` | text | Size tercile within sector: `large` · `mid` · `small`. |
| `cd_cvm` | text | CVM registration code (the firm's Brazilian regulator ID). |
| `year` | int | Fiscal year (2023 or 2024). |
| `adopt_level` | 0/1/2 | Disclosed AI adoption: **0** none disclosed · **1** piloting/partial · **2** deployed at scale (a named, operating system). |
| `claim_specificity` | 0/1/2 / blank | Concreteness of the strongest claim (AI-washing guard): **0** vague · **1** named use/system · **2** quantified. Blank when `adopt_level`=0. |
| `labor_signal` | text | Firm's framing of AI's workforce implication, in the AI context: `hiring` · `neutral` · `restraint` · `cuts`. |
| `use_case` | text | `;`-separated tags (customer-service/chatbot, credit/underwriting/risk, fraud/AML, process-automation/RPA, precision-ag, supply-chain/logistics, marketing/personalization, HR/people, data-analytics, other). |
| `use_case_other` | text | Free text when `use_case` includes `other`. |
| `evidence_quote` | text | A verbatim quote from the firm's filing supporting the codes (100% verified as an exact substring of the source; empty when `adopt_level`=0). |
| `source_url` | url | Public URL of the document the quote came from (CVM/SEC). |
| `access_date` | date | When the document was retrieved. |
| `doc_type` | text | Which document the evidence came from (annual/integrated report, Q4 earnings release, Formulário de Referência, 20-F). |
| `headcount` | int | Total employees, from the firm's Formulário de Referência (objective companion variable). |
| `notes` | text | Coder rationale / ambiguity flag. Rows tagged `[THIN COVERAGE …]` had a non-machine-readable FRE and minimal other text, so their `0` reflects minimal readable disclosure, not a confident zero. |
| `coding_method` | text | `double-coded (A=B)` where both independent coders agreed; `adjudicated` where a third agent resolved a disagreement. |
