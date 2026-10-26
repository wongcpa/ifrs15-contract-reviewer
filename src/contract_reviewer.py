"""
contract_revenue_reviewer.py
=============================
Contract PDF Revenue Term Extractor & IFRS 15 / ASPE 3400 Risk Reviewer

Usage:
  python contract_revenue_reviewer.py

You will be prompted for:
  - PDF contract file path

Test fixture: sample_content_license_agreement.pdf

DEPENDENCY: pdfplumber — runs 100% locally. No PDF content is transmitted.
  Install: pip install pdfplumber

Author: Jimmy Wong, CPA
DATA PRIVACY: pdfplumber extracts text locally. No data leaves your machine.
"""

import csv
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# ---------------------------------------------------------------------------
# SECTION 1: DEPENDENCY CHECK
# ---------------------------------------------------------------------------

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ---------------------------------------------------------------------------
# SECTION 2: IFRS 15 & ASPE 3400 RULES
# ---------------------------------------------------------------------------

REVENUE_RULES: List[Dict] = [
    {
        "rule_id": "IFRS15-S1-01", "name": "Contingent contract effectiveness",
        "pattern": r"\b(contingent\s+upon|conditional\s+(on|upon)|effective\s+only\s+if|conditioned\s+upon|upon\s+receipt\s+of\s+regulatory|subject\s+to\s+(the\s+)?(receipt\s+of\s+)?(regulatory|board|shareholder|stockholder|governmental|government)\s+approval)\b",
        "standard": "IFRS 15.9 / ASPE 3400.06", "risk_level": "HIGH",
        "flag_reason": "Contract effectiveness is contingent — may not meet IFRS 15 Step 1 criteria.",
        "guidance": "Assess all five IFRS 15.9 criteria before recognizing revenue. Defer if conditions unresolved.",
    },
    {
        "rule_id": "IFRS15-S2-01", "name": "Bundled / multi-element arrangement",
        "pattern": r"\b(bundle[d]?|package[d]?|combined\s+offering|multi.element|integrated\s+solution|all-inclusive|combined\s+license|bundled\s+package|multiple\s+deliverables)\b",
        "standard": "IFRS 15.22-30 / ASPE 3400.09", "risk_level": "HIGH",
        "flag_reason": "Bundled arrangement detected — requires identification of distinct performance obligations.",
        "guidance": "Apply IFRS 15.27 'distinct' test. Allocate transaction price using SSP for each POB.",
    },
    {
        "rule_id": "IFRS15-S2-02", "name": "Content license: right-of-access vs. right-of-use",
        "pattern": r"\b(streaming\s+rights|exclusive\s+license|non-exclusive\s+license|license\s+to\s+exhibit|broadcast\s+rights|distribution\s+rights|content\s+license|right-of-access)\b",
        "standard": "IFRS 15.B58-B62", "risk_level": "HIGH",
        "flag_reason": "IP license detected. Determine if right-of-access (over time) vs. right-of-use (point in time).",
        "guidance": "Right-of-access if entity's activities significantly affect the IP. Streaming content often qualifies.",
    },
    {
        "rule_id": "IFRS15-S3-01", "name": "Variable consideration",
        "pattern": r"\b(royalt(y|ies)|usage.based|per.view|per.stream|milestone\s+payment|performance.based|earn.out|success\s+fee|revenue\s+share|minimum\s+guarantee|MG|advance\s+against\s+royalties|escalat(e|ing|or)|tiered\s+pricing)\b",
        "standard": "IFRS 15.50-55 / ASPE 3400", "risk_level": "HIGH",
        "flag_reason": "Variable consideration detected. Estimate and constrain where reversal is probable.",
        "guidance": "IFRS 15.56: Include only to extent significant reversal won't occur. Apply royalty exception (B63) for sales-based royalties on IP.",
    },
    {
        "rule_id": "IFRS15-S3-02", "name": "Significant financing component",
        # Terms of 12 months or less fall under the IFRS 15.63 practical expedient, so only longer terms are flagged.
        "pattern": r"\b(net\s+(36[6-9]|3[7-9]\d|[4-9]\d\d|\d{4,})|deferred\s+payment|payment\s+in\s+([2-9]|\d{2,})\s+years|long.term\s+payment|installments?\s+over\s+(1[3-9]|[2-9]\d|\d{3,})\s+months|installments?\s+over\s+([2-9]|\d{2,})\s+years)\b",
        "standard": "IFRS 15.60-65", "risk_level": "MEDIUM",
        "flag_reason": "Payment terms extend beyond 12 months — possible significant financing component.",
        "guidance": "IFRS 15.63: no adjustment if payment is within 12 months of performance. Beyond that, assess significance and adjust the transaction price using an appropriate discount rate.",
    },
    {
        "rule_id": "IFRS15-S3-03", "name": "Non-cash consideration",
        "pattern": r"\b(barter|in.kind|equity\s+consideration|shares?\s+as\s+payment|non.monetary|non.cash|promotional\s+services|in-kind\s+promotional)\b",
        "standard": "IFRS 15.66-69", "risk_level": "MEDIUM",
        "flag_reason": "Non-cash consideration detected. Measure at fair value at contract inception.",
        "guidance": "If fair value cannot be estimated, measure by reference to SSP of goods/services transferred.",
    },
    {
        "rule_id": "IFRS15-S4-01", "name": "Discount on bundled contracts",
        "pattern": r"\b(discount(ed)?|reduced\s+rate|promotional\s+price|package\s+discount|bundled\s+discount|combined\s+price)\b",
        "standard": "IFRS 15.81-83", "risk_level": "LOW",
        "flag_reason": "Discount applied to bundled arrangement. Allocate to all POBs unless evidence of specificity.",
        "guidance": "Allocate proportionately unless observable evidence exists for allocation to a specific POB subset.",
    },
    {
        "rule_id": "IFRS15-S5-01", "name": "Over-time recognition trigger",
        "pattern": r"\b(ratable(ly)?|straight.line|pro.rat(a|ed)|as\s+services\s+are\s+rendered|continuous\s+(access|service)|subscription|monthly\s+license\s+fee)\b",
        "standard": "IFRS 15.35", "risk_level": "LOW",
        "flag_reason": "Over-time recognition language detected. Confirm criteria are met.",
        "guidance": "Recognize over time only if customer simultaneously receives/consumes benefits, or entity has right to payment for performance to date.",
    },
    {
        "rule_id": "IFRS15-S5-02", "name": "Acceptance / delivery condition",
        "pattern": r"\b(upon\s+acceptance|client\s+acceptance|customer\s+sign.off|final\s+acceptance|acceptance\s+testing|UAT|go.live)\b",
        "standard": "IFRS 15.38 / ASPE 3400.07", "risk_level": "HIGH",
        "flag_reason": "Formal acceptance clause detected. Revenue may be deferred until acceptance is received.",
        "guidance": "Assess whether acceptance is substantive. If yes, defer revenue until acceptance.",
    },
    {
        "rule_id": "IFRS15-B34", "name": "Principal vs. agent indicator",
        "pattern": r"\b(agent|commission|net\s+settlement|pass.through|on\s+behalf\s+of|intermediary|resell(er)?|sub.licens(e|ing)|gross\s+proceeds|net\s+proceeds)\b",
        "standard": "IFRS 15.B34-B38", "risk_level": "HIGH",
        "flag_reason": "Principal vs. agent indicators detected. Gross vs. net revenue presentation at risk.",
        "guidance": "Determine if entity controls the good/service before transfer. Sub-licensing requires careful analysis.",
    },
    {
        "rule_id": "ASPE3400-01", "name": "Completed-contract method indicator",
        "pattern": r"\b(upon\s+completion|on\s+completion|when\s+project\s+is\s+complete|at\s+project\s+completion|final\s+delivery\s+only)\b",
        "standard": "ASPE 3400.19", "risk_level": "MEDIUM",
        "flag_reason": "Completed-contract language. Under ASPE may indicate completed-contract method appropriate.",
        "guidance": "ASPE 3400.19 allows completed-contract when outcome cannot be reliably estimated. IFRS 15 does not permit this method.",
    },
]

