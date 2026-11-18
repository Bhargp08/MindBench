# Data Management Plan

Status: approved (Bharg, Nov 17, 2026). Current scope: Bharg is the only participant.

## ID scheme
Random 8-character participant code (no ambiguous characters), generated in MB-06. No names, emails or IP addresses in the dataset. Any code-to-person key stays offline, never in the repo.

## Storage
Raw data goes through DataPipe to private Google Drive (D1). Downloads run locally with credentials in environment variables. Local copies live in gitignored `data/`. The repo and CI hold simulated data only. Sleep and sleepiness data are health-related and stay private.

## Retention
Raw data is kept until Dec 31, 2028 or 2 years after the write-up is published, whichever is later, then deleted. De-identified open data on Zenodo is kept indefinitely. Pilot sessions are flagged `is_pilot` and excluded from confirmatory analysis.

## De-identification
Before any release: replace codes with new unrelated ones, drop free-text fields, reduce timestamps to the date or coarser (final rule in MB-24), and coarsen device and browser details. A check script verifies this.

## Release rule
Bharg's own de-identified data may be released on Zenodo (CC-BY-4.0), linked from the OSF registration. Releasing is an external action Bharg does himself after approval. If other participants join later, their trial-level data is not published without their explicit consent (see the deferred consent form).
