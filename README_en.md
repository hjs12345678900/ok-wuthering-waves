<div align="center">
  <h1 align="center">
    <img src="icon.png" width="200" alt="OK-WW logo"/>
    <br/>
    OK-WW macOS (Testing)
  </h1>

  <p>
    An experimental Wuthering Waves automation script for macOS, built with
    <a href="https://github.com/hjs12345678900/ok-script">OK-Script macOS</a>.
  </p>

  <p><i>Unofficial macOS derivative; foreground input only; still under real-device testing</i></p>
</div>

<div align="center">

![Platform](https://img.shields.io/badge/platform-macOS-black?logo=apple)
![Status](https://img.shields.io/badge/status-testing-orange)
[![Original Windows Version](https://img.shields.io/badge/original-Windows-blue)](https://github.com/ok-oldking/ok-wuthering-waves)

</div>

### English README | [中文说明](README.md)

---

## Project Status and Upstream

> [!WARNING]
> This is an unofficial experimental macOS fork of the upstream project. It is not an official macOS release from the upstream author. No double-clickable `.app` or `.dmg` is currently provided.

> [!CAUTION]
> This macOS port was produced primarily through AI-assisted **vibe coding**. It has not received a formal security audit, systematic code review, or complete real-device validation. AI-generated or AI-modified code may contain defects, incorrect assumptions, and unexpected behavior.

| Purpose | Repository |
| --- | --- |
| macOS Wuthering Waves script (this testing fork) | [`hjs12345678900/ok-wuthering-waves`](https://github.com/hjs12345678900/ok-wuthering-waves) |
| Companion macOS automation framework | [`hjs12345678900/ok-script`](https://github.com/hjs12345678900/ok-script) |
| Original Windows Wuthering Waves application and releases | [`ok-oldking/ok-wuthering-waves`](https://github.com/ok-oldking/ok-wuthering-waves) |
| Original Windows/emulator automation framework | [`ok-oldking/ok-script`](https://github.com/ok-oldking/ok-script) |

Windows users should use the original repositories and their Releases. Windows `.exe` files do not run on macOS. This fork currently supports foreground input only; ScreenCaptureKit capture, window detection, and task compatibility remain under active testing.

## Disclaimer and Risk

This software is an unofficial experimental third-party automation tool. It interacts with Wuthering Waves through screen capture and simulated user input. It does not read game memory or modify game files, but that does not guarantee safety, compliance with the game's terms of service, or freedom from detection.

This project is free and open source and is intended only for personal learning, research, and testing. Review the source before use. You assume all risks, including account penalties or bans, unintended actions, loss of game progress or data, exposure caused by system permissions, device or software malfunction, and any other direct or indirect loss.

Kuro Games prohibits unauthorized third-party automation and may penalize accounts that use macro scripts or similar tools.

**To the maximum extent permitted by applicable law, the maintainers and contributors of this fork, the upstream authors, and the relevant AI service providers are not liable for consequences arising from use of or inability to use this software. The software is provided “as is,” without express or implied warranties. By using it, you acknowledge and voluntarily accept all risks.**

## Quick Start

1. Follow [Complete macOS Source Setup](#complete-macos-source-setup) to install Python 3.12, clone both repositories, and grant macOS permissions.
2. Run the permission and capture probes before starting any automation.
3. After a correct game-window snapshot is produced, use `python main_debug.py` for low-risk real-device testing.
4. Do not rely on minimized or background operation.
5. Windows users should download the stable application from the [original OK-WW repository](https://github.com/ok-oldking/ok-wuthering-waves).

## Downloads

- **macOS testing source:** [`hjs12345678900/ok-wuthering-waves`](https://github.com/hjs12345678900/ok-wuthering-waves). Clone it with `--recurse-submodules`.
- **Original Windows releases:** [`ok-oldking/ok-wuthering-waves`](https://github.com/ok-oldking/ok-wuthering-waves/releases).
- **macOS `.app` / `.dmg`:** not available yet.

## Current macOS Capabilities

- **Window capture:** uses ScreenCaptureKit to capture the native Wuthering Waves window; compatibility is still being tested.
- **Foreground input:** uses Quartz to simulate keyboard and mouse input; the game must remain in the foreground.
- **Upstream tasks and recognition:** character detection, daily tasks, materials, and Echo workflows are inherited from upstream, but not every task has completed macOS real-device validation.
- **Resolution adaptation:** inherits upstream 16:9 scaling; ultrawide displays and non-default scaling require separate validation.

## Troubleshooting

1. **Permissions:** enable “Screen & System Audio Recording” and “Accessibility” for the Terminal that launches the app. Quit Terminal completely with `Command + Q`, then reopen it.
2. **Environment:** activate the project `.venv` and verify that `python -c "import ok; print(ok.__file__)"` points to the sibling `ok-script/ok` directory.
3. **Submodules:** run `git submodule update --init --recursive`.
4. **Game window:** launch the native Wuthering Waves client first, keep it in the foreground, and do not minimize it.
5. **Capture:** produce a snapshot with `scripts/macos_probe.py` before running tasks.
6. **Input:** synchronize any custom in-game key bindings and begin with low-risk actions.
7. **Bug reports:** include reproduction steps, macOS version, Mac model/chip, terminal output, and `logs/ok-ww_error.log`. Never publish account or personal information.

## Complete macOS Source Setup

### Requirements

- macOS 12 or later
- Apple Silicon Mac
- Native Wuthering Waves client
- Python 3.12
- Git
- Xcode Command Line Tools

If [Homebrew](https://brew.sh/) is installed:

```bash
xcode-select --install
brew install python@3.12 git
```

### First Installation

Clone both repositories into the same parent directory:

```bash
# 1. Clone the macOS backend and game script
git clone https://github.com/hjs12345678900/ok-script.git
git clone --recurse-submodules https://github.com/hjs12345678900/ok-wuthering-waves.git

# 2. Create and activate the project environment
cd ok-wuthering-waves
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies and the companion macOS backend
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e ../ok-script

# 4. Start the application
python main.py
```

If the repository was cloned without `--recurse-submodules`:

```bash
git submodule update --init --recursive
```

### Later Launches

```bash
cd ok-wuthering-waves
source .venv/bin/activate
python main.py
```

### Permissions and Capture Probe

Grant the launching Terminal:

- Screen & System Audio Recording
- Accessibility

Quit and reopen Terminal after changing permissions. Start Wuthering Waves and keep it in the foreground, then run:

```bash
source .venv/bin/activate
python scripts/macos_probe.py --prompt-permissions
python scripts/macos_probe.py --snapshot /tmp/ok-ww-macos.png
open /tmp/ok-ww-macos.png
```

If the snapshot is correct, start the debug build:

```bash
python main_debug.py
```

## Development Workflow

Keep the original repository configured as `upstream` and work on a dedicated feature branch:

```bash
git remote add upstream https://github.com/ok-oldking/ok-wuthering-waves.git
git fetch upstream
git switch -c feature/your-change
```

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

On macOS, run each `Test*.py` file in a separate process to avoid shared-executor shutdown cascades:

```bash
for test_file in tests/Test*.py; do
  PYTHONPATH=../ok-script python -m unittest "$test_file" || exit 1
done
```

Windows developers can use:

```powershell
.\run_tests.ps1
```

After testing:

```bash
git status
git add path/to/changed-file
git commit -m "Describe the change"
```

Pull requests should describe the goal, macOS test environment, test results, and known limitations. Do not commit virtual environments, caches, logs, screenshots, personal configuration, or account information. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for additional upstream-oriented contribution guidance.

## Command-Line Arguments

```bash
# Run the first task and exit when it completes
python main.py -t 1 -e
```

- `-t` or `--task`: run the Nth task after launch.
- `-e` or `--exit`: exit after the selected task completes.

## Acknowledgements

- [lazydog28/mc_auto_boss](https://github.com/lazydog28/mc_auto_boss)
- [ok-oldking/OnnxOCR](https://github.com/ok-oldking/OnnxOCR)
- [zhiyiYo/PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
- [Toufool/AutoSplit](https://github.com/Toufool/AutoSplit)

## License and Derivative Work

This project remains licensed under the upstream [GNU AGPL-3.0](LICENSE.txt). The license permits use, modification, forking, and redistribution, but derivative versions must retain the license and copyright notices, identify their changes, and provide the corresponding source code as required by AGPL-3.0. Refer to `LICENSE.txt` for the controlling terms.
