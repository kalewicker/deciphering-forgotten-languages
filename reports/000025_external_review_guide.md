# External review handoff

Two self-contained archives are ready to give to an external reviewer. Preparing these archives sent no message and uploaded no material.

| Packet | Download | Fixed publisher window |
|---|---|---|
| Western esoterism | [Western review packet](../data/v25/packets/western_esoterism.zip) | PDF pages 90–94 |
| Risk mathematics | [Risk review packet](../data/v25/packets/risk_math.zip) | PDF pages 1–3 |

1. Give either archive, or both, to a reviewer who has not seen our prior predictions. Ask the reviewer to describe all prior exposure honestly. The candidate source identities are disclosed, so this is source/passage review with a proposed source, rather than blinded source retrieval.
2. The reviewer extracts the archive and reads `INSTRUCTIONS.md`. Each archive includes the dated FL post, unchanged publisher PDF, fixed page images, publisher window text, a material manifest with hashes/offset conventions, and a blank return template.
3. The reviewer copies `review_return_template.json` to a new JSON file and fills it. Supported, rejected and uncertain findings are welcome. Unknown-language passages should remain unknown unless independent evidence supports a relationship; copied names and structural resemblance do not establish meanings. The reviewer restricts evidence to the fixed publisher window and records any coverage limitations.
4. Bring back the completed JSON file. Preserve the original returned bytes and reviewer declaration in a new intake record. The original archives/templates and the zero-return handoff remain unchanged.

The reviewer must supply identity, role/identifier, independence and exposure declarations, completion time, scoped language observations, boundary/coverage assessments and explicit uncertainty. Support/rejection needs cited paired evidence; an uncertain review may have no pairs. Exact quoted spans use half-open Python Unicode code-point offsets in the supplied UTF-8 text. These conventions include whitespace, extraction artifacts and the final newline. The source images govern layout.

The project can check a returned file with:

```sh
.venv/bin/python scripts/validate_review_return_v25.py western_esoterism /absolute/path/to/returned_review.json
.venv/bin/python scripts/validate_review_return_v25.py risk_math /absolute/path/to/returned_review.json
```

Use the command for the corresponding nominee. The validator prints problems without modifying the packet or the returned file. Exit status 2 means an invalid/incomplete return; exit status 0 means structurally ready for adjudication. It checks packet/text hashes, declarations and exact span quotes; self-declared independence still needs assessment. A successful structural check admits zero source identities, semantic labels or untouched-test units. Independently recheck the return and adjudicate evidence before any scientific acceptance. A subsequent intake must retain negative and uncertain results as well as support.

The [engineering report](000025_interpretation.md) records what was prepared and verified. No review has yet been returned, and no semantic evaluation has run.
