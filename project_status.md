# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: deploy and reload the native-support stale-threshold alignment fix on the live Home Assistant install, then verify that the false solar_energy command-center blocker clears and re-check whether the first real control action is only waiting on device guards

# Current blocker or none
blocker: live Home Assistant now shows a command-center inconsistency, stale_source_count is 0 and health_status is healthy, but mapped_source_blocker_summary still flags solar_energy as needing attention because native_support.py still hard-codes a 120-second stale cutoff instead of using each source's stale_threshold_seconds

# Exact user action needed or none
user_action: James, on the Home Assistant host at 192.168.86.200 over the documented SSH path on port 2222, please either approve live deploy/reload of the latest Zero Net Export main-branch fix or run these exact commands and send the full output: `cd /config/custom_components/zero_net_export && git pull` then `ha core restart` and after Home Assistant is back `curl -s -H "Authorization: Bearer $HOME_ASSISTANT_TOKEN" http://192.168.86.200:8123/api/states/sensor.zero_net_export_command_center_status` and `curl -s -H "Authorization: Bearer $HOME_ASSISTANT_TOKEN" http://192.168.86.200:8123/api/states/sensor.zero_net_export_stale_source_count` so we can confirm the false solar_energy blocker is gone before judging live action execution

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, and prefer the documented Home Assistant SSH path in TOOLS.md before treating live deploy or validation as blocked

# Last time this file materially changed
last_modified: 2026-04-15 12:14
