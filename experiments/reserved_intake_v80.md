# E80: bounded raw-material intake after E79

E79 passes an adaptively designed development gate. The next resource question
is whether one observed native label route can supply four previously unrecorded
raw posts for a later confirmation-eligibility decision. This is intake, not
confirmation, language identification, group admission or scoring.

Before any network request freeze this protocol/code, E79 seal, the saved Western
HTML containing `a[rel~=tag]` text Kamri with the exact label URL, and an exposure
registry. The observed route is:
https://forgottenlanguages-full.forgottenlanguages.org/search/label/Kamri
No guessed feed endpoint, search engine, alternate host, archive, pagination,
query variation or return to E62/E70's closed discovery routes.

## Frozen exposure screen

Collect same-host article-shaped URLs from all public tracked UTF-8 .md/.json/.py
files, plus data/v15/parsed_annotations.json, data/v37/known_exposure.json,
data/v37/nominations.json and data/v63_registration/known_exposure.json. Store
input hashes, a local snapshot of every screened file, the public commit ID and
the sorted union before acquisition. Use the frozen snapshots for later replay,
so evolving README text cannot alter the recorded exposure screen. Match /YYYY/MM/slug.html
on this host, ignoring query/fragment and treating HTTP/HTTPS as the same exposure
key. This incomplete registry screens recorded exposure; absence does NOT prove
never-seen material, source-group independence or untouched status. No opaque
texts or vocabulary overlaps are analyzed to select candidates.

## One label page, four unreplaced post slots

At most five requests total: one exact label page, then one per selected post.
Each GET uses curl with user config disabled, HTTPS only, zero retries, no redirect
following, 8 s connect / 20 s total deadline, 4 MiB response limit and fixed E80
user-agent. Save intent before each request; reserve it permanently even on failure.
Save raw response bytes, headers, complete curl telemetry/stderr and hashes locally.
No cookies, credentials, browser, JavaScript, assets or unrelated requests.
Infrastructure approval is not a research retry; never rerun a recorded attempt.

A response passes transport only with exit0, HTTP200, exact final URL, zero
redirects, one application response (excluding proxy CONNECT/1xx), no Location,
consistent text/html media types, nonempty size <=4 MiB and no casefolded static
text occurrence of: 'verify you are human', 'access denied', 'captcha',
'just a moment', 'enable javascript and cookies'. Failure stops that route.

From a passing label page use only `.post-title a[href]` elements in DOM order.
Retain all such elements and reasons. An eligible nomination has nonempty title,
an absolute HTTPS same-host /YYYY/MM/slug.html URL, no credentials/port/query/
fragment, no duplicate key and no key in the frozen exposure registry. Reject
any base[href] document without resolution or repair. Pick the first four eligible
unique links; later eligible links are over-cap. Freeze the complete selection
before post requests. Missing or failed slots stay in the four-slot denominator.
Do not choose by title topic, source familiarity, token count or expected scores.
A failed label response produces four empty slots and no post requests.

For each captured selected post, require the transport gate and exactly one
nonempty .post-body, exactly one .post-title whose NFC/casefold/whitespace-normalized
text equals the nomination, and a rel=tag Kamri link to the exact label route.
Require either at least one exact canonical URL, or exactly one exact post-title
link plus exactly one exact bookmark permalink. Every canonical and og:url field
that is present must equal the selected URL; conflicts reject the post. No
metadata repair, query stripping, body widening or fallback to partial excerpts.

Do not export/display prose, tokenize it, inspect model vocabulary overlap,
extract references or run predictions. Store raw bytes as unscored quarantine.
HTML parser inspection for fixed metadata/body presence is disclosed; quarantine
is procedural, not a technical access-control guarantee or proof of no exposure.
Titles/URLs/labels are exposed metadata. Live capture time does not authenticate
wording at the publication date in a URL.

## Result and stop

Record four slots and all failures. Raw-intake capacity is true only if all four
slots pass the fixed capture gates. It is distinct from confirmation eligibility,
which remains unresolved even if all four pass: source connections, duplication,
representation/masking and reserved evaluation rules still need a separate frozen
protocol without model scoring. No new independent works or untouched units are
admitted in E80. Do not confuse this four-slot resource budget with the separate
four-work independently reviewed semantic benchmark, which remains 0/4.

Verify request budgets/telemetry/hashes, exposure provenance, exact selection order
and all per-post checks independently from saved bytes. Fixture tests cover strict
URLs, exposure/duplicate handling, four-slot cap, base tags, conflicts, label and
body ambiguity. Run once, preserve E79 and all prior gates, then stop. No second
batch or endpoint repair after a failure; any future resource route requires a
materially different justification. Publish code/protocol/small reports; raw HTML,
headers and quarantine stay on the local-only evidence branch.
