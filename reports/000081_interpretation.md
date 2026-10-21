# E81: two HTTPS controls succeed, neither client reaches target HTTP

Both installed clients completed verified HTTPS HEAD exchanges with the control
site. Neither completed an HTTP exchange with the FL site's robots endpoint.
**No candidate replacement transport was established.** Switching from system
curl's LibreSSL stack to Python's newer OpenSSL stack did not resolve access
in this fixed comparison.

This is infrastructure evidence. It does not identify a server fault, filtering
policy, certificate problem or intermediary, and it does not establish that the
whole FL site is unavailable to every client. E80's label-page failure remains
unchanged; its route was not retried and no post body was retrieved.

## Fixed four-cell result

The [protocol](../experiments/transport_probe_v81.md) and
[configuration](../experiments/transport_probe_v81.json) were frozen before the
four attempts. Both clients ran under the same approved outer execution setting,
with no proxy configuration or certificate overrides, TLS verification enabled,
no retries or redirect following, and fixed operation/process deadlines.

| Destination | Client | Outcome |
|---|---|---|
| `https://example.com/` | System curl 8.7.1 | HTTP 200 |
| `https://example.com/` | Python urllib / OpenSSL 3.5.5 | HTTP 200 |
| FL host `/robots.txt` | System curl / LibreSSL 3.3.6 | curl35, TLS protocol-version alert; no HTTP response |
| FL host `/robots.txt` | Python urllib / OpenSSL 3.5.5 | SSL record-layer failure; no HTTP response |

All four attempts remain in the denominator. No attempt timed out. Both target
attempts are classified `transport_unresolved`, while both controls are
`http_response_observed`. A valid HTTP error would also have established a TLS/
HTTP exchange under the protocol, but neither target produced one.

The preserved target errors are:

```text
curl: (35) LibreSSL/3.3.6: error:1404B42E:SSL routines:ST_CONNECT:tlsv1 alert protocol version
<urlopen error [SSL: RECORD_LAYER_FAILURE] record layer failure (_ssl.c:1081)>
```

The Python worker returns process code0 after recording an exception as structured
metadata. That is successful error recording, not a successful network exchange;
its HTTP status is null and its transport classification remains unresolved.

## What the comparison resolves

The control results show that verified HTTPS worked for both clients on another
host in this execution setting. Thus a general inability to use HTTPS is not
supported by this panel. The target failure persists across the two tested
client stacks, weakening the proposed practical fix of simply using the installed
Python client. It does not isolate TLS library version as a cause: client
implementation, negotiation details, endpoint behavior, routing and intermediaries
are not separately controlled.

This was a header-only check of a different path from E80. Even a successful
robots response would not have proven label-page or article-body availability.
E81 used an explicitly approved outer execution setting; comparison against E80
does not isolate its sandbox environment. No unverified SSL context, certificate
change, TLS downgrade, package installation, browser fallback, archive lookup,
body read or additional destination was used.

Curl headers are saved as raw response-header bytes. Python stores parsed header
pairs, not original wire bytes. Intents, commands, versions, binary hashes,
timestamps, stdout/stderr and receipts remain local. The observed-label and
post-selection rules were not changed, and no new corpus material was admitted.

## Stop and next resource boundary

Stop this diagnostic with transport unresolved and an empty candidate-client
list. The four outcomes do not justify a continuing client, TLS-version or host
sweep. Before another research intake, obtain a different documented material
resource, such as native saved pages supplied by someone who can access them,
or develop a separately justified acquisition route with a fixed budget.
Do not silently retry E80 with another client and relabel it successful.

Any supplied material still needs provenance, recorded-exposure, duplicate/group,
masking and reservation checks before confirmation. A new file or URL is not
automatically a new independent work. E79's positive result remains exposed
and unconfirmed, with its rule fixed. E77's failure stays failed. No new source
identity, meaning, independent review or untouched unit is admitted; semantic
benchmark capacity remains 0/4. No additional request or model run is launched
by this report.

## Verification and publication

The separate verifier imports none of the E81 production functions. It checks
the complete four-cell roster/order, exact commands and deadlines, per-attempt
artifact hashes, telemetry/parsed-header classifications, manifest chronology,
environment restrictions and unchanged E80 seal. It verifies accounting rather
than independently observing the network or cryptographically attesting the
execution environment. Local binary versions and recorded code bind the claimed
verification/body-read configuration.

Six fixture tests cover HTTP errors versus connection errors, unfollowed redirects,
metadata limits/malformed output, verification/body-read requirements and curl
header consistency. **589 workspace tests and 550 isolated-public tests pass**,
with the same 39 archive-dependent exclusions. E80's sealed evidence remains
unchanged. Network/environment artifacts are checkpointed locally; code, protocol
and small reports are public.

Read-only reconstruction requires the local archive:

```sh
.venv/bin/python scripts/verify_transport_probe_v81.py
```

Preparation and execution are single-use; do not overwrite sealed paths.
