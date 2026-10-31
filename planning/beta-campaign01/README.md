# AERIS Beta Campaign 01

Start with [MASTERPLAN.md](MASTERPLAN.md), or open
[the readable plan](../../delivery/PLAN-BETA-CAMPAIGN01.html).

- `campaign.json`: proposed milestones,28 MUST,13 metrics,48 feature groups,
  48 scenario designs,22 work packages, dependencies, risks and source provenance.
- `TIP-M0.md`: first executable work-package specification, with analysis budget;
  this plan itself launches no runtime.
- `PLAN-VALIDATION.json`: structural/cross-reference validation only, not product
  acceptance or permission for hardware flight.

Every new campaign gate starts NOT_STARTED/NOT_CHECKED. Historic successes retain
their own source/configuration and do not automatically qualify the beta. Hardware,
real media, Hera calibration and production release have separate gates.

Generation scripts use exclusive outputs. Preserve an earlier draft in the task
evidence root before deliberately generating a new draft. Do not invoke all Python
scripts as a generic test suite: these scripts generate planning artifacts, not
application source or simulator workloads.
