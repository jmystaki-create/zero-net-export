# Tools and live-evidence access paths

This file documents the preferred ways to gather live validation evidence for **Zero Net Export** before asking the user for manual screenshots, logs, or restatement.

Use these paths in order when they are available.

## 1. Home Assistant UI via browser access

Preferred for:
- HACS version visibility
- Integration card state
- Configure flow behavior
- Devices, entities, Repairs, and notifications
- Restart-confirmation checks that are visible in the UI

Use browser access to inspect the real installed surfaces directly when the session has authenticated access.

## 2. Home Assistant APIs

Preferred for:
- config entry state
- entity state and attributes
- device/entity presence
- service-call outcomes
- diagnostics that are exposed through HA APIs or websocket endpoints

Use API access when it gives a clearer or more reproducible answer than screenshots.

## 3. Home Assistant logs

Preferred for:
- setup failures
- retries
- tracebacks
- warnings after restart or reload
- confirming whether a fix cleared the intended project-specific error

Review project-specific log lines after install, upgrade, reload, or restart.

## 4. Host or container inspection

Preferred for:
- confirming the installed package path
- verifying copied files under `custom_components/zero_net_export`
- checking manifest/version/fingerprint state in the live install
- restart or service status when exposed at the host level

Use local filesystem or shell inspection when package contents or runtime environment need confirmation.

## 5. Repo helper scripts

Preferred for exact-build validation during manual install or live repair work.

Primary commands:

```bash
python3 scripts/deploy_exact_repo_build.py /path/to/home-assistant/config --dry-run --expected-commit <intended_commit> --require-clean --require-upstream-sync
python3 scripts/deploy_exact_repo_build.py /path/to/home-assistant/config --expected-commit <intended_commit> --require-clean --require-upstream-sync
python3 scripts/validate_install_fingerprint.py /path/to/home-assistant/config/custom_components
```

After the exact deploy copy succeeds, use the helper's printed post-restart checklist and go back to Configure -> Sensors and source mapping before trusting live control.

Use discovery first when the install root is unknown. The helper checks common Home Assistant env vars plus typical container, Home Assistant OS / Supervised, and bare-metal config paths:

```bash
python3 scripts/deploy_exact_repo_build.py --discover-home-assistant-config
```

If that still reports no candidates, rerun the same discovery command from the actual Home Assistant host or container. The helper also does a bounded recursive search from common roots there, which can catch non-standard mounted config paths that are not visible from this workspace shell.

## Escalate to the user only when needed

Treat live validation as a user blocker only when the required evidence cannot be gathered through the documented access paths above, or when the next step requires human-only interaction or approval.
