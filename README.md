# Building & Publishing Docker Images in CI
 
Exercise project for building and publishing Docker images with GitHub Actions. The repository reuses the app, `requirements.txt`, and `Dockerfile` from `docker_fundamentals/1-first_image/` in the `holbertonschool-devops-formation` repository (the earlier Docker Fundamentals project).
 
## Image Build
 
The workflow is defined in `.github/workflows/image.yml`.
 
**Trigger**: the workflow runs automatically on every `push` to the repository — as soon as a commit is pushed, GitHub Actions starts the job.
 
**Jobs**: the workflow contains a single job, `build`, running on an `ubuntu-latest` machine.
 
**Steps of the `build` job**:
1. **Checkout** (`actions/checkout@v4`) — fetches the repository's code onto the runner, making the `Dockerfile` and the app available for the next steps.
2. **Login to GHCR** (`if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/')`) — authenticates to `ghcr.io` using `secrets.GITHUB_TOKEN` piped into `docker login` on stdin.
3. **Generate Tags** (`docker/metadata-action@v5`) — computes the list of tags to apply to the image from the Git context (branch, commit, Git tag) instead of any of them being written by hand (see "Automatic Tagging Strategy" below).
4. **Set up Buildx** (`docker/setup-buildx-action@v3`) — switches the runner to the Buildx builder, which is required for `build-push-action` to export its cache to `type=gha` (see "Build Caching" below).
5. **Build Image** (`docker/build-push-action@v6`, `push: false`, `load: true`) — builds the image from the `Dockerfile` at the repository root, restoring cached layers when available, and loads it into the runner's local Docker daemon without publishing it anywhere yet.
6. **Scan Image** (`aquasecurity/trivy-action@v0.24.0`) — scans the freshly built image for known vulnerabilities and fails the step (see "Vulnerability Scanning" below) if a `CRITICAL` one is found.
7. **Push Image** (`if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/')`, `docker/build-push-action@v6`, `push: true`) — only reached if the scan passed; rebuilds (instantly, from cache) and pushes the image under every tag from `generate tags`, but only on `main` or a Git tag.
The build and the scan always run, on every push, on every branch — only the final push to the registry is gated, both by the scan having passed and by the branch/tag condition. If the build or the scan fails, the job fails, the error is visible in the logs, and `push image` never runs.
 
## Successful run (Task 0)
 
