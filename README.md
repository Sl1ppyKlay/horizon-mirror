# Horizon archive for Blokky

Public backup of https://github.com/horizon-rust/horizon (MIT).

- `horizon-upstream`: upstream source snapshots, excluding executable `.github/workflows`. Exact original history, CI files and nightly source tags are preserved in each release’s `horizon-history.bundle` (restore with `git clone horizon-history.bundle`).
- Releases: checksum-verified copies of all nightly assets, including source archives and original checksums/signature.
- `main/manifest.json`: Blokky update manifest pointing to immutable archived release URLs.
- Scheduled hourly, with manual dispatch. Old builds are never automatically deleted.

Upstream code and workflows are never executed by the archive job. Failed downloads or checksums leave the previous manifest intact. Rewritten upstream history stops synchronization for review instead of force-deleting history. The archive preserves available source and builds, not Mojang services or third-party dependency registries. Public GitHub schedules may be delayed and are disabled after 60 days of repository inactivity; monitor Actions and re-enable if necessary.

Original Horizon licensing and copyright notices are preserved on `horizon-upstream` and in the source archives. Archive automation in `main` is MIT licensed.
