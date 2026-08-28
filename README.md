# Building & Publishing Docker Images in CI
 
Exercise project for building and publishing Docker images with GitHub Actions. The repository reuses the app, `requirements.txt`, and `Dockerfile` from `docker_fundamentals/1-first_image/` in the `holbertonschool-devops-formation` repository (the earlier Docker Fundamentals project).
 
## Image Build
 
The workflow is defined in `.github/workflows/image.yml`.
 
**Trigger**: the workflow runs automatically on every `push` to the repository — as soon as a commit is pushed, GitHub Actions starts the job.
 
**Jobs**: the workflow contains a single job, `build`, running on an `ubuntu-latest` machine.
 
**Steps of the `build` job**:
1. **Checkout** (`actions/checkout@v4`) — fetches the repository's code onto the runner, making the `Dockerfile` and the app available for the next step.
2. **Build Image** — runs `docker build -t mon-app .`, building the image from the `Dockerfile` at the repository root (based on `python:3.10-slim`, installing the dependencies from `requirements.txt`, then running `app.py`) and tagging it locally as `mon-app`. This step runs on every push, on every branch.
3. **Login to GHCR** (`if: github.ref == 'refs/heads/main'`) — authenticates to `ghcr.io` using `secrets.GITHUB_TOKEN` piped into `docker login` on stdin.
4. **Tag Image** (`if: github.ref == 'refs/heads/main'`) — tags the locally built image twice: once with the commit SHA, once with `latest`.
5. **Push Image** (`if: github.ref == 'refs/heads/main'`) — pushes both tags to `ghcr.io/n-haitu31/holbertonschool-continuous_integrations`.
Steps 3 to 5 only run when the workflow is evaluating the `main` branch (see "Publish to Registry" below). If `docker build` completes without errors, the job finishes successfully (green); otherwise the run fails and the build error is visible in the logs.
 
## Successful run (Task 0)
 
Example of a run where the image built successfully: [run #33065547354](https://github.com/N-Haitu31/holbertonschool-continuous_integrations/actions/runs/33065547354)
 
This link shows the `build` job passing: the checkout completed, and `docker build` produced the `mon-app` image from the reused `Dockerfile` without any error — proving the image builds cleanly on a machine that isn't the developer's own.
 
## Publish to Registry (Task 1)
 
### Authentication
 
The `login to ghcr` step never hardcodes a credential: it pipes `secrets.GITHUB_TOKEN` — generated automatically by GitHub for the run, scoped to this repository — into `docker login ghcr.io` on stdin. The workflow only needs `permissions: packages: write` to be allowed to push; no personal access token or manually created secret is involved.
 
### Tagging: SHA vs `latest`
 
Every push to `main` that publishes an image gets tagged twice, on the same image:
- **The commit SHA** (`${{ github.sha }}`) — immutable. It says exactly which commit produced this image, which is what you need to audit what's running or roll back to a known-good build.
- **`latest`** — a mutable, convenient pointer to whatever was most recently published from `main`. On its own it can't tell you which commit it corresponds to, which is why it's always published alongside the SHA tag, never instead of it.
### Gating
 
The `login`, `tag`, and `push` steps all carry `if: github.ref == 'refs/heads/main'`. The `build` step still runs on every push, on every branch, so a broken build is caught everywhere — but only a push that lands on `main` ever reaches the registry. A feature branch or a pull request can fail or succeed its build without ever publishing an image.
 
### Published image
 
The image is published on GHCR: [ghcr.io/n-haitu31/holbertonschool-continuous_integrations](https://github.com/N-Haitu31/holbertonschool-continuous_integrations/pkgs/container/holbertonschool-continuous_integrations), with both the `latest` and commit SHA tags visible on the same version.
 
Example of a run that logged in, tagged, and pushed successfully: [run #33156486925](https://github.com/N-Haitu31/holbertonschool-continuous_integrations/actions/runs/33156486925)
 
## Running locally
 
```bash
docker build -t mon-app .
docker run -p 5000:5000 mon-app
```