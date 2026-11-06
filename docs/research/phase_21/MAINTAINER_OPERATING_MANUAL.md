# PHASE 21 DELIVERABLE 06 — MAINTAINER OPERATING MANUAL
## Daily Maintenance Workflows, Review Cadences, Triage SLA, and Long-Term Operations

**Document Identifier:** `docs/research/phase_21/MAINTAINER_OPERATING_MANUAL.md`<br>
**Phase:** 21 — Continuous R&D<br>
**Baseline Git Commit:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Date:** 2026-11-06<br>
**Auditor:** Operations Director & Senior Maintainer Lead<br>

---

## 1. Daily Maintainer Operating Responsibilities

Maintainers ensure the health, security, algorithmic rigor, and community responsiveness of the project.

### Core Operating Cadence:
- **Daily:** Triage incoming issues and pull requests; inspect automated CI failure alerts.
- **Weekly:** Maintainer triage sync to review open RFCs and research proposals.
- **Bi-Weekly:** Dependency vulnerability and supply-chain review (`pip-audit`, Dependabot).
- **Monthly:** Benchmark regression review comparing historical tracking metrics.
- **Quarterly:** Strategic research roadmap review with the Project Owner.

---

## 2. Defect Severity & Escalation Policy

Issues are classified into four severity tiers:

```
+---------------------------------------------------------------------------------------------------------+
|                                    DEFECT SEVERITY & ESCALATION MATRIX                                  |
+-------------------+-----------------------------------+-----------------------+-------------------------+
| Severity Level    | Definition                        | Target Remediation SLA| Action Protocol         |
+-------------------+-----------------------------------+-----------------------+-------------------------+
| P0 — Critical     | Security vulnerability (RCE/data  | Patch within 24 hours | Emergency patch release |
|                   | loss), crash in core streaming    |                       | Hotfix branch tagged    |
| P1 — High         | Algorithmic divergence (NaNs),    | Fix within 7 days     | Prioritized in next     |
|                   | memory leak, adapter failure      |                       | scheduled patch release |
| P2 — Medium       | Minor edge case, non-critical     | Fix within 30 days    | Standard PR queue       |
|                   | performance degradation           |                       |                         |
| P3 — Low          | Typo, documentation enhancement,  | Open community queue  | Tagged good-first-issue |
|                   | cosmetic code cleanup             |                       |                         |
+-------------------+-----------------------------------+-----------------------+-------------------------+
```

---

## 3. Dependency Management & Security Response

1. **Dependency Minimization:** Maintainers must reject pull requests introducing new third-party dependencies unless strictly justified by core functionality.
2. **Automated Weekly Audits:** The automated security workflow executes weekly:
   ```bash
   pip-audit --desc on
   bandit -r adaptive_ml/ -ll
   ```
3. **Deprecation Handling:** Dependencies reaching upstream End-of-Life (EOL) are transitioned within 60 days of vendor EOL announcement.
