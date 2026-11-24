# 0002: Release through release-please and k3s-infrastructure promotion

## Status
Accepted

## Context
Production runs in a k3s cluster managed by Flux from
`dylanwhitetech/k3s-infrastructure`. Manual tags, version bumps, and mutable
`:latest` images made releases hard to trace and roll back.

## Decision
release-please owns versioning from Conventional Commit PR titles. Merging the
release PR tags `vX.Y.Z` and runs `release-chart.yml`, which publishes
SHA-tagged multi-arch images and an immutable OCI chart to
`oci://ghcr.io/dylanwhitetech/charts`, then opens a promotion PR in
`dylanwhitetech/k3s-infrastructure`. Flux deploys the merged promotion.
Intentional rollback is reverting that promotion PR. Nobody mutates the cluster
directly for releases.

## Consequences
- Every deployed version maps to a tag, a chart version, and a commit SHA.
- Rollback is a git revert in the infra repo.
- No manual tagging or version bumps during normal shipping; release-please
  owns `.release-please-manifest.json` and `deploy/chart/weatherapp/Chart.yaml`.
- Requires the repo setting that allows GitHub Actions to create PRs and the
  `K3S_INFRA_REPO_TOKEN` secret for automated promotion.

## References
- [docs/operations.md](../docs/operations.md)
- PR #27 (release-please and chart smoke test), PR #28 (docs refresh)
- [release-please](https://github.com/googleapis/release-please)