Example of a run where the image built successfully: [run #33065547354](https://github.com/N-Haitu31/holbertonschool-continuous_integrations/actions/runs/33065547354)
 
This link shows the `build` job passing: the checkout completed, and `docker build` produced the `mon-app` image from the reused `Dockerfile` without any error — proving the image builds cleanly on a machine that isn't the developer's own.
 
## Publish to Registry (Task 1)
 
### Authentication
 
The `login to ghcr` step never hardcodes a credential: it pipes `secrets.GITHUB_TOKEN` — generated automatically by GitHub for the run, scoped to this repository — into `docker login ghcr.io` on stdin. The workflow only needs `permissions: packages: write` to be allowed to push; no personal access token or manually created secret is involved.
 
### Tagging: SHA vs `latest` (Task 1 approach, later replaced)
 
Originally, the workflow tagged the image by hand with two `docker tag` commands, giving the same image two tags:
- **The full commit SHA** (`${{ github.sha }}`) — immutable. It says exactly which commit produced this image, which is what you need to audit what's running or roll back to a known-good build.
- **`latest`** — a mutable, convenient pointer to whatever was most recently published from `main`. On its own it can't tell you which commit it corresponds to, which is why it was always published alongside the SHA tag, never instead of it.
This manual step no longer exists in `image.yml` — it was replaced in Task 2 by `docker/metadata-action` generating tags automatically (a short SHA, the branch name, and a version tag on Git tags), which also adds `latest` by default. See "Automatic Tagging Strategy" below for the current mechanism.
 
### Gating
 
The `login to ghcr` step, and the `push image` step, only run when `github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/')` — a push to `main`, or a push of a Git tag. The build and the scan still run on every push, on every branch, so a broken build or a critical vulnerability is caught everywhere — but only `main` or a tag ever reaches the registry. A feature branch or a pull request can fail or succeed its build without ever publishing an image.
 
### Published image
 
The image is published on GHCR: [ghcr.io/n-haitu31/holbertonschool-continuous_integrations](https://github.com/N-Haitu31/holbertonschool-continuous_integrations/pkgs/container/holbertonschool-continuous_integrations). This link stays valid regardless of which tags are currently on the image — see "Automatic Tagging Strategy" below for what those are today.
 
Example of the first successful publish (Task 1), back when tags were still written by hand: [run #33156486925](https://github.com/N-Haitu31/holbertonschool-continuous_integrations/actions/runs/33156486925)
 
## Automatic Tagging Strategy (Task 2)
 
### What's generated automatically
 
The `generate tags` step configures three rules, each producing a different kind of tag from the Git context:
- **`type=ref,event=branch`** — a tag matching the branch name (e.g. `main`).
- **`type=sha,format=short`** — a tag matching the short commit SHA (e.g. `a1b2c3d`).
- **`type=semver,pattern={{version}}`** — only when the push is a Git tag that looks like a version (e.g. `v1.0.0`), a tag matching that version (`1.0.0`).
### Why this beats hardcoding tags
 
With the manual `docker tag` commands from Task 1, every tag had to be known and typed by hand — the exact commit SHA, the exact version string. That's exactly the kind of thing that's easy to get wrong under no real pressure and even easier to get wrong the moment it matters: forget to bump `v1.0.0` to `v1.0.1`, copy the wrong SHA, and the tag on the image no longer matches the commit that actually produced it — silently defeating the entire point of having an immutable tag to audit or roll back to. Generating tags from the Git context removes that class of mistake: the tag is always derived from what actually happened, not from what someone remembered to type.
 
### The automatic `latest`
 
None of the three rules above mention `latest` — yet it still appears on the image. `docker/metadata-action` adds a `latest` tag by default whenever the build is the highest-priority match for the repository (in practice, a push to the default branch), without it needing to be listed in `tags:` at all. It's a default behavior of the action, not something this workflow configured explicitly.
 
### Proof
 
Example of a run triggered by `git push origin v1.0.0`: [run #33159243045](https://github.com/N-Haitu31/holbertonschool-continuous_integrations/actions/runs/33159243045)
 
This run shows the `1.0.0` tag appear on the published image — generated entirely from the Git tag by `type=semver,pattern={{version}}`, without that version string ever being written anywhere in `image.yml`.
 
## Build Caching (Task 3)
 
Building the image from scratch on every push means redownloading the base image and reinstalling dependencies every single time, even when nothing changed. `build image` uses `cache-from: type=gha` and `cache-to: type=gha,mode=max`, backed by GitHub Actions' own cache, so unchanged layers are restored instead of rebuilt — `mode=max` specifically saves every intermediate layer, not just the final one, so more of the build can be skipped next time. This only works because of the preceding `set up buildx` step: the default Docker driver can't export to `type=gha`, only the Buildx builder can.
 
To measure the gain, the same `build` job was timed on two runs:
 
- **Without a warm cache** (the first run after `cache-from`/`cache-to` were added — a cache miss, since nothing had been saved yet): [run #8](https://github.com/N-Haitu31/holbertonschool-continuous_integrations/actions/runs/33160657284) — job total **39s**.
- **With a cache hit** (a later push that touched only `README.md`, leaving `Dockerfile`/`requirements.txt`/`app.py` untouched): [run #9](https://github.com/N-Haitu31/holbertonschool-continuous_integrations/actions/runs/33161220157) — job total **26s**.
That's roughly a **33% reduction** (13s saved) on the whole `build` job once the layer cache is warm.
 
## Vulnerability Scanning (Task 4)
 
### Severity policy
 
`scan image` runs Trivy with `exit-code: '1'` and `severity: CRITICAL` — only a **`CRITICAL`** finding fails the step. `HIGH`, `MEDIUM`, and `LOW` findings are still reported in the logs but never block a publish. `CRITICAL` is the threshold GitHub, Trivy, and most registries reserve for vulnerabilities that are both easy to exploit and severe in impact (remote code execution, full compromise) — the bar deliberately doesn't sit any lower, so the gate blocks what's genuinely dangerous to ship without also blocking on findings that don't justify stopping every deploy.
 
### `ignore-unfixed: true`
 
The scan also sets `ignore-unfixed: true`, and this is the part of the policy that matters most to document. The first time the scan ran for real (pinned to a real `trivy-action` version instead of the broken `@0.36.0` reference), it failed — but not because the app's own code was vulnerable: Trivy reported **3 `CRITICAL` CVEs in `perl-base`**, a package pulled in by the `python:3.10-slim` base image, not by anything in this repository. Every one of them had an empty "Fixed Version" column and a `fix_deferred` status — meaning no patched version exists yet to upgrade to, for any of them.
Originally pinned to `@master` — a mutable reference — later switched to `@v0.24.0`, an immutable release tag, for the same reason documented in "Automatic Tagging Strategy" above.
 
Blocking the pipeline forever on a CVE with no available fix doesn't protect anything — it just means the image can never be published again until upstream ships a patch that may or may not come. `ignore-unfixed: true` tells Trivy to only fail the build on `CRITICAL` vulnerabilities that **do** have a fix available, so the gate keeps doing its job (blocking anything you could actually act on) without holding the pipeline hostage to a vulnerability nobody, including the base image maintainers, can currently resolve.
 
### How the block actually works
 
GitHub Actions stops a job at the first failing step by default: if `scan image` exits with a non-zero code, every step after it — here, `push image` — is skipped entirely, and the job is marked failed. No extra `if:` condition checking the scan's outcome is needed for this: it falls out of the normal step-by-step execution model. A dangerous image is built and scanned, but never reaches `push image`, so nothing gets pushed anywhere.
 
### Proof
 
- **Scan genuinely failing** on the 3 unresolved `perl-base` CVEs (before `ignore-unfixed` was added): [run #33168401754](https://github.com/N-Haitu31/holbertonschool-continuous_integrations/actions/runs/33168401754) — the Trivy table lists all three, each with no fixed version, and `push image` never runs.
- **Scan passing and the image publishing** (after `ignore-unfixed: true`): [run #33168656389](https://github.com/N-Haitu31/holbertonschool-continuous_integrations/actions/runs/33168656389) — green, and `push image` executes.
- **Scan still passing after pinning to `@v0.24.0`**: [run #33171056728](https://github.com/N-Haitu31/holbertonschool-continuous_integrations/actions/runs/33171056728) — confirms the version pin didn't change the scan's behavior.
## Running locally
 
```bash
docker build -t mon-app .
docker run -p 5000:5000 mon-app
```