RISK_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

STEP_MAP = {
    "Step 1 — Identify Contract":       ["IFRS15-S1-01"],
    "Step 2 — Performance Obligations": ["IFRS15-S2-01", "IFRS15-S2-02"],
    "Step 3 — Transaction Price":       ["IFRS15-S3-01", "IFRS15-S3-02", "IFRS15-S3-03"],
    "Step 4 — Allocate Price":          ["IFRS15-S4-01"],
    "Step 5 — Recognize Revenue":       ["IFRS15-S5-01", "IFRS15-S5-02"],
    "Principal vs. Agent":              ["IFRS15-B34"],
    "ASPE 3400 Considerations":         ["ASPE3400-01"],
}

# ---------------------------------------------------------------------------
# SECTION 3: FILE INPUT WITH RETRY LOGIC
# ---------------------------------------------------------------------------

def prompt_for_file(max_attempts: int = 3) -> str:
    """
    Prompt for a PDF contract file path.
    Re-prompts up to max_attempts times on failure.
    """
    print("\n" + "=" * 64)
    print("  CONTRACT REVENUE RECOGNITION REVIEWER")
    print("  Standards: IFRS 15 / ASPE 3400")
    print("=" * 64)

    if not PDF_AVAILABLE:
        print("\n  ⚠  pdfplumber not installed.")
        print("  Install it with: pip install pdfplumber")
        print("  Then re-run this program.")
        sys.exit(1)

    print("\nTest fixture: sample_content_license_agreement.pdf")

    for attempt in range(1, max_attempts + 1):
        raw = input("\nPDF contract file path: ").strip()
        path = Path(raw)

        if not path.exists():
            print(f"  ERROR: File not found: '{raw}'")
        elif path.suffix.lower() != ".pdf":
            print(f"  ERROR: Expected a .pdf file, got '{path.suffix}'")
        else:
            # Quick check — try to open it
            try:
                with pdfplumber.open(str(path)) as pdf:
                    if len(pdf.pages) == 0:
                        print("  ERROR: PDF has no pages.")
                    else:
                        print(f"  ✔ PDF opened: {len(pdf.pages)} page(s) found.")
                        return str(path)
            except Exception as e:
                print(f"  ERROR: Could not open PDF: {e}")

        if attempt < max_attempts:
            print(f"  Attempt {attempt}/{max_attempts}. Please try again.")

    print(f"\n  FATAL: Maximum attempts ({max_attempts}) reached. Exiting.")
    sys.exit(1)


