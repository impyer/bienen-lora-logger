# GitHub-Workflow: Anforderung → Claude → CI → Codex-Review → Freigabe

**Status:** vorgeschlagene Automatisierung als eigenständiger Pull Request, **kein automatischer Merge und kein Safety-Sign-off**. Gilt ergänzend zu [Regelwerk 1.0](README.md); die [Präzisierung 1.1](https://github.com/impyer/bienen-lora-logger/pull/1) wird separat behandelt.

## Ablauf

| Schritt | Verantwortlich | Auslöser / Ergebnis |
|---|---|---|
| 1. Anforderungen | Maintainer | GitHub-Issue aus Vorlage **Feature** oder **Bug**. Betroffene D-Klasse, Abnahmekriterien und Testfälle stehen im Issue. |
| 2. Umsetzung | Claude Code | Lokaler/IDE-Workflow: neuer Branch `feature/<issue>-...` oder `fix/<issue>-...`, Änderung **in den führenden Quellen**, Unit-/SiL-Test, Commit/Push. Alternativ bei aktiviertem Claude-Action-Workflow ein **vertrauenswürdiger** `@claude`-Kommentar im Issue. |
| 3. Pull Request | Claude Code oder Maintainer | PR mit `Fixes #N`, D0–D3, getesteten Kommandos, tatsächlichen Ergebnissen und offenen HiL-Punkten. Claude Code Action liefert je nach Einrichtung nur einen **Link zum PR-Erstellen**, nicht zwingend automatisch den PR. |
| 4a. Technische CI | GitHub Actions | Bereits vorhandene `.github/workflows/tests.yml` prüft Firmware, Formatter, Server, Simulationsmodelle, KiCad-Generator/ERC und die Netztest-Kette, sofern in `pruefen.sh` **wirklich** integriert. Fehlgeschlagene Jobs bleiben rot. |
| 4b. Unabhängiges Review | Codex GitHub Action | Optionaler `codex-pr-review.yml`, startet für vertrauenswürdige PRs nach `opened/synchronize`; veröffentlicht **einen aktualisierbaren Kommentar** mit Risiken und Vorschlägen für neue Unit-/Regressionstests. Er **schreibt keine Dateien** in den PR. |
| 5. Korrekturschleife | Claude | Aus Review Befund-IDs und Tests übernehmen, fixen, pushen; neue Commits lösen CI und Codex erneut aus. Bei aktivierter Claude Action kann der Maintainer als Kommentar `@claude Bitte prüfe und behebe die Befunde aus dem Codex-Review. Neue Tests ergänzen.` schreiben. |
| 6. Merge / Labor / Release | Maintainer | G1 nur nach relevanter grüner CI, dokumentiertem Review und Entscheidung. G2 = sichere Laborzulassung, G3/G4 D3 nur nach passenden realen HiL-Nachweisen plus fachkundiger unabhängiger Sicherheitsprüfung. **Kein automatisches Merge.** |

**Wer prüft wirklich?** Das GitHub Action-Modell ist ein **separater OpenAI/Codex-Agent**, nicht dieselbe laufende ChatGPT-Unterhaltung und nicht automatisch die GitHub-Integration dieses Chats. Reviews werden als konkrete PR-Kommentare/Aktionschecks sichtbar.

## Aktivierung: Einstellungen durch Repo-Administrator

**Phase A – kostenfrei ohne KI-API-Schlüssel (nach Merge verfügbar)**

1. Die neuen **GitHub-Issue-Vorlagen** nutzen; beim PR `Fixes #N` und Tests eintragen.
2. `PR-Vertrag – Anforderung und Nachweis` läuft auf jedem PR, zunächst **nur mit Warnungen**. Nach Prüfung der Beispiele: Repository **Settings → Secrets and variables → Actions → Variables**, `ENFORCE_PR_CONTRACT=true` setzen.
3. In **Settings → Rules → Rulesets** (oder Branch protection) für `main` PRs verpflichtend machen, direkte Pushes verhindern, relevante CI-Checks unter „Require status checks“ aufnehmen (insbesondere KiCad-10, Server, Formatter, Host/FFT, STM32-Build, PR-Formular). **Nicht** ein „skipped“ KI-Review als bestanden werten. Vor Freigabe prüfen, welche Regeln der GitHub-Plan tatsächlich erzwingen kann.
4. Reviews brauchen **aktuelle** Befundstände. Die bestehende [KiCad-Regression](https://github.com/impyer/bienen-lora-logger/issues/2) ist zu beheben, nicht durch weniger strenge Checks zu umschiffen.

**Phase B – Claude Code aus GitHub heraus optional starten**

1. Offizielle [Claude-GitHub-App und Setup](https://github.com/anthropics/claude-code-action/blob/main/docs/setup.md) prüfen/installieren.
2. In **Settings → Secrets and variables → Actions → Secrets**: `ANTHROPIC_API_KEY` als Secret hinterlegen. **Niemals ins Issue, Code, Chat-Log oder Repo schreiben.**
3. In **Variables**: `ENABLE_CLAUDE_ACTION=true` setzen.
4. Ein Maintainer kommentiert ein Issue oder einen PR mit `@claude Bitte Aufgabe aus diesem Issue umsetzen, passenden Test ergänzen, separaten Branch verwenden und den PR verlinken.`
5. Nur Kommentare von Repository-Ownern/Mitgliedern/Kollaborierenden dürfen die Action auslösen. API-Kosten und GitHub-Actions-Minuten fallen separat an. Bei der Korrektur kontrollieren, ob die Claude-Action lediglich einen vorausgefüllten PR-Link anbietet. Wenn ja: PR von Claude Code/CLI oder Maintainer eröffnen.

**Phase C – Codex-Review auf PR-Änderungen optional aktivieren**

1. Einen **eigenen OpenAI-API-Schlüssel** mit Budgetgrenze verwenden. Eine ChatGPT-Subscription allein aktiviert die API-Abrechnung **nicht**. Schlüssel als `OPENAI_API_KEY` in GitHub Actions **Secrets** hinterlegen.
2. Variable `ENABLE_CODEX_REVIEW=true` setzen. Der Workflow nutzt [`openai/codex-action@v1`](https://github.com/openai/codex-action) mit `permission-profile: ":read-only"` und `drop-sudo`. Er darf selbst **keine Commits** machen.
3. Trigger sind `opened`, `reopened`, `synchronize`, `ready_for_review`. Er läuft **nur für Branches im selben Repository**, keine Fork-PRs, keine Draft-PRs; vertrauenswürdige Maintainer/Kollaborierende und der ausdrücklich angegebene Claude-Bot.
4. Review und PR-Kommentar sind **zwei getrennte Jobs**. Der Job mit dem OpenAI-API-Schlüssel hat nur Lesezugriff; der Kommentarjob verfügt über **keinen API-Schlüssel**, überprüft die aktuelle Head-SHA und aktualisiert statt zu spammen denselben Bot-Kommentar.
5. Der Codex-Kommentar enthält P0/P1/P2, reproduzierbare Testvorschläge und offene HiL-Aufgaben. **Er ist keine Freigabe.** Wenn das Review deaktiviert/übersprungen ist, wird dies nicht als „KI geprüft“ ausgegeben.

Die Action ist keine risikofreie Verarbeitung untrusted PR-Textes. Dokumente, Commit-Nachrichten und PR-Änderungen können Prompt-Injection enthalten. Deshalb nur vertrauenswürdige interne Branches mit dem API-Key, strikt minimale Rechte und getrennte Jobs. Keine PR-Codeskripte im Schlüssel-Job ausführen. Externe Fork-PRs weiterhin über **CI ohne Secrets** und manuelles Reviewergebnis prüfen. Einzelne gezielte ChatGPT-Reviews lassen sich außerdem über den GitHub-Connector in diesem Chat anstoßen.

## Standard-Prompts und Beispiel

**Issue:** „Der FFT-Encoder soll bei abweichender Kanalzahl keinen Phantomwert liefern. `REQ-FW-... `, D2. Abnahme: Host-Test mit 0, 2 und 3 Kanälen; Legacy-FPort1 darf sich nicht ändern.“

**Claude:** „Implementiere `Fixes #N` auf neuem Branch. Ergänze zunächst einen fehlschlagenden Regressionstest, dann den Fix. Führe die relevanten Tests aus; erfinde keine HiL-Werte.“

**Codex:** Übernimmt durch den PR automatisch Review + Testvorschläge; Claude setzt die konkret benannten Korrekturen um und pusht erneut. Die vorhandene CI belegt den technischen Nachtest.

## Grenzen und offene Betriebsentscheidungen

- **Ein einzelner KI-Reviewer ist nicht unabhängig qualifiziert für einen Lithium-Akku-Sicherheitssign-off.**
- Die **Codex-Action schlägt Unit-Tests mit Codebeispielen vor**; sie committet sie **nicht automatisch**. Das bleibt eine bewusst getrennte, überprüfbare Aufgabe für Claude. Wer automatische Test-PRs möchte, muss einen separaten, eingeschränkten Schreib-Workflow mit expliziter Freigabe bauen.
- Eine fehlende KI-Konfiguration wird **nicht** durch erfundene grüne KI-Checks kompensiert.
- Sicherheitsrelevante GitHub-Einstellungen, externe App-Installationen und API-Schlüssel erfordern **bewusste Admin-Aktion**; ein Dokumentations-PR kann sie nicht selbst aktivieren.
- Für Änderungen an `.github/workflows/` selbst ein eigenes Maintainer-Review einplanen, weil Workflowdateien mit Secrets und Repository-Rechten besonders sensibel sind.

## Quellen

- [Anthropic Claude Code Action](https://github.com/anthropics/claude-code-action) und [FAQ](https://github.com/anthropics/claude-code-action/blob/main/docs/faq.md)
- [OpenAI Codex GitHub Action](https://github.com/openai/codex-action) / [Sicherheitsleitfaden](https://github.com/openai/codex-action/blob/main/docs/security.md)
- [GitHub – pull_request_target-Sicherheit](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)
- [GitHub – Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository)
