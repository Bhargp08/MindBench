# Data Management Plan

**Status:** DRAFT for Bharg's approval.

## ID scheme
- Each participant gets a random 8-character code with no ambiguous characters (generated in MB-06). The code is not derived from a name, email or any personal detail.
- The key linking a code to a person, if one exists at all, is kept offline by Bharg, never in the repo, never in the dataset.
- The dataset holds no names, emails or IP addresses.

## Storage
- Raw data is collected through DataPipe and stored privately in Google Drive (decision D1).
- Downloads run locally from Bharg's machine, with credentials in environment variables. No secrets in code, notebooks, issues or commits.
- Local copies live in `data/`, which is gitignored. The repo and CI hold only **simulated** data.
- Sleep and sleepiness data are health-related and stay private.

## Retention
- Raw data is kept while the project runs and for the paper and release. After that Bharg decides whether to keep or delete it; [retention end date to be set by Bharg].
- On a participant's withdrawal request, their data is deleted from Drive and the local database, then confirmed back to them.
- Pilot data is flagged (`is_pilot`) and excluded from confirmatory analysis.

## De-identification
Before any release:
1. Participant codes are replaced with new, unrelated codes.
2. Free-text fields are removed.
3. Timestamps are reduced to the date or coarser (Bharg decides the final rule in MB-24).
4. Device and user-agent details are removed or coarsened.
5. A check script verifies this. Records of people without consent for release are dropped.

## Release rule
- Bharg's own data may be released in de-identified form on Zenodo (CC-BY-4.0), linked from the OSF registration.
- **Friends' trial-level data is not published** unless that person ticked the open-data box. Otherwise it is used for pilot and UX purposes only.
- Publishing is an external action that Bharg performs himself, after approval.
- Recruiting beyond adult friends needs proper institutional oversight first. This is outside the current scope.
