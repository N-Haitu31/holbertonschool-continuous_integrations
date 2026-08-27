# Building & Publishing Docker Images in CI
 
Exercise project for building and publishing Docker images with GitHub Actions. The repository reuses the app, `requirements.txt`, and `Dockerfile` from `docker_fundamentals/1-first_image/` in the `holbertonschool-devops-formation` repository (the earlier Docker Fundamentals project).
 
## Image Build
 
The workflow is defined in `.github/workflows/image.yml`.
 
**Trigger**: the workflow runs automatically on every `push` to the repository — as soon as a commit is pushed, GitHub Actions starts the job.
 
**Jobs**: the workflow contains a single job, `build`, running on an `ubuntu-latest` machine.
 
**Steps of the `build` job**:
1. **Checkout** (`actions/checkout@v4`) — fetches the repository's code onto the runner, making the `Dockerfile` and the app available for the next step.
2. **Build Image** — runs `docker build -t mon-app .`, building the image from the `Dockerfile` at the repository root (based on `python:3.10-slim`, installing the dependencies from `requirements.txt`, then running `app.py`) and tagging it locally as `mon-app`. Nothing is pushed to a registry at this stage — the goal is only to prove the image builds cleanly.
If `docker build` completes without errors, the job finishes successfully (green); otherwise the run fails and the build error is visible in the logs.
 
## Successful run
 
Example of a run where the image built successfully: [run #33065547354](https://github.com/N-Haitu31/holbertonschool-continuous_integrations/actions/runs/33065547354)
 
This link shows the `build` job passing: the checkout completed, and `docker build` produced the `mon-app` image from the reused `Dockerfile` without any error — proving the image builds cleanly on a machine that isn't the developer's own.
 
## Running locally
 
```bash
docker build -t mon-app .
docker run -p 5000:5000 mon-app
```
 