<div align="center">
  <h1 align="center">
    <img src="icon.png" width="200" alt="ok-ww logo"/>
    <br/>
    OK-WW macOS（测试中）
  </h1> 
  
  <p>
    一个处于实机测试阶段的《鸣潮》macOS 自动化脚本，基于实验性 <a href="https://github.com/hjs12345678900/ok-script">OK-Script macOS</a> 开发。
    <br />
    An experimental Wuthering Waves automation script for macOS, developed with <a href="https://github.com/hjs12345678900/ok-script">OK-Script macOS</a>.
  </p>
  
  <p><i>非官方 macOS 派生版本；仅支持前台输入，仍在测试中</i></p>
</div>

<!-- Badges -->
<div align="center">
  
![平台](https://img.shields.io/badge/platform-macOS-black?logo=apple)
![状态](https://img.shields.io/badge/status-testing-orange)
[![原版 Windows](https://img.shields.io/badge/original-Windows-blue)](https://github.com/ok-oldking/ok-wuthering-waves)
[![Discord](https://img.shields.io/discord/296598043787132928?color=5865f2&label=%20Discord)](https://discord.gg/vVyCatEBgA)

</div>

### [English README](README_en.md) | 中文说明

---

## 🍎 项目定位与上游

> [!WARNING]
> 这是基于原项目修改的非官方 macOS 测试分支，并非原作者发布的正式 macOS 版本。目前没有可双击安装的 `.app` 或 `.dmg`，请仅用于开发和低风险实机验证。

> [!CAUTION]
> 本 macOS 移植主要由 AI 辅助的 **vibe coding** 完成，尚未经过正式安全审计、系统化代码审查或完整实机验证。AI 生成或修改的代码可能包含缺陷、错误假设和不可预期行为。

| 用途 | 项目 |
| --- | --- |
| macOS《鸣潮》脚本（本测试分支） | [`hjs12345678900/ok-wuthering-waves`](https://github.com/hjs12345678900/ok-wuthering-waves) |
| 配套 macOS 自动化框架 | [`hjs12345678900/ok-script`](https://github.com/hjs12345678900/ok-script) |
| 原版 Windows《鸣潮》脚本与安装包 | [`ok-oldking/ok-wuthering-waves`](https://github.com/ok-oldking/ok-wuthering-waves) |
| 原版 Windows / 模拟器自动化框架 | [`ok-oldking/ok-script`](https://github.com/ok-oldking/ok-script) |

Windows 用户应使用上表中的原版 Windows 仓库及其 Releases；其中的 `.exe` 不能在 macOS 上运行。本分支当前仅支持游戏位于前台时的输入，ScreenCaptureKit 捕获、窗口识别和任务兼容性仍在持续测试。

## ⚠️ 免责声明

本软件是未经官方认可的实验性第三方自动化工具，通过屏幕捕获和模拟用户输入与《鸣潮》交互。它不读取游戏内存，也不修改游戏文件，但这不代表其使用一定安全、符合游戏服务条款或不会触发检测。

本项目开源、免费，仅供个人学习、研究与测试。使用者应自行审查代码，并自行承担包括但不限于账号处罚或封禁、误操作、游戏进度或数据损失、系统权限暴露、设备或软件异常以及其他直接或间接损失的全部风险。

请注意，根据库洛官方的《鸣潮》公平运营声明：
> 严禁利用任何第三方工具破坏游戏体验。
> 我们将严厉打击使用外挂、加速器、作弊软件、宏脚本等违规工具的行为，这些行为包括但不限于自动挂机、技能加速、无敌模式、瞬移、修改游戏数据等操作。
> 一经查证，我们将视违规情况和次数，采取包括但不限于扣除违规收益、冻结或永久封禁游戏账号等措施。

**在适用法律允许的最大范围内，本 fork 的维护者、贡献者、上游作者及相关 AI 服务提供方不对使用或无法使用本软件造成的任何后果负责。本软件按“原样”提供，不作任何明示或默示保证。使用本软件即表示您已理解并自愿承担全部风险。**

## 🚀 快速开始

1. macOS 用户请按照下方的[“macOS 源码测试版（完整安装步骤）”](#macos-源码测试版完整安装步骤)配置 Python 3.12、两个相邻仓库和系统权限。
2. 首次自动化前，先运行权限探针并确认能够正确保存游戏窗口截图。
3. 截图通过后使用 `python main_debug.py` 做低风险实机测试；暂时不要依赖后台或最小化运行。
4. Windows 用户请前往[原版 OK-WW](https://github.com/ok-oldking/ok-wuthering-waves)下载正式安装包。

## 📥 下载渠道

- **macOS 测试源码**：[`hjs12345678900/ok-wuthering-waves`](https://github.com/hjs12345678900/ok-wuthering-waves)。请使用 `git clone --recurse-submodules`，不要把 Windows `.exe` 当作 macOS 安装包。
- **Windows 正式版及 Releases**：[`ok-oldking/ok-wuthering-waves`](https://github.com/ok-oldking/ok-wuthering-waves/releases)。
- macOS `.app` / `.dmg`：**尚未提供**。

## ✨ 主要功能

- **macOS 窗口捕获**：使用 ScreenCaptureKit 捕获原生《鸣潮》窗口，目前仍在实机兼容性测试。
- **前台键鼠输入**：使用 Quartz 模拟输入，游戏必须位于前台。
- **继承原版任务与识别逻辑**：角色识别、日常、材料、声骸等功能来自原版项目，但并非所有任务都已完成 macOS 实机验证。
- **分辨率适配**：沿用原版的 16:9 分辨率适配；超宽屏和不同缩放比例需要单独验证。

## 🔧 疑难解答 (Troubleshooting)

如果遇到问题，请在提问前按以下步骤逐一排查：

1. **权限**：为启动程序的 Terminal 开启“屏幕与系统音频录制”和“辅助功能”，然后使用 `Command + Q` 完全退出并重开 Terminal。
2. **环境**：确认已激活项目 `.venv`，并且 `python -c "import ok; print(ok.__file__)"` 指向相邻的 `ok-script/ok`。
3. **子模块**：确认已经执行 `git submodule update --init --recursive`。
4. **窗口**：先打开原生《鸣潮》客户端并保持在前台，不要最小化。
5. **捕获**：先运行 `scripts/macos_probe.py --snapshot /tmp/ok-ww-macos.png`，确认截图正确后再启动任务。
6. **输入**：同步游戏内自定义按键；首次只测试低风险操作。
7. **日志**：报告问题时附上复现步骤、macOS/芯片型号、终端输出以及 `logs/ok-ww_error.log`，但不要公开账号或个人信息。
9.  **关闭自动奔跑**：游戏设置里关闭自动奔跑。

---

## 💻 开发者专区

### 普通用户安装（Windows）

普通用户建议直接从[官方 Releases](https://github.com/ok-oldking/ok-wuthering-waves/releases)下载最新的 `setup.exe`，不要下载 GitHub 自动生成的 Source Code 压缩包。安装完成后从桌面快捷方式或开始菜单启动。

### macOS 源码测试版（完整安装步骤）

> [!IMPORTANT]
> macOS 版目前是实验性源码测试版，还没有可双击安装的 `.app` 或 `.dmg`。Windows Releases 中的 `.exe` 不能在 Mac 上运行。测试者需要按下面的步骤配置一次 Python 环境。

系统要求：macOS 12 或更高版本、Apple Silicon Mac、原生《鸣潮》客户端、Python 3.12、Git，以及 Xcode Command Line Tools。

如果已经安装 [Homebrew](https://brew.sh/)，可以先执行：

```bash
xcode-select --install
brew install python@3.12 git
```

首次安装时，依次复制执行下面的全部命令。两个仓库必须放在同一个父目录：

```bash
# 1. 下载 macOS 后端和鸣潮项目
git clone https://github.com/hjs12345678900/ok-script.git
git clone --recurse-submodules https://github.com/hjs12345678900/ok-wuthering-waves.git

# 2. 进入鸣潮项目并创建独立 Python 环境
cd ok-wuthering-waves
python3.12 -m venv .venv
source .venv/bin/activate

# 3. 安装项目依赖和配套的 macOS 后端
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e ../ok-script

# 4. 启动
python main.py
```

如果此前下载项目时没有使用 `--recurse-submodules`，请在项目目录补充执行：

```bash
git submodule update --init --recursive
```

以后每次启动只需要：

```bash
cd ok-wuthering-waves
source .venv/bin/activate
python main.py
```

首次运行时，在“系统设置 → 隐私与安全性”中，为启动程序的终端开启以下权限：

- “屏幕与系统音频录制”
- “辅助功能”

授权后请完全退出并重新打开终端。打开《鸣潮》并保持游戏在前台，然后先检查权限和截图：

```bash
source .venv/bin/activate
python scripts/macos_probe.py --prompt-permissions
python scripts/macos_probe.py --snapshot /tmp/ok-ww-macos.png
open /tmp/ok-ww-macos.png
```

截图正确后，可以使用 Debug 版本进行低风险实机测试：

```bash
python main_debug.py
```

macOS 输入目前只在游戏位于前台时发送，不承诺最小化或后台运行。详细设计与已知限制见 [`docs/macos-port-plan.md`](docs/macos-port-plan.md) 和 [`docs/macos-pitfalls-2026-07-25.md`](docs/macos-pitfalls-2026-07-25.md)。

### 从源码运行（Windows / 开发者）

推荐使用 **Python 3.12**：

```bash
git clone --recurse-submodules https://github.com/hjs12345678900/ok-wuthering-waves.git
cd ok-wuthering-waves
python3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

#### 开发验证

Windows 可以使用原项目提供的测试脚本：

```powershell
.\run_tests.ps1
```

macOS 上应让每个 `Test*.py` 在独立进程中运行，避免共享执行器退出造成连锁误报：

```bash
python -m pip install -r requirements-dev.txt
for test_file in tests/Test*.py; do
  PYTHONPATH=../ok-script python -m unittest "$test_file" || exit 1
done
```

#### 标准开发与提交流程

保留原项目为 `upstream`，所有修改在独立分支完成：

```bash
git remote add upstream https://github.com/ok-oldking/ok-wuthering-waves.git
git fetch upstream
git switch -c feature/your-change

# 修改并完成相关测试后
git status
git add path/to/changed-file
git commit -m "Describe the change"
```

提交 PR 时请说明修改目的、macOS 实机环境、测试结果和已知限制。不要提交 `.venv`、缓存、日志、截图、个人配置或游戏账号信息。更完整的贡献要求见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

### 命令行参数

您可以通过命令行参数实现自动化启动。

```bash
# 示例：启动后自动执行第一个任务（一条龙），并在任务完成后退出程序
python main.py -t 1 -e
```

*   `-t` 或 `--task`: 启动后自动执行第 N 个任务。`1` 代表任务列表中的第一个。
*   `-e` 或 `--exit`: 任务执行完毕后自动退出程序。

## 🔗 使用ok-script的项目：

* 鸣潮 [https://github.com/ok-oldking/ok-wuthering-wave](https://github.com/ok-oldking/ok-wuthering-waves)
* 原神(停止维护,
  但是后台过剧情可用) [https://github.com/ok-oldking/ok-genshin-impact](https://github.com/ok-oldking/ok-genshin-impact)
* 少前2 [https://github.com/ok-oldking/ok-gf2](https://github.com/ok-oldking/ok-gf2)
* 星铁 [https://github.com/Shasnow/ok-starrailassistant](https://github.com/Shasnow/ok-starrailassistant)
* 星痕共鸣 [https://github.com/Sanheiii/ok-star-resonance](https://github.com/Sanheiii/ok-star-resonance)
* 二重螺旋 [https://github.com/BnanZ0/ok-duet-night-abyss](https://github.com/BnanZ0/ok-duet-night-abyss)
* 白荆回廊(停止更新) [https://github.com/ok-oldking/ok-baijing](https://github.com/ok-oldking/ok-baijing)


## ❤️ 致谢
*   [lazydog28/mc_auto_boss](https://github.com/lazydog28/mc_auto_boss)
*   [ok-oldking/OnnxOCR](https://github.com/ok-oldking/OnnxOCR)
*   [zhiyiYo/PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
*   [Toufool/AutoSplit](https://github.com/Toufool/AutoSplit)

## 📄 许可证与派生开发

本项目沿用原项目的 [GNU AGPL-3.0](LICENSE.txt) 许可证。许可证允许使用、修改、fork 和再发布，因此可以进行派生开发；但派生版本需要保留许可证和版权声明、明确说明修改，并按 AGPL-3.0 要求向使用者提供对应源代码。具体权利与义务以 `LICENSE.txt` 原文为准。
