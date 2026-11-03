# Horizon archive for Blokky

Public backup of https://github.com/horizon-rust/horizon (MIT).

- `horizon-upstream`: upstream source snapshots, excluding executable `.github/workflows`. Exact original history, CI files and nightly source tags are preserved in each release’s `horizon-history.bundle` (restore with `git clone horizon-history.bundle`).
- Releases: checksum-verified copies of all nightly assets, including source archives and original checksums/signature.
- `main/manifest.json`: Blokky update manifest pointing to immutable archived release URLs.
- Scheduled hourly, with manual dispatch. Old builds are never automatically deleted.

Upstream code and workflows are never executed by the archive job. Failed downloads or checksums leave the previous manifest intact. Rewritten or deleted upstream history never removes anything here: every earlier snapshot stays on `horizon-upstream` and every earlier release keeps its own history bundle. The archive preserves available source and builds, not Mojang services or third-party dependency registries. Public GitHub schedules may be delayed; a heartbeat commit every 40 idle days keeps them from being disabled after 60.

Original Horizon licensing and copyright notices are preserved on `horizon-upstream` and in the source archives. Archive automation in `main` is MIT licensed.
