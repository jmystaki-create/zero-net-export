# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: preview then deploy the current local intended repo build from commit `0c6b544` to the live Home Assistant install path, preferably with `python3 scripts/deploy_exact_repo_build.py /path/to/home-assistant/config --dry-run` first and then `python3 scripts/deploy_exact_repo_build.py /path/to/home-assistant/config`, confirm the post-copy fingerprint match with `python3 scripts/validate_install_fingerprint.py /path/to/home-assistant/config/custom_components`, then restart Home Assistant core and validate only from that one synchronized source

# Current blocker or none
blocker: the live Home Assistant install is still serving a mixed build, with `manifest.json` version `0.1.79` and tracked files that do not consistently match the current local intended repo build at commit `0c6b544` (`manifest.json` version `0.1.80` plus the exact deploy helper, updated live repair guidance with the exact deploy and dry-run preview commands, clearer managed-device promotion copy, the guard that refuses to target the repo source directory during manual deploy, the new dry-run preview for checking the resolved deploy target before copying, the fingerprint-compare guard that now refuses repo-local paths so repo copies cannot be mistaken for live validation, and refreshed helper-script coverage that validates a real copied install tree instead of the repo source path); until Home Assistant is pointed at one explicit install path, compared against the repo fingerprint, and restarted from that synchronized package, live validation remains untrustworthy

# Exact user action needed or none
user_action: approve or perform deployment of the current local Zero Net Export commit `0c6b544` to the Home Assistant `custom_components/zero_net_export` install path, preferably by running `python3 scripts/deploy_exact_repo_build.py /path/to/home-assistant/config --dry-run` first to confirm the resolved target, then `python3 scripts/deploy_exact_repo_build.py /path/to/home-assistant/config`, then `python3 scripts/validate_install_fingerprint.py /path/to/home-assistant/config/custom_components` from this repo to confirm an exact match before restarting Home Assistant core from that synchronized install so live validation can be trusted

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, and keep version tracking explicit across local repo state, remote GitHub state, and public release state

# Last time this file materially changed
last_modified: 2026-04-13 16:19
