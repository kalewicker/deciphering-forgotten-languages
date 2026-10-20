# Experiment 61: offline attribution of the saved native search cards

## Question, exposure and budget

Can the E60 static links be attributed to individual publisher result cards with
complete accounting, without admitting article eligibility? Use exactly the
saved E60 response and its receipt/observation/layout; **zero research requests**.
E60 already exposed this page. Before this registration, markup was inspected:
ten article.listing-block elements share one container, one info block, title
link, image link and snippet each; none has registered date markers. One card's
percent-encoded URL fails the existing strict article-URL rule. This is a
layout-derived development parser, not an untouched parser test.

Freeze the original body, receipt, E60 artifacts and configuration, the prior
v58 exposure registry, the progress review, new protocol/code/fixtures and all
60 previous manifests/seals. Do not alter old outputs or rules. The completed
result must reproduce every one of E60's 115 anchor occurrences and original
DOM indices/text/hrefs/resolutions before adding classifications.

## Fixed page and card schema

Use BeautifulSoup html.parser. Require one body with search and search-results
classes, one main#main-content, one exact registered result container, one exact
query heading and title, and no base[href]. The container is:

`main#main-content > div#main-content.wrapper.category-container > div.row > div.col-md-8.col-sm-7`

The heading selector is `main#main-content > div.type-bar h2`; its sole text
must be Results for: ANITA. The sole HTML title must be You searched for ANITA
– Physics World. Only whitespace is collapsed. Repeated IDs on main and its
inner div are preserved as observed and constrained by element/path, not
silently deduplicated. Missing or conflicting page structure prevents all card
attribution; the original rows and anchors still remain in the denominator.

Inventory every article.listing-block anywhere in DOM order, including outside
the container and nested units. An attributed card requires the page checks,
direct parentage in the unique container, no ancestor/descendant listing card,
exactly one direct div.listing-block__info, exactly one title link at
`:scope > div.listing-block__info > h3.listing-block__title > a[href]`, exactly one
`:scope > a.listing-block__image[href]`, one nonempty direct info p snippet,
nonempty title text, and a matching title attribute when present. Resolve both
links against the saved request URL and require identical HTTPS publisher /a/
URLs, no credentials, nonstandard port, query or fragment. This broad structural
URL check allows encoded paths; the unchanged E55 article_key predicate is a
separate strict usability diagnostic and may reject an otherwise attributable
card. Neither diagnostic nominates a candidate or establishes source identity.

Record all original title/image link occurrences, snippets and their DOM indices.
Record every card time, [datetime], .date or .listing-block__date marker. Missing
markers are explicitly unavailable; present markers require later validation.
Do not infer publication dates from image paths, snippet wording or result rank.
Keep duplicate cards with their first prior URL occurrence; never replace a
malformed card or choose a favorable duplicate title/link. No topic/date/scaffold
eligibility decisions occur in E61.

## Complete anchor and exposure accounting

Each original a[href] receives exactly one role: outside_listing_cards,
ambiguous_nested_card_ownership, rejected_card_link, attributed_title_link,
attributed_image_duplicate, or supporting_card_link. Preserve empty anchor
text, encoded or malformed URLs, category/navigation links and duplicate URLs.
Record every containing listing-card index. Title and image copies remain two
anchor occurrences belonging to one attributed card, not two independent hits.

Attach prior registry tags and prior-capture flags without treating a missing
registry entry as unfamiliarity or source independence. Form the union of the
frozen v58 registry with all strict article URLs in the entire saved response,
including out-of-card links. Preserve original captured keys; viewing a search
link does not make it a captured article. Also retain every resolved listing
URL, including the strict-URL failure. All viewed material is development data.
This registry is explicitly incomplete lifetime exposure/source grouping.

## Adopted recommendation and stop

The next proposed challenge has **two fixed candidate slots**, the unchanged
**eleven-numeric-anchor cap**, and requires at least one window with numeric
multiset overlap capacity **at least six** to challenge the reference's score.
The E58 three-type rule and all old results remain fixed. These new conditions
are planning constraints for a later separate registration, not computations
or nominations in this audit. Freeze nomination/exposure/native rules, request
and conditional-alias budgets and comparison/control rules before that intake.
Do not make the absence of listing dates a reason to relax the native date gate.

After that one fixed batch, close this discovery route as feasibility-limited
if no capable comparator is obtained. A capable comparator proceeds through the
frozen comparison, retaining ties/failures; no extra batch or query tuning is
allowed by this recommendation. Broader work then depends on new independent
review or fresh source-group evidence. E61 stops after this offline audit.

## Validation

Adversarial fixtures cover navigation and duplicate/empty links, encoded URL
rejection, missing/conflicting/duplicate card fields, wrong query/page/container,
base href, nested/outside cards, explicit/missing dates and exposure unions.
A separate verifier replays page/card predicates, original indices and all
anchor/exposure rows without the production v61 attribution or summary functions.
Shared HTML parsing is disclosed. Check all 60 previous manifests/seals and
full local/isolated public suites, then seal outputs, checkpoint raw evidence
locally and commit/push appropriate public files. No semantic, source-identity,
independent-review or untouched-test admission follows from structural attribution.
