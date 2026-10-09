#!/usr/bin/env python3
"""Prüft PR-Text als Daten, nicht als Shell-Code. Optionaler G1-Formalgate."""
from __future__ import annotations

import os
import re
import sys
from typing import List, Tuple


def check_pr_text(body: str) -> Tuple[List[str], str]:
    """Erfordert Traceability und überprüfbare Testangaben, kein KI-Sign-off."""
    problems: List[str] = []
    issue = re.search(
        r"(?i)\b(?:fixes|closes|resolves)\s+#\d+\b|"
        r"\b(?:issue|anforderung|befund)\s*[:#]\s*#?\d+\b|"
        r"\b(?:REQ-(?:HW|FW|DATA)-\d+|(?:SCH|HW|FW|SRV|CI|REG)26-\d+)\b",
        body,
    )
    if not issue:
        problems.append("Issue-/Anforderungs-/Befundreferenz fehlt (z. B. Fixes #123).")

    change_class = re.search(
        r"(?im)^\s*\*{0,2}(?:Änderungsklasse|Change Class)\*{0,2}:?\s*(D[0-3])\b",
        body,
    )
    kind = change_class.group(1) if change_class else "unbekannt"
    if not change_class:
        problems.append("Explizite Änderungsklasse fehlt (D0, D1, D2 oder D3).")

    if not re.search(r"(?i)\b(?:PASS|FAIL|SKIP|NICHT\s+(?:GELAUFEN|AUSGEFÜHRT)|NOT\s+RUN)\b", body):
        problems.append("Testergebnis fehlt (PASS/FAIL/SKIP/NICHT AUSGEFÜHRT).")

    if not re.search(r"(?im)^\s*(?:#{1,3}\s*)?(?:Nachweis|Tests?|Testnachweise)\b", body):
        problems.append("Abschnitt 'Tests' oder 'Nachweis' fehlt.")

    if kind == "D3":
        if not re.search(r"(?i)(?:G2|G3|G4|\bHiL\b|Laborversuch)", body):
            problems.append("D3: Labor-/HiL-/Gate-Status nicht dokumentiert.")
        if not re.search(r"(?i)(?:Safety|Sicherheit|Gefährdung|Risiko)", body):
            problems.append("D3: Sicherheitsrisiko bzw. Gefährdung fehlt.")

    return problems, kind


def main() -> int:
    issues, kind = check_pr_text(os.getenv("PR_BODY", ""))
    enforce = os.getenv("ENFORCE", "").strip().lower() == "true"
    n = os.getenv("PR_NUMBER", "?")
    if issues:
        print(f"PR #{n} ({kind}): {len(issues)} Nachweislücke(n).")
        for entry in issues:
            print(f"::warning::{entry}")
        summary = (
            f"### PR-Formalprüfung: {len(issues)} offene Angabe(n)\n"
            + "\n".join(f"- {x}" for x in issues)
            + "\n\n"
            + ("**Gate aktiv: FAIL.**\n" if enforce else "**Pilotphase: Hinweis, kein Merge-Block.**\n")
        )
    else:
        print(f"PR #{n} ({kind}): Angaben vorhanden (keine inhaltliche Abnahme).")
        summary = "### PR-Formalprüfung: Angaben vorhanden\nKein Nachweis für tatsächlich bestandene Tests oder sichere Hardware.\n"
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write(summary)
    return 1 if enforce and issues else 0


if __name__ == "__main__":
    sys.exit(main())
