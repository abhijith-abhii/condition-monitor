# Failure and improvement ledger

Date: 2026-11-11. Observed failures are distinguished from review findings and
intentionally injected faults. No fabricated development history is used.

| ID | Type | Evidence / trigger | Cause | Change | Verification / tradeoff |
|---|---|---|---|---|---|
| D01 | Observed build failure | environment-logger/evidence/initial-tests.txt | Expected persistent layout 288 bytes; actual 284 | Corrected layout guard to 284 before final builds | Host and ESP32 compile; every stored-byte corruption rejected |
| D02 | Observed test failure | pulse-recorder/evidence/initial-tests.txt; long idle regression | Old edge timestamp looked recent after 32-bit timer wrap | Saturating idle-age accumulation | 90,000 stopped reporting intervals pass; tools/replay_failure.py reproduces legacy failure |
| D03 | Review finding | ISR used 32-bit timestamp for debounce after arbitrarily long idle | Modulo age can alias after a full wrap | 64-bit ESP timer for physical ISR debounce | Target compiles; actual long-idle pulse test remains hardware work |
| D04 | Review finding | Embedded NUL in line could truncate parser-visible text | C-string parser could ignore trailing bytes | Drop lines containing nonprintable bytes, with bounded resynchronization | New regression checks reject the whole binary command |
| D05 | Review finding | Gateway SELECT before insert could race another writer | Conflict check was outside transaction | Insert and verify stored payload in one transaction | Conflict/dedup/restart tests pass; storage failure produces no ACK |
| D06 | Review finding | Monitor persisted state was not printed at restart | Startup visibility was incomplete | Print prior saved state and NVS-open result | ESP32 compile; physical restart remains pending |
| T01 | Tooling failure | Restricted environment could not download compiler | Network isolation | Approved workspace-scoped download | All six ESP32 targets compiled; no global tool install |
| T02 | Tooling failure | Architecture figure renderer rejected parallel angle connector | Invalid connection geometry | Used explicit serpentine layout and vertical connection | Figure regenerated and included in visual review |

Injected missing sensors, bad CRCs, full queues, malformed frames and storage
errors are expected negative test cases, not claims of defects found in real
hardware. Their results live in the test matrix and logs.