def prompt_for_output(default: str = "contract_revenue_flags.csv") -> str:
    raw = input(f"\nOutput CSV filename [{default}]: ").strip()
    return raw if raw else default


# ---------------------------------------------------------------------------
# SECTION 4: EXTRACTION & REVIEW ENGINE
# ---------------------------------------------------------------------------

def extract_text(pdf_path: str) -> str:
    """Extract all text from a PDF using pdfplumber (local only)."""
    parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                parts.append(f"\n--- PAGE {i} ---\n{text}")
    return "\n".join(parts)


def review_contract(text: str, contract_name: str) -> List[Dict]:
    """Apply all revenue recognition rules to contract text."""
    flags = []
    for rule in REVENUE_RULES:
        matches = list(re.finditer(rule["pattern"], text, re.IGNORECASE))
        if not matches:
            continue
        snippets = []
        for m in matches[:3]:
            start   = max(0, m.start() - 60)
            end     = min(len(text), m.end() + 60)
            snippet = "..." + text[start:end].replace("\n", " ").strip() + "..."
            snippets.append(snippet)
        flags.append({
            "contract":    contract_name,
            "rule_id":     rule["rule_id"],
            "name":        rule["name"],
            "standard":    rule["standard"],
            "risk_level":  rule["risk_level"],
            "flag_reason": rule["flag_reason"],
            "guidance":    rule["guidance"],
            "match_count": len(matches),
            "snippets":    snippets,
        })
    return flags


