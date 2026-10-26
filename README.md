# ifrs15-contract-reviewer

**Automated contract scanning for IFRS 15 and ASPE 3400 revenue recognition risks.**

Built to reflect content contract review work at an Amazon streaming subsidiary. Parses PDF contracts or pasted text to flag unusual revenue recognition terms — variable consideration, bundled arrangements, principal vs. agent, acceptance conditions, right-of-access vs. right-of-use, and significant financing components — against the IFRS 15 five-step model and ASPE Section 3400.

[![License: MIT](https://img.shields.io/badge/License-MIT-teal.svg)](LICENSE) [![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org) [![Tests: pytest](https://img.shields.io/badge/Tests-pytest-green.svg)](tests/) [![100% Local](https://img.shields.io/badge/Data%20Privacy-100%25%20Local-brightgreen.svg)](#data-privacy)

---

## Live Demo
**[Try it live →](https://www.wong.cpa/ifrs15-contract-reviewer/src/)**. Or open `src/index.html` locally → click **Load Sample Text** for an instant demo, or drop `tests/fixtures/sample_content_license_agreement.pdf`.

---

## Features

| Feature | Detail |
|---|---|
| IFRS 15 five-step coverage | Steps 1–5 plus principal/agent and ASPE 3400 |
| PDF parsing (browser) | PDF.js extracts text locally — no server required |
| PDF parsing (CLI) | pdfplumber — runs 100% locally |
| Text paste option | Copy from any source and paste directly |
| Risk classification | HIGH / MEDIUM / LOW with standard references |
| Contract excerpts | Exact clause text shown for each flagged rule |
| Step coverage summary | Dashboard showing which IFRS 15 steps have flags |
| CSV export | Audit-ready flag log |

---

## Repository Structure

```
ifrs15-contract-reviewer/
├── src/
│   ├── index.html              # Browser web app (PDF drop or text paste)
│   └── contract_reviewer.py    # Python CLI (pdfplumber for PDF parsing)
├── tests/
│   ├── test_contract_reviewer.py  # pytest suite — 11 rules, risk levels, integration
│   └── fixtures/
│       └── sample_content_license_agreement.pdf  # Synthetic streaming content contract
├── requirements.txt
├── .gitignore
└── LICENSE
```

---

## Quick Start

**Web app:** `open src/index.html` → click Load Sample Text or drop the PDF fixture.

**CLI:**
```bash
git clone https://github.com/wongcpa/ifrs15-contract-reviewer.git
cd ifrs15-contract-reviewer
pip install pdfplumber
python src/contract_reviewer.py
# Enter: tests/fixtures/sample_content_license_agreement.pdf
```

**Tests:** `pip install pytest && pytest tests/ -v`

---

## IFRS 15 Rules Covered

| Rule ID | Issue | Risk |
|---|---|---|
| IFRS15-S1-01 | Contingent contract effectiveness | HIGH |
| IFRS15-S2-01 | Bundled / multi-element arrangement | HIGH |
| IFRS15-S2-02 | Content license right-of-access vs. right-of-use | HIGH |
| IFRS15-S3-01 | Variable consideration (royalties, milestones, per-stream) | HIGH |
| IFRS15-S3-02 | Significant financing component (terms beyond 12 months; IFRS 15.63 practical expedient applied) | MEDIUM |
| IFRS15-S3-03 | Non-cash / in-kind consideration | MEDIUM |
| IFRS15-S4-01 | Discount allocation on bundled contracts | LOW |
| IFRS15-S5-01 | Over-time recognition (ratable, subscription) | LOW |
| IFRS15-S5-02 | Acceptance / UAT delivery condition | HIGH |
| IFRS15-B34 | Principal vs. agent (gross vs. net revenue) | HIGH |
| ASPE3400-01 | Completed-contract method indicator | MEDIUM |

---

## Data Privacy
PDF text is extracted entirely in-browser via PDF.js or locally via pdfplumber. No contract content is transmitted to any server or API.

---

## Author

**Jimmy Wong, CPA (WA), CPA (Canada)**
[www.wong.cpa](https://www.wong.cpa) · [LinkedIn](https://www.linkedin.com/in/wongjimmy/) · [GitHub @wongcpa](https://github.com/wongcpa)

*Automated flagging only. Revenue recognition determination requires professional CPA judgment.*
