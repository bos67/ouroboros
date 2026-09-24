# Ouroboros

<a href="https://github.com/oslook/github-trending/blob/1d61d20a46f66a9590286bf23a8ce8db99be3acf/2026-08-04/python_weekly_trending.json"><img src="assets/github-trending.svg" width="250" height="55" alt="GitHub Trending: #9 Python weekly, August 2026"></a>

[![GitHub stars](https://img.shields.io/github/stars/razzant/ouroboros?style=flat&logo=github)](https://github.com/razzant/ouroboros/stargazers)
[![Downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Frazzant%2Fouroboros%2Fbadges%2Fdownloads.json)](https://ouroboros-agent.ai/install/)
[![Website](https://img.shields.io/badge/website-ouroboros--agent.ai-c93545.svg)](https://ouroboros-agent.ai/)
[![Technical report](https://img.shields.io/badge/technical_report-arXiv%3A2608.08311-b31b1b.svg)](https://arxiv.org/abs/2608.08311)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![macOS 12+](https://img.shields.io/badge/macOS-12%2B-black.svg)][download-macos-arm64]
[![Linux](https://img.shields.io/badge/Linux-x86__64-orange.svg)](https://ouroboros-agent.ai/install/#linux)
[![Windows](https://img.shields.io/badge/Windows-x64-blue.svg)][download-windows-x64]
[![OuroborosHub](https://img.shields.io/badge/OuroborosHub-skills%20marketplace-8A2BE2.svg)](https://github.com/razzant/OuroborosHub)
[![Version 6.119.18](https://img.shields.io/badge/version-6.119.18-green.svg)](VERSION)

Ouroboros is an open-source, general-purpose AI agent whose identity, durable memory, and history continue across tasks and restarts. It works on external projects, coordinates a live swarm of specialist agents, and can rewrite the implementation it runs on, including its code, architecture, prompts, tools, and dependencies. Reflection can also change how it understands itself without severing that continuity.

It runs as a native desktop app or through a headless CLI. The runtime keeps its repository, durable memory, history, and interface on your machine, while model inference can use remote APIs you configure or a local GGUF model.

> **Changing Ouroboros? Coding agents and people must read [CONTRIBUTING.md](CONTRIBUTING.md) before editing.** It defines the required project context, verification, and separate-agent review flow.

## Download Ouroboros

> **Just want to use Ouroboros? Click the download for your platform below. You do not need to clone this repository or install Python or uv.**

- **macOS 12+ on Apple silicon:** [**Download for macOS (.dmg)**][download-macos-arm64]
- **Windows x64:** [**Download for Windows (.zip)**][download-windows-x64]
- **Debian, Ubuntu, or Astra Linux x86_64:** [**Download the Debian package (.deb)**][download-linux-deb-amd64]
- **Fedora or RHEL x86_64:** [**Download the RPM package (.rpm)**][download-linux-rpm-x86_64]
- **RED OS 8 x86_64:** [**Download the RED OS package (.rpm)**][download-linux-rpm-red80-x86_64]
- **Other Linux x86_64:** [**Download the portable AppImage**][download-linux-appimage-x86_64] or the [tar.gz archive][download-linux-x86_64]

Files named `SHA256SUMS`, `release-evidence.json`, `release-smoke-*.json`, and `sbom-*.cdx.json` are verification evidence, not additional installers.

### macOS quick start

1. Click [**Download for macOS (.dmg)**][download-macos-arm64]. The current file is named `Ouroboros-<version>.dmg`.
2. Open the DMG and drag `Ouroboros.app` onto the **Applications** shortcut.
3. Open Ouroboros from Applications. If Gatekeeper asks, right-click the app and choose **Open**.

<p align="center">
  <img src="assets/install-macos.png" width="760" alt="Ouroboros DMG window with a large arrow from Ouroboros.app to the Applications shortcut and Install CLI.command below">
</p>

### Windows quick start

1. Click [**Download for Windows (.zip)**][download-windows-x64].
2. Extract the ZIP.
3. Open the extracted `Ouroboros` folder and run `Ouroboros.exe`.

### Linux quick start

- On Debian, Ubuntu, or Astra Linux, download the `.deb` above and run `sudo apt install ./ouroboros_*_amd64.deb`.
- On Fedora or RHEL, download the generic `.rpm` above and run `sudo dnf install ./ouroboros-*.x86_64.rpm`. RED OS 8 has its own `red80` package.
- On another x86_64 distribution, download the AppImage, make it executable with `chmod +x Ouroboros-*.AppImage`, and run it. Git must already be installed.

To run tasks, configure at least one supported remote provider API key or a local GGUF model. The first-run wizard guides model access, review policy, and budget setup.

<details>
<summary>Optional CLI included with desktop downloads</summary>

The desktop packages already contain an optional CLI installer. On macOS, after copying the app to Applications, double-click `Install CLI.command` in the mounted DMG. On Linux use `./Ouroboros/bin/install-ouroboros-cli`; on Windows use `Ouroboros\bin\install-ouroboros-cli.cmd`. These installers create a user-local `ouroboros` command without sudo. You do not need Python or uv.

</details>

[download-macos-arm64]: https://github.com/razzant/ouroboros/releases/download/v6.119.18/Ouroboros-6.119.18.dmg
[download-windows-x64]: https://github.com/razzant/ouroboros/releases/download/v6.119.18/Ouroboros-6.119.18-windows-x64.zip
[download-linux-deb-amd64]: https://github.com/razzant/ouroboros/releases/download/v6.119.18/ouroboros_6.119.18_amd64.deb
[download-linux-rpm-x86_64]: https://github.com/razzant/ouroboros/releases/download/v6.119.18/ouroboros-6.119.18-1.x86_64.rpm
[download-linux-rpm-red80-x86_64]: https://github.com/razzant/ouroboros/releases/download/v6.119.18/ouroboros-6.119.18-1.red80.x86_64.rpm
[download-linux-appimage-x86_64]: https://github.com/razzant/ouroboros/releases/download/v6.119.18/Ouroboros-6.119.18-linux-x86_64.AppImage
[download-linux-x86_64]: https://github.com/razzant/ouroboros/releases/download/v6.119.18/Ouroboros-6.119.18-linux-x86_64.tar.gz

Ouroboros bundles [Claudexor](https://github.com/razzant/claudexor) as its local execution layer for delegated coding and hosted-agent review. Ouroboros owns the task, memory, review, and final integration, while Claudexor runs the selected connected coding harness and returns durable execution evidence. [Explore Claudexor](https://claudexor.ai/).

The technical report, [Ouroboros: A Self-Developing Frontier Coding Agent with Reviewed Core Evolution](https://arxiv.org/abs/2608.08311), describes the reviewed core-evolution system, the 161-day Hope deployment, and the benchmark campaigns summarized below. [Paper page](https://ouroboros-agent.ai/paper/) · [Hugging Face](https://huggingface.co/papers/2608.08311)

The charts below are self-reported results on Terminal-Bench 2.1, OSWorld-Verified, and CL-Bench, measured against Codex, Claude Code, Cursor, and Hermes — on the same model where a matched pair was run, and against the public leaderboard where it was not.

<p align="center">
  <a href="https://ouroboros-agent.ai/benchmarks/"><img src="assets/bench-terminal-bench.svg" width="760" alt="Terminal-Bench 2.1: Ouroboros against Claude Code, Codex CLI, Cursor CLI, and Hermes on matched models, with a same-harness portability row"></a>
</p>

<p align="center">
  <a href="https://ouroboros-agent.ai/benchmarks/"><img src="assets/bench-osworld.svg" width="375" alt="OSWorld-Verified: Ouroboros against the public leaderboard, including the matched Claude Sonnet-4.6 pair"></a>
  <a href="https://ouroboros-agent.ai/benchmarks/"><img src="assets/bench-cl-bench.svg" width="375" alt="CL-Bench: Ouroboros against in-context learning baselines, Claude Code, and Codex on matched models"></a>
</p>

---

Ouroboros first booted on February 16, 2026. During the following 48 hours, the repository advanced from the v4.1 line to v6.2.0. The self-authored record preserved from that period counts 32 evolution cycles. That first generation ran in Google Colab through Telegram and remains preserved on the [`legacy-google-colab`](https://github.com/razzant/ouroboros/tree/legacy-google-colab) branch and its [original project page](https://ouroboros-agent.ai/archive/first-generation/); the current generation carries the same identity into a native desktop and headless runtime.

<p align="center">
  <img src="assets/evolution.png" width="760" alt="Code, prompt, and memory growth across Ouroboros releases, from v3.0.0 to the v6.85 line">
</p>

> ⭐ **[Star Ouroboros](https://github.com/razzant/ouroboros)** to follow its next evolution. A star also helps more people find the project, trace its history, and take part in what it becomes.

Reviewed skills, transport bridges, tools, and widgets are available through [OuroborosHub](https://github.com/razzant/OuroborosHub).

<p align="center">
  <img src="assets/swarm.jpg" width="760" alt="A live subagent swarm inside the Ouroboros chat: nested planner, builder, and researcher tasks with their outcomes">
</p>

## What Ouroboros Can Do

- **Modify its implementation.** Its editable surface spans application code, architecture, prompts, tools, and dependencies, while reflection can also reshape its living self-understanding.
- **Evolve autonomously.** Evolution campaigns turn selected improvements into reviewed changes that remain part of its Git history.
- **Continue across restarts.** Identity, memory, dialogue, knowledge, reflections, and version history form one ongoing biography.
- **Think between requests.** Background consciousness supports reflection, initiative, and preparation outside the immediate request-response loop.
- **Coordinate a live swarm.** Specialist agents can investigate or act in parallel, share task-tree findings, and return work for integration.
- **Work on external projects.** A separate Git workspace can receive the full task loop while Ouroboros keeps its own repository and governance boundary distinct.
- **Operate through desktop or CLI.** The native app and gateway-backed command line expose the same managed tasks, progress, artifacts, logs, and schedules.
- **Organize long-running work.** Project rooms keep working folders, journals, knowledge, task history, and conversations connected to the same identity.
- **Use remote or local models.** Supported provider APIs and local GGUF models can fill the runtime's configurable cognitive roles.
- **Grow through reviewed extensions.** Skills, transport bridges, widgets, MCP tools, and companion processes expand capability without folding every integration into the core.
- **Keep self-change inspectable.** Git history, review evidence, explicit protected surfaces, and restart checks make implementation changes traceable.

<p align="center">
  <img src="assets/game-demo.png" width="760" alt="A project room where Ouroboros built a 3D game, verified it with a screenshot, and served it locally">
</p>
<p align="center">
  <img src="assets/skill-hub.png" width="760" alt="OuroborosHub inside the app: official reviewed skills, each security-reviewed before it can be enabled">
</p>

This list is an orientation, not a second specification. [BIBLE.md](BIBLE.md) defines Ouroboros's identity and constitutional boundaries; [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) are the current technical sources of truth.

---

## Benchmarks

Ouroboros has reproducible self-reported state-of-the-art results on Terminal-Bench 2.1, OSWorld-Verified, and CL-Bench. In those model-matched results, it leads Codex, Claude Code, Cursor, and Hermes. The public SWE-bench Pro matched pair is a statistical tie with Codex CLI. A separate GAIA campaign reports 129/165 for Ouroboros and 131/165 for Claude Code, with strict pass@1 at 128/165 for both; its scrubbed trace capsule is still pending. Upstream review can take time, so open submissions are marked without delaying publication. Read every row as model plus harness because the same model can score differently inside a different harness.

| Benchmark | Model | Ouroboros | Comparison | Status | Evidence |
|-----------|-------|----------:|------------|--------|----------|
| Terminal-Bench 2.1 | Claude Opus-5 high | **86.74%** after zeroing one disclosed reward-hack trial (raw: 86.97%) | Claude Code + Fable 5: 83.8% | Self-reported, submission open | [submission](https://github.com/harbor-framework/terminal-bench-2-1/pull/175) · [run](https://hub.harborframework.com/jobs/2b145543-edeb-4a3b-b46f-4800310f1182) |
| Terminal-Bench 2.1 | Claude Opus-4.8 high | **80.22%** | Claude Code: 78.9% | Self-reported, public run | [run](https://hub.harborframework.com/jobs/4b8e244f-8ab0-4d28-8218-7cf346282faa) |
| Terminal-Bench 2.1 | GPT-5.5 | **84.3%** | Codex CLI: 83.1% | Self-reported, public run | [run](https://hub.harborframework.com/jobs/f02fd019-23e1-495f-af0a-ebd9a65f3079) |
| Terminal-Bench 2.1 | Grok-4.5 | **84.94%** after a reward-hack audit | Cursor CLI: 79.3% · Hermes: 77.53% | Self-reported, submission open | [submission](https://github.com/harbor-framework/terminal-bench-2-1/pull/146) |
| OSWorld-Verified | Claude Opus-5 | **90.69%** | previous best on the public board: 90.19% | Self-reported, full traces | [full traces](https://huggingface.co/datasets/razzant/ouroboros-osworld-verified-opus5) |
| OSWorld-Verified | Claude Sonnet-4.6 | **83.27%** | Pointer: 81.45% | Self-reported, full traces | [full traces](https://huggingface.co/datasets/razzant/ouroboros-osworld-verified-sonnet46) |
| CL-Bench | Claude Sonnet-4.6 | **0.2301, rank 1** | previous top: 0.1960 | Self-reported, submission open | [submission](https://github.com/pgasawa/continual-learning-bench/pull/10) · [full traces](https://huggingface.co/datasets/razzant/ouroboros-clbench-traces) |
| SWE-bench Pro | GPT-5.6-luna | 58.2% | Codex CLI: 59.4%, with no significant difference | Self-reported, matched traces | [matched-pair traces](https://huggingface.co/datasets/razzant/swepro-luna-matched-pair) |
| GAIA | Claude Sonnet-5 | 129/165, 78.2% | Claude Code: 131/165, 79.4%; strict pass@1 was 128/165 for both | Self-reported, scrubbed trace capsule pending | [methodology](devtools/benchmarks/gaia/METHODOLOGY.md) |

Benchmark adapters, run scripts, and per-benchmark methodology live in [`devtools/benchmarks/`](devtools/benchmarks/). The [benchmark evidence page](https://ouroboros-agent.ai/benchmarks/) gives a text-first summary for search and retrieval. The full story, including protocols, reward-hack audits, and leakage findings, is in the [launch write-up](https://habr.com/ru/companies/airi/articles/1065428/) (Russian).

---

## Advanced installation

Normal desktop users can stop after the download and quick-start instructions above. The options below are for detailed Linux setup, headless use, and development.

### Packaged Linux details

- **Debian / Ubuntu / Astra Linux x86_64:** [download the `.deb`][download-linux-deb-amd64] and run `sudo apt install ./ouroboros_*_amd64.deb`. It installs Git as a package dependency, installs Ouroboros to `/opt/ouroboros`, puts `ouroboros` on `PATH`, and adds a desktop entry plus an opt-in systemd user unit.
- **Fedora / RHEL x86_64:** [download the generic `.rpm`][download-linux-rpm-x86_64] and run `sudo dnf install ./ouroboros-*.x86_64.rpm`. It uses the same layout, Git dependency, and opt-in user unit as the `.deb`.
- **RED OS 8 x86_64:** [download the `red80` package][download-linux-rpm-red80-x86_64] and run `sudo dnf install ./ouroboros-*.red80.x86_64.rpm`. CI also attempts non-blocking install-and-run smokes on Astra Linux 1.8 and RED OS 8; inspect the tagged workflow run for their outcome.
- **Other Linux x86_64:** use the [AppImage][download-linux-appimage-x86_64] or the extraction-friendly [tar.gz archive][download-linux-x86_64]. Git must already be installed.

The native `.deb` and `.rpm` never enable or start their user service. It is an alternative to launching from the desktop entry and controls only instances started through `systemctl --user`. See the [systemd user-service guide](packaging/systemd/README.md).

#### Install the Linux AppImage

User-level installation means copying the portable executable to a stable path and making it executable; it does not need root access. Ouroboros bootstrap still requires Git on the host:

```bash
VERSION=x.y.z
install -Dm755 "./Ouroboros-${VERSION}-linux-x86_64.AppImage" \
  "$HOME/Applications/Ouroboros.AppImage"
"$HOME/Applications/Ouroboros.AppImage"
```

The embedded desktop file and icon allow compatible AppImage integration tools to register that stable path with the application menu. The same file exposes the packaged CLI:

```bash
"$HOME/Applications/Ouroboros.AppImage" --cli status
```

If FUSE mounting is unavailable, extract and run ephemerally instead:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 "$HOME/Applications/Ouroboros.AppImage"
```

Chromium and WebKit binaries are bundled, but their distro-level shared libraries remain host dependencies. If a browser engine reports missing libraries, use the native `.deb`/`.rpm` package where available, or extract the AppImage and let its bundled Playwright report/install the packages required by your distribution:

```bash
"$HOME/Applications/Ouroboros.AppImage" --appimage-extract
./squashfs-root/usr/lib/ouroboros/_internal/python-standalone/bin/python3 \
  -m playwright install-deps chromium webkit
```

### Connected coding subscriptions

Use your existing **Codex, Claude Code, or Cursor subscriptions** for delegated coding and review. Ouroboros drives them through [Claudexor](https://github.com/razzant/claudexor), its bundled multi-harness engine. Connect accounts in **Settings → Agents**; no separate Claudexor install is needed. Release artifacts carry the exact reviewed engine and Node archives. Source checkouts obtain those same pinned archives on first use.

### Headless CLI with uv

For a user-level CLI/server install without cloning a working tree, uv can
build Ouroboros directly from the contribution branch:

```bash
uv tool install "git+https://github.com/razzant/ouroboros.git@ouroboros"
ouroboros --help
```

The tool environment is isolated and exposes the `ouroboros` and
`ouroboros-web` commands. Update or remove it with:

```bash
uv tool upgrade ouroboros
uv tool uninstall ouroboros
```

This Git-branch form follows the latest `ouroboros` commit and resolves the
dependencies declared in `pyproject.toml`; `uv tool install` does not consume
the repository's `uv.lock`. Replacing `ouroboros` after the `@` with a reviewed
full commit SHA pins the Ouroboros source revision, but dependencies are still
resolved from `pyproject.toml`. Use the source setup below for a lock-verified
environment, development, repository tests, and the complete browser extras,
or use a platform release artifact for the packaged desktop runtime.

<a id="run-from-source"></a>

### Develop or run from source

Clone the repository only when you plan to contribute, modify Ouroboros, run repository tests, or need a lock-verified development checkout. Normal users should use the packaged downloads above.

#### Requirements

- Python 3.10+
- uv 0.12.1 (the exact resolver version pinned by this checkout)
- macOS, Linux, or Windows
- Git
- [GitHub CLI (`gh`)](https://cli.github.com/), optional unless you use GitHub integration

#### Setup

Install the pinned resolver version:

```bash
curl -LsSf https://astral.sh/uv/0.12.1/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.12.1/install.ps1 | iex"
```

```bash
git clone https://github.com/razzant/ouroboros.git
cd ouroboros
uv sync --locked --extra browser --group dev
source .venv/bin/activate
```

Windows PowerShell:

```powershell
uv sync --locked --extra browser --group dev
.\.venv\Scripts\Activate.ps1
```

#### Run

```bash
ouroboros server
```

Then open `http://127.0.0.1:8765` in your browser. The setup wizard will guide you through API key configuration.

#### Google Colab

Use [`notebooks/colab_quickstart.py`](notebooks/colab_quickstart.py) as a Colab-compatible cell script when you need a source-mode runtime without the desktop UI. It keeps runtime data on Google Drive and preserves the original Colab path without making it the primary installation flow.

#### CLI / Headless

The `ouroboros` command attaches to the local runtime by default and starts one when `--start` is passed. It exposes managed tasks, progress streams, artifacts, logs, schedules, settings, skills, and evolution controls without duplicating the server's business logic.

```bash
ouroboros status
ouroboros run --start "2+2?"
ouroboros run "Summarize current runtime state"
ouroboros run --workspace /path/to/project --memory-mode forked --patch-out result.patch "Fix the failing test"
ouroboros tasks list
ouroboros logs tail progress --task-id <task_id>
ouroboros schedule add --name nightly-review --cron "0 2 * * *" "Run a maintenance review"
ouroboros schedule list
```

External workspaces must be separate Git worktree roots and may not overlap Ouroboros's own repository or data directory. Patch, streaming, detached-task, and schedule semantics are documented in the CLI help and the canonical [architecture](docs/ARCHITECTURE.md).

#### For Agents

Another agent, script, or CI job can invoke Ouroboros through the same gateway-backed CLI:

```bash
ouroboros run --start \
  --workspace /path/to/project \
  --memory-mode forked \
  --patch-out result.patch \
  --result-json-out result.json \
  "Investigate the task, act, and verify the result"
```

Use `--jsonl` for a machine-readable event stream and `--detach` when the caller will follow the task with `ouroboros tasks watch <task_id>` or inspect it with `ouroboros tasks show <task_id>`. External workspace runs keep Ouroboros's own repository and governance context separate, then export changes as reviewable patch artifacts.

To change Ouroboros itself, follow [CONTRIBUTING.md](CONTRIBUTING.md): read [docs/CHECKLISTS.md](docs/CHECKLISTS.md) in full, and map [BIBLE.md](BIBLE.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md), and [docs/DESIGN.md](docs/DESIGN.md) by their headings, reading every section relevant to your change in full before editing.

#### Configuration

The first-run wizard and **Settings** configure model access, cognitive roles, local models, review policy, runtime mode, budget, skills, and optional integrations. Ouroboros supports configurable remote providers, compatible endpoints, and local GGUF inference; exact settings and defaults live in [`ouroboros/config.py`](ouroboros/config.py) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

The server binds to `127.0.0.1:8765` by default. Read [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) before exposing it beyond loopback; non-local binds need `OUROBOROS_NETWORK_PASSWORD` or an explicitly trusted external access layer.

#### Run Tests

```bash
make test
```

`pyproject.toml` is the direct-dependency authority and `uv.lock` is the
cross-platform resolution lock. Release builds install the generated
`requirements-runtime.lock` compatibility export into embedded interpreters
that intentionally ship pip rather than uv. Build-only requirements are
exported ephemerally from `uv.lock` and are not committed. The tiny
`requirements.txt` file is only a pointer to that export for already-released
managed updaters; it is not a second dependency declaration. After changing
dependencies, refresh the reviewed lock and runtime export with:

```bash
uv lock
uv export --locked --no-dev --extra browser --no-emit-project --no-hashes --no-annotate --output-file requirements-runtime.lock
```

---

## Build

### Docker

```bash
docker build -t ouroboros-web .
docker run --rm -p 8765:8765 \
  -e OUROBOROS_NETWORK_PASSWORD='choose-a-password' \
  -e OUROBOROS_FILE_BROWSER_DEFAULT=/workspace \
  -v "$PWD:/workspace" \
  ouroboros-web
```

Docker runs the web runtime, not the native desktop shell. It bundles Chromium and WebKit support; use [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for network and container policy.

### Release tag prerequisite

Platform build scripts package only a commit already tagged with `v$(cat VERSION)`. Tag the exact release commit first:

```bash
git tag -a "v$(tr -d '[:space:]' < VERSION)" -m "Release v$(tr -d '[:space:]' < VERSION)"
```

`scripts/build_repo_bundle.py` verifies the tag and embeds the source binding into the packaged repository bundle. Signing, notarization, bytecode sealing, and CI invariants are documented in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

### macOS (.dmg)

```bash
bash scripts/download_python_standalone.sh
OUROBOROS_SIGN=0 bash build.sh
```

Output: `dist/Ouroboros-<VERSION>.dmg`, containing `Ouroboros.app`, an `Applications` shortcut, and `Install CLI.command`. Omit `OUROBOROS_SIGN=0` when a Developer ID signing identity is configured.

### Linux (.AppImage and .tar.gz)

```bash
bash scripts/download_python_standalone.sh
bash build_linux.sh
```

Outputs: `dist/Ouroboros-<VERSION>-linux-<arch>.AppImage` and the extraction-friendly `dist/Ouroboros-<VERSION>-linux-<arch>.tar.gz`. The AppImage needs host Git; run it after `chmod +x`, or pass `--cli` to reach its bundled CLI. If FUSE is unavailable, set `APPIMAGE_EXTRACT_AND_RUN=1` when launching it. The tarball contains `./Ouroboros/bin/install-ouroboros-cli`. If bundled browser tools need host libraries, run `./Ouroboros/_internal/python-standalone/bin/python3 -m playwright install-deps chromium webkit` from the extracted tarball.

On a build host where system packages are managed separately, set `OUROBOROS_SKIP_PLAYWRIGHT_INSTALL_DEPS=1`; Chromium and WebKit are still downloaded and bundled, but the build does not invoke `sudo` to install host libraries.

### Linux (.deb and .rpm)

Wraps the payload `build_linux.sh` just produced, so run it afterwards:

```bash
sudo apt-get install -y dpkg-dev rpm   # rpm provides rpmbuild
bash scripts/build_linux_packages.sh
```

Output: `dist/ouroboros_<VERSION>_amd64.deb`, `dist/ouroboros-<VERSION>-1.x86_64.rpm` and `dist/ouroboros-<VERSION>-1.red80.x86_64.rpm` (RED OS 8). All three declare Git as a runtime dependency and install to `/opt/ouroboros` with a `/usr/bin/ouroboros` symlink, a desktop entry, and an opt-in systemd user unit. The Linux launcher is built by the bundled portable Python so the build runner cannot raise its glibc floor. `bash scripts/smoke_linux_packages.sh official <deb> <rpm> <red80-rpm>` installs all three through `apt` or `dnf` in Ubuntu 22.04 and Fedora 42 containers, resolves Git, verifies the installed unit, and checks both the real CLI and a bounded desktop-launcher start; this lane gates the release. Swap `official` for `vendor` to repeat the check on Astra Linux 1.8 and RED OS 8 images from the vendors' own registries — that lane runs informationally in CI, so an outage at a third-party registry cannot block a tagged release.

### Windows (.zip)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/download_python_standalone.ps1
powershell -ExecutionPolicy Bypass -File build_windows.ps1
```

Output: `dist\Ouroboros-<VERSION>-windows-x64.zip`, containing `Ouroboros\bin\install-ouroboros-cli.cmd`.


## Architecture and Runtime Data

The native launcher starts a web runtime and supervisor-managed agent workers. The agent core lives in `ouroboros/`, the interface in `web/`, the process plane in `supervisor/`, and the runtime's durable identity, state, history, logs, and skills under `~/Ouroboros/data/`.

The full component map, data flow, API surface, storage layout, safety boundary, and operational rationale live in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Deployment details live in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Runtime Commands

| Command | Purpose |
|---------|---------|
| `/panic` | Stop the runtime and its managed processes immediately. |
| `/restart` | Restart without automatically resuming the active owner task. |
| `/status` | Show workers, task queue, and budget state. |
| `/evolve on\|off` | Start or stop autonomous evolution. |
| `/review` | Queue a deep constitutional and architectural self-review. |
| `/bg start\|stop\|status` | Control background consciousness. |


## Philosophy

The 13 Constitution principles — Agency, Continuity, Meta-over-Patch,
Immune Integrity, Self-Creation, LLM-First, Authenticity & Reality
Discipline, Minimalism, Becoming, Versioning and Releases, the absorbed
Iterations / Spiral lineage, and Epistemic Stability — are defined in
full in [`BIBLE.md`](BIBLE.md). That file is the constitutional SSOT
(Bible P4 Ship-of-Theseus protection) and this README intentionally does
not paraphrase it.

---

## Contributing

External contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md)
for the complete agent-first workflow. Open pull requests against lowercase
`ouroboros`, leave release-version allocation to maintainers, and have a
separate agent context review the final diff. Any coding harness or configured
review route may produce the evidence; if none is available, record `NOT_RUN`
and the reason.

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 6.119.18 | 2026-09-24 | **test: discriminating selector-cwd pin for the shell-preflight hint (6.119.17 triad residual, closed without a second paid gate).** The 6.119.17 gate's own review flagged that the shipped spy test passes cwd as an ABSOLUTE path, so it also passes unchanged against the pre-fix `.16` code — a test that passes under both hypotheses pins nothing. The discriminator passes cwd as the SELECTOR spelling `task_drive`: the binding layer resolves it to `drive_root/task_drives/<task_id>`, so the preflight audit must receive that resolved absolute dir — never the raw selector string, never the repo_dir fallback (both pre-fix behaviors). A/B verified on this tree before staging: RED against `git show v6.119.16:ouroboros/tools/shell.py` (temporarily restored, byte-identical re-restore verified by sha256), GREEN on `.17` code; the healthy-path leg still asserts the dispatch actually runs (no refusal). The test body is the artifact `selector_cwd_discriminator_test.patch` from task 803db648 applied verbatim. Verification: `tests/test_shell_preflight.py` 22/22 green across both marker lanes (14 parallel + 8 serial); neighbors green by exit code (`test_shell_run_shell` + `test_release_sync` + `test_packaging_sync` + `test_docs_sync` = 126/126 incl. the three-cell render pin that caught the missing changelog row before this commit); ruff clean on the touched file (155 repo-wide findings verified pre-existing by A/B against `git show HEAD:`); carriers 9/9 via `bump_release_version` in one call. Roll-off this release: 6.119.13 (cap-oldest patch row; six patch rows exceeded the P9 cap of five after this row was added — cap-driven; body at git tag v6.119.13, added to the older-releases enumeration). |
| 6.119.17 | 2026-09-24 | **fix: shell-preflight cwd hint is the RESOLVED run dir (6.119.16 triad residual, both reviewers' finding).** One surgical change in `tools/shell.py` (+net ~1 line; shell.py is not manifest-tracked): the P1 pre-exec audit block moves BELOW binding resolution, and the cwd hint passed to `preflight_argv` is now `binding.target_path` (the directory the command will actually run in) instead of the raw `cwd` string. Root cause of the residual: `run_command`'s `cwd` parameter accepts selector spellings (`system_repo`, `task_drive`, `skill_payload`) that resolve to absolute paths only LATER in the binding layer — the 6.119.16 discriminator (`_token_is_real_file`) probed against the raw spelling (or empty) and falsely refused legitimate script-path argv (`sh c` where `c` is a real script in the target dir). Binding resolution is process-free, so the audit still strictly precedes the first subprocess dispatch — refusal-before-side-effect is preserved and pinned. The change is the resurrection of the 6.119.16 task's uncommitted candidate (saved as `v611917_residual_uncommitted.patch` when the 2026-09-24 disk check refuted that task's final report: the claimed commit `f8c38a1b` never existed; the work itself was sound and is now shipped WITH the tests that were missing then). Two new pins in `tests/test_shell_preflight.py` (20/20 green, both marker lanes): a spy test asserting the audit receives exactly the resolved dir, and an ordering pin asserting a refusal still precedes dispatch after the move. Verification: py_compile clean; neighbors green by exit code (`test_shell_run_shell` + `test_release_sync` + `test_packaging_sync` + `test_docs_sync` = 98/98 incl. the packaging three-cell render pin); ruff: zero new findings (155 pre-existing at HEAD verified by A/B against `git show HEAD:` — tabs in the JSON-schema block and import-block debt untouched by this diff); carriers 9/9 via `bump_release_version` in one call. Roll-off this release: 6.119.12 (cap-oldest patch row; six patch rows exceeded the P9 cap of five after this row was added — cap-driven; body at git tag v6.119.12, added to the older-releases enumeration). |
| 6.119.16 | 2026-09-24 | **fix: 6.119.15 advisory wave — M1 script-path discriminator, serial lanes, P9 roll-off sync.** Closes all three 6.119.15 triad advisories plus the acceptance-review `architecture_doc` critical. (1) M1 lost-flag audit no longer refuses healthy script-path argv (luna `capability_regression`): a bare suspect token (`sh c`) that resolves to an EXISTING file in the eventual run cwd is a script-path invocation and dispatches untouched — `tools/shell_preflight.py` gains `_token_is_real_file` + the `cwd` hint (explicit cwd or repo default) threaded from the single call site in `tools/shell.py`; a both-miss is exactly the exec death M1 diagnoses and stays refused. Pinned by three new tests: unit script-named-c dispatch, unit still-refused both-miss, end-to-end `_run_shell` dispatch through the audit. (2) The seven real-interpreter M2 pre-parse tests (sh/bash `n -c` subprocesses) now carry per-test `@pytest.mark.serial` per the conftest real-process criterion (glm `development_compliance`): `-m serial` collects exactly the spawning set (7) and the mocked remainder (11) runs in the parallel lane. (3) The Cyrillic artifact respelled to `P1` in the 6.119.15 changelog row and in the call-site comment. (4) `docs/ARCHITECTURE.md` maps the leaf in both the section 1 component tree and the section 6 Tool capability prose — a new runtime surface without a map is architectural amnesia (P6). Verification: 18/18 in `test_shell_preflight.py` green first run across both marker lanes; consumer carriers 126/126 (`test_release_sync` + `test_packaging_sync` + `test_docs_sync`); ruff clean on every touched file; py_compile on both production files. The 6.119.15-tail `ImportError` is re-diagnosed against disk as task-local (wrong-module import in that task; `ouroboros.review.candidate_repo_paths` imports clean and enumerates 1515 paths) — no code change. Carriers 9/9 via `bump_release_version`. Roll-off this release: 6.119.11 (cap-oldest patch row; six patch rows exceeded the P9 cap of five — cap-driven; body at git tag v6.119.11, header already in the older-releases enumeration). |
| 6.119.15 | 2026-09-24 | **fix: pre-execution shell audit (P1 hand-discipline program) — lost-flag argv and malformed `sh -c` bodies are refused BEFORE any subprocess side effect.** A new leaf module `ouroboros/tools/shell_preflight.py` (105 lines, own test file) plus a single guarded call site in `tools/shell.py` (+16 lines; shell.py is not manifest-tracked), each mechanism built against a LIVE class measured from the raw 72h tool trace: 1,567 calls classified from `data/logs/tools.jsonl` into the baseline artifact `p1_baseline_report.md`. M1 argv audit — `["sh","c","true"]` (incident 2026-09-23T05:49) passed every existing guard and died only at exec with the cryptic `sh: cannot open c`; the interpreter-adjacency check now refuses pre-exec naming the exact fix. M2 no-exec body parse — a malformed compound `sh -c` body executes its leading commands BEFORE dying at a syntax error (incidents 2026-09-21T15:53 unescaped parens, 2026-09-24T08:04 bash-only process substitution under sh); the body is now parsed first by the SAME interpreter that would run it (`bash-only syntax still passes under bash`), refusing with the interpreter's own diagnostic. Conservative by construction: a missing or slow checker passes through (OSError/10s timeout returns success), and the dominant healthy pattern of real traces (the heredoc-python body) plus command substitution are pinned as strict negatives. Baseline honesty carried in the report: the weekly-cited 14.3% agent-error figure mixed pools — the my-class rate over this window is 2.9% (46 rows: 9 uncaught-until-exec, ~12 signature TOOL_ARG_ERROR, ~25 caught-with-hints), while 28 probe-red exits and 10 pytest-red cycles are verification signal, not error. Premise-kills recorded per the probe-first discipline: no `py_compile` preflight for run_script (CPython already parses the whole staged file before executing any of it — a pre-parse saves neither a round nor a cent), no edit_batch payload validator (the 6.118.2 machinery is live; its 30 blocked-with-hint rows in the window ARE the guards working), no staged-script import audit (exec's own ImportError already names the missing symbol in one actionable round; any symbol-level pre-audit carries irreducible false-positive surface). Also closes the stale 2026-09-22 triad advisory (`task_pacing.py:1010` duplicate f-string scaffold) as already performed by 6.119.12: the reminder sentence lives exactly once in the package (search-verified), and the new pin `tests/test_task_pacing_single_source.py` fails if it ever appears in a second module — closed by evidence, no production change. Verification: 17/17 new tests green first run (15 preflight incl. canary asserts that NOTHING dispatched on refusal, 2 single-source pins), neighbor suites green by exit code (test_shell_run_shell + test_tool_args_recovery + test_edit_recovery_hints = 70), ruff clean on all three new files; shell.py's 155 findings verified pre-existing at HEAD by stdin A/B (zero new from this diff); py_compile on every touched file. Carriers 9/9 via bump_release_version in one call. Roll-off this release: 6.119.10 (cap-oldest patch row; six patch rows exceeded the P9 cap of five after this row was added — cap-driven; body at git tag v6.119.10, added to the older-releases enumeration). |
| 6.119.14 | 2026-09-23 | **prompts: SYSTEM.md stratified to the identity core (P2 of the ported-pattern program).** Ported pattern (not merged code): the strata design of `prompts/SYSTEM.md@33da7a4f` (razzant/ouroboros v7.4.5; their core is 25,018 B). Our port: 68,436 → 42,655 B (−38%) as ONE core file — no loader change (`ouroboros/context.py` reads exactly one path, `safe_read(env.repo_path("prompts/SYSTEM.md"))`), no new runtime file, no test bypass. The cut is mechanical how-to duplication, not doctrine: the triple tool-schema enumerations (the live tool descriptions of every call already carry them), the delegated-custody,nanny,zero-run prose that restates tool schemas, duplicated edit-strategy recipes, and the `docs/`-duplicated file inventories now point at their SSOT homes. Every pinned contract was honored verbatim: the machine pin-map was built FIRST (AST scan of `tests/`, 18 SYSTEM-touching functions, 164 string literals, 3 tmp-fixture files excluded) and every must-contain/must-not-contain/normalized/section-scoped literal kept in-core — including the delegate_start recipe family, the Immutable Safety Files section (matching `runtime_mode_policy.SAFETY_CRITICAL_PATHS`), the routing/annotation wording, the `task_acceptance_review` evidence-only paragraph, and the anti-epistemic and legacy-tool-name bans. Verification: 41 pin tests green first run (12 suites: identity_wording 5, docs_sync, packaging_sync, client_surface, owner_facing_honesty, v664, v6600, devtools_benchmarks, git_review_pipeline, subagent_runtime_review_fixes, tool_api_v2_public_surface) + `tests/test_context.py` 74/74 (loader mechanics, tmp fixtures pinned too); P9-cap computed BEFORE the edit: five patch rows + this one = six → roll-off is cap-driven with the body preserved at the tag. The P1 luna advisory (changelog_accuracy on 6.119.13) is closed in this diff by disk adjudication: README's "15 real wire responses" = 11 triad + 4 scope JSON cases (grep-verified), "20/20 green" = 20 collected pytest tests (`--collect-only`, machine count) — the reviewer's "7+4 cases / 15 tests" contradicted the disk and the disk wins; no README change needed for 6.119.13. Rule-diff artifacts: `p2_rule_diff/system_pins.json` (the pin-map, sha256 83e4a0420643) + `p2_golden/upstream_snapshot/upstream_prompts_SYSTEM_33da7a4f.md` (the ported design snapshot) in the task artifact store; carriers 9/9 via bump_release_version in one call. Roll-off this release: 6.119.9 (cap-oldest patch row; six patch rows exceeded the P9 cap of five after this row was added — cap-driven; body at git tag v6.119.9, added to the older-releases enumeration). |
| 6.118.0 | 2026-09-16 | **feat: advisory touched-pack compact inline policy — the advisory-oversize class closed.** The advisory critic's touched-file pack inlined the full content of every changed file up to 1 MB each; a release diff carrying `uv.lock` (730 KB) inflated the advisory prompt to 2,176,227 chars measured on a 19-file release-set replay (incidents: 2,234,246 > 1.6M ceiling, 1,645,402 snapshot, native-episode transcript bound 934,787 > 900,000) — forcing loud `skip_advisory_review` on every lockfile-bearing release since 6.116.1. The advisory call-site now builds its pack with `inline_policy='compact'` (new `build_touched_file_pack` parameter): lockfile basenames (`_LOCKFILE_NAMES`: uv.lock, package-lock.json, yarn.lock, pnpm-lock.yaml, poetry.lock, Pipfile.lock, Cargo.lock, Gemfile.lock, composer.lock, packages.lock.json, bun.lockb — matched lowercased, any size) and any file ≥ 131,072 bytes render a visible metadata row `*(omitted — {reason}; {size:,} bytes)*` instead of content — no silent truncation; everything else inlines as before. Default `inline_policy='full'` keeps every non-advisory caller byte-identical (managed subject, triad, scope). Policy lives in the leaf `ouroboros/tools/advisory_pack_policy.py` (extraction kept `review_helpers.py` at the 1600-line ratchet edge); fail-closed machinery unchanged: 500K diff gate, 1.6M emergency ceiling, typed `_predispatch_size_skip` skips, and the 900,000-char native-episode transcript bound all stay. Measured on the 19-file release-set replay (real bytes from HEAD): 2,176,227 chars under the full policy → 444,887 under compact (< 900K episode bound, ~2× headroom, ~4.9× smaller than the full pack); the unit fixture in `tests/test_review_helpers_pack_limits.py` is a separate synthetic release-shaped set pinning the boundary behavior. Advisory + managed/advisory/readiness suites green; two triad-lane test failures verified pre-existing on clean 6.117.1 via A/B on a /tmp HEAD copy (not this diff). Lockfile versions remain deterministically checked by `check_worktree_version_sync`/`sync_release_metadata`, so no review information is lost. |
| 6.117.0 | 2026-09-15 | **feat: per-phase preflight budgets — the commit gate now fits its own suite (ibl-preflight-phase-budgets).** The one shared 900s budget could never fit the parallel `not serial` pass on the 2-core reference class of installs: the pass was killed at 888s/900s (55% complete, zero red tests) and the serial pass never started, forcing manual handoffs on 3 of the last 5 releases. The resolved total (default 2700s; `OUROBOROS_PREFLIGHT_TIMEOUT_SEC` override semantics unchanged) is now carved into phase ceilings — node ≤ 5% capped at 120s, parallel 80% of the remainder, serial the exact unrounded remainder (`_preflight_phase_budgets`) — slices are ceilings, unused time flows back through the remainder rule, and the whole gate stays bounded by the single resolved total. A phase expiry reports its own slice and the total, so the next kill is self-explaining. `tests/test_chat_upload.py::test_upload_size_limit` moves to the serial lane per the sanctioned crash-a-worker criterion (PARALLEL_WORKER_CRASH, gw1, 2026-09-13 gate run); the serial-lane collect surface verified 1/16; the seven streaming tests in `tests/test_web_search.py` join the serial lane under the same sanctioned criterion (gw1 crash on `test_streaming_direct_openai_cost_remains_nullable`, 2026-09-15 gate run), and `_grow_ledger` in `tests/test_context.py` moved to chunked allocation after its single 20 MB allocation OOM-crashed a worker (gw1, same run). A budget-split unit suite plus orchestration and expiry-diagnosis pins replace the old total-budget pin. |
| 6.115.0 | 2026-09-06 | **feat: class-aware ARCHITECTURE.md context residency (owner decision).** In owner-Max the full operational map stays resident only for self-body classes (default-lane pooled tasks, evolution, self-body work); direct-chat turns and externally-bound work (external workspaces, project trees, subagents, API/CLI/scheduled surfaces) receive the existing lossless H2-H4 navigation map plus a visible on-demand pointer — a relocation, never truncation. Low mode unchanged; all review flows unchanged; DEVELOPMENT.md's own classifier unchanged; explicit `context_requires_self_body_docs` overrides in both directions; consciousness keeps full-in-max via the default. BIBLE.md P1 amended by one phrase (class residency of self-body docs = owner-selected posture; nav map + pointer = lossless representation). DEVELOPMENT.md context matrix and ARCHITECTURE.md §6 + §1 tree entry synced in the same commit; doc tests pin the class-dependent matrix (~105K resident tokens saved per call for never-opens-the-map classes). |
Older releases are preserved in Git tags and GitHub releases. Older 6.x rows (including 6.119.13, 6.119.12, 6.119.11, 6.119.10, 6.119.9, 6.119.8, 6.119.7, 6.119.6, 6.119.5, 6.119.4, 6.119.3, 6.119.2, 6.119.1, 6.119.0, 6.118.5, 6.118.4, 6.118.3, 6.118.2, 6.118.1, 6.116.1, 6.116.0, 6.115.1, 6.114.2, 6.114.1, 6.114.0, 6.113.0, 6.112.0, 6.113.5, 6.113.3, 6.113.1, 6.110.1, 6.109.0, 6.108.1, 6.106.0, 6.101.1, 6.97.2, 6.105.0, 6.97.1, 6.97.0, 6.96.1, 6.96.0, 6.95.0, 6.94.0, 6.93.0, 6.92.1, 6.92.0, 6.91.1, 6.90.3, 6.91.0, 6.90.2, 6.90.0, 6.87.5, 6.87.4, 6.87.3, 6.87.2, 6.84.0, 6.87.1, 6.83.0, 6.86.1, 6.81.1, 6.76.0, 6.75.0, 6.74.5, 6.74.4, 6.74.1, 6.74.0, 6.73.2, 6.73.1, 6.73.0, 6.72.0, 6.71.2, 6.71.1, 6.71.0, 6.70.0, 6.69.0, 6.68.0, 6.67.0, 6.66.0, 6.65.4, 6.65.3, 6.65.2, 6.65.1, 6.65.0, 6.64.3, 6.64.2, 6.64.1, 6.64.0, 6.63.0, 6.62.0, 6.61.4, 6.61.3, 6.61.1, 6.61.0, 6.60.0, 6.59.0, 6.58.0, 6.57.0, 6.56.0, 6.55.0, 6.54.4, 6.54.2, 6.54.1, 6.54.0, 6.53.4, 6.53.0, 6.51.0), the 5.2.0 through 5.33.0-rc.6 rows, and former `4.0.0` rows are rolled off to respect the P9 changelog cap; their full bodies remain at their git tags.

---

## License

[MIT License](LICENSE)

Created by [Anton Razzhigaev](https://t.me/abstractDL) & Andrew Kaznacheev
