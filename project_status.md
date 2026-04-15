# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: deploy and restart the latest slow-energy-staleness runtime fix on the live Home Assistant install, then capture the recovered command-center state and confirm the next operator-visible path once safe mode is no longer being held only by solar_energy staleness

# Current blocker or none
blocker: the live Home Assistant install is still on the pre-fix build, so slow solar_energy staleness can still hold runtime safe mode and keep the command-center path from reflecting the real post-action state until the latest repo fix is deployed and Home Assistant is restarted

# Exact user action needed or none
user_action: James, on the Home Assistant host at 192.168.86.200 over the documented SSH path on port 2222, please either approve a live deploy and Home Assistant restart of the latest Zero Net Export main-branch fix, or run these exact commands and send the full output: `cd /root/.openclaw/workspace/projects/zero-net-export && python3 scripts/deploy_exact_repo_build.py /config --expected-commit $(git rev-parse HEAD) --require-clean --require-upstream-sync` then `ha core restart` and after Home Assistant is back `curl -s -H "Authorization: Bearer $HOME_ASSISTANT_TOKEN" http://192.168.86.200:8123/api/states/sensor.zero_net_export_status` plus `curl -s -H "Authorization: Bearer $HOME_ASSISTANT_TOKEN" http://192.168.86.200:8123/api/states/sensor.zero_net_export_command_center_status`; this is needed to prove the live install no longer blocks on slow solar_energy totals and to record the correct next native operator path

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, and prefer the documented Home Assistant SSH path in TOOLS.md before treating live deploy or validation as blocked

# Last time this file materially changed
last_modified: 2026-04-15 13:47
