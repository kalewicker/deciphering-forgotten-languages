# E102 finds no lead under the fixed source catalog screen

The catalog screen accounted for all **86 documents** and returned **zero
qualifying leads** for E101 replication. The audit identified 82 catalog
components using shared external locators and citations. Three rows were directly
linked to known exposure, the same three development members used in the earlier
Yid work. The catalog and exposure links describe recorded connections and have
incomplete coverage.

| Screen condition | Rows failing |
|---|---:|
| Resolved article join and one locator | 0 |
| Minimum of 22 parsed pairs | 10 |
| No known exposure in the recorded component | 3 |
| Exactly one external source claim | 49 |
| Citation and usable HTTPS locator for that claim | 1 |
| Numeric page range plus wording or order cue for that claim | 35 |

Failures overlap. The citation, locator and Role checks apply when one external
claim is present. **28 rows otherwise qualified but lacked the required Role
combination.** Of the two single-claim rows that supplied the required
combination, one was exposed and the other fell below the 22-pair floor.

The page-range requirement was a deliberate way to select a source with an
already bounded route to passage verification. The result closes that catalog
route. It leaves open whether a cited work's passages could be localized
independently of its catalog Role field. A separate localization design could
fix a source work, an edition or section scope and an acquisition budget before
reading pairings. The 28 rows describe a potential pool for such a design.
Their eligibility for eventual replication remains unverified.

Selection used the frozen join and source catalog metadata and prior exposure
ledgers. All 86 dispositions and the connected-component links were retained.
The original archive's earlier machine processing precludes calling these rows
untouched. This audit recorded zero nominations, replications, new pairing
scores or network requests. Semantic benchmark capacity remains 0/4.
[Registered protocol](../experiments/yid_reservation_v102.md)

Deterministic replay reproduced all 86 dispositions and the zero-nomination
decision from the registered inputs. The full catalog ledger stays local.
With the local archive, replay using
`.venv/bin/python scripts/yid_reservation_v102.py verify`.