# ---------------------------------------------------------------------------
# SECTION 5: REPORTING
# ---------------------------------------------------------------------------

def print_report(flags: List[Dict], contract_name: str) -> None:
    """Print a formatted revenue recognition risk report."""
    flags_sorted = sorted(flags, key=lambda x: RISK_ORDER.get(x["risk_level"], 3))
    high   = [f for f in flags_sorted if f["risk_level"] == "HIGH"]
    medium = [f for f in flags_sorted if f["risk_level"] == "MEDIUM"]
    low    = [f for f in flags_sorted if f["risk_level"] == "LOW"]

    div = "=" * 80
    markers = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}

    print(f"\n{div}")
    print("  CONTRACT REVENUE RECOGNITION REVIEW")
    print(f"  Contract: {contract_name}")
    print(f"  Standards: IFRS 15 / ASPE Section 3400")
    print(f"  Review Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"  Flags: {len(high)} HIGH  |  {len(medium)} MEDIUM  |  {len(low)} LOW")
    print(div)

    for risk_level, group in [("HIGH", high), ("MEDIUM", medium), ("LOW", low)]:
        if not group:
            continue
        print(f"\n  {markers[risk_level]} {risk_level} RISK FLAGS")
        print("  " + "-" * 70)
        for flag in group:
            print(f"\n  [{flag['rule_id']}] {flag['name']}")
            print(f"  Standard: {flag['standard']}")
            print(f"  Matches:  {flag['match_count']} clause(s)")
            print(f"\n  Issue:    {flag['flag_reason']}")
            print(f"\n  Guidance: {flag['guidance']}")
            if flag["snippets"]:
                print(f"\n  Excerpts:")
                for s in flag["snippets"]:
                    print(f'    "{s}"')

    print(f"\n\n  IFRS 15 FIVE-STEP COVERAGE SUMMARY")
    print("  " + "-" * 70)
    flagged_ids = {f["rule_id"] for f in flags}
    for step, rule_ids in STEP_MAP.items():
        hits   = [r for r in rule_ids if r in flagged_ids]
        status = f"⚠  {len(hits)} flag(s)" if hits else "✔  No issues"
        print(f"  {step:<42}  {status}")

    print(f"\n{div}")
    print("  DISCLAIMER: Automated review only. Final determination requires")
    print("  professional judgment by a qualified CPA.")
    print(div)


def export_csv(flags: List[Dict], filepath: str) -> None:
    """Export flagged issues to CSV."""
    if not flags:
        return
    rows = [{
        "contract":    f["contract"],
        "rule_id":     f["rule_id"],
        "name":        f["name"],
        "standard":    f["standard"],
        "risk_level":  f["risk_level"],
        "matches":     f["match_count"],
        "flag_reason": f["flag_reason"],
    } for f in flags]
    with open(filepath, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n  ✔ Flags exported to: {filepath}")


# ---------------------------------------------------------------------------
# SECTION 6: MAIN
# ---------------------------------------------------------------------------

def main():
    pdf_path    = prompt_for_file()
    output_path = prompt_for_output()

    contract_name = Path(pdf_path).stem

    print(f"\nExtracting text from: {pdf_path}")
    text = extract_text(pdf_path)
    print(f"Extracted {len(text):,} characters.")

    print("Reviewing against IFRS 15 and ASPE 3400 rules...")
    flags = review_contract(text, contract_name)

    print_report(flags, contract_name)
    export_csv(flags, output_path)


if __name__ == "__main__":
    # Report symbols (✔, →) must print even when output is redirected on Windows.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
