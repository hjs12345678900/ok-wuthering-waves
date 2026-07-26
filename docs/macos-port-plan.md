# OK-WW macOS 原生版移植方案

状态：前台 MVP 后端已落地，等待有《鸣潮》Mac 客户端和权限的机器做实机验收
基线日期：2026-07-25
上游基线：

- `ok-script`：`d2d2b7de463bfca29d924bb35e6364132d031b64`（2026-07-24）
- `ok-wuthering-waves`：`ce17834066408cbd80eca5da8cf1290b36ceeab9`（2026-07-24）

## 1. 经核查后的结论

移植到 Mac 原生版《鸣潮》是可行的，但 Windows 后端不能直接复用。正确边界是：

> 保留任务状态机、模板匹配、OCR 后处理和大部分 GUI；为 `ok-script` 增加 macOS 窗口、捕获、权限及前台输入后端。

《鸣潮》App Store 页面明确列出 Mac 版本，要求 macOS 12.0 及 Apple M1 或更新芯片，因此本方案直接控制原生客户端，不涉及 Wine/CrossOver。

原分析的主结论成立，但有三项需要更精确：

1. “可复用约 80%”只能作为规划假设，必须等低风险任务与战斗任务回归后再给出实测比例。
2. ScreenCaptureKit 可对独立窗口建立内容过滤器，但不等于游戏在最小化、其他 Space 或显示器休眠时仍持续渲染；这些状态必须逐项实测。
3. Quartz `CGEvent` 是系统输入事件，不是 macOS 版 `PostMessage`。MVP 只承诺激活游戏后的前台输入，不承诺定向后台输入。

## 2. 现有阻塞点

原框架存在以下 Windows 绑定：

- `ok.util.window` 顶层导入 `win32api`、`win32gui`、`win32process` 并加载 `user32`；
- 捕获包初始化时无条件导入 WGC、BitBlt、DXGI；
- 输入包初始化时无条件导入 `win32con`、`pydirectinput` 和 PostMessage 实现；
- `DeviceManager` 把 PC 游戏等同于 Windows 设备；
- 单实例、启动、管理员检测、阻止休眠和依赖声明均以 Windows 为默认；
- OK-WW 配置写死 Windows 可执行文件、`UnrealWindow`、PostMessage、WGC 和 BitBlt；
- OCR 配置无条件启用 OpenVINO/NPU。

## 3. MVP 架构

```text
OK-WW task / scene / OCR / template matching
                    │
              ok-script API
         next_frame / click / send_key
                    │
       ┌────────────┴────────────┐
       │                         │
MacScreenCaptureMethod   MacForegroundInteraction
       │                         │
       └────────────┬────────────┘
                    │
          native_helper.swift
      ┌─────────────┼──────────────┐
      │             │              │
SCShareableContent  SCStream   Quartz CGEvent
SCWindow/filter     BGRA流      前台键鼠事件
```

采用小型 Swift 辅助程序，原因是它能直接管理 ScreenCaptureKit 异步流、`CMSampleBuffer` 生命周期和系统权限。Python 与辅助程序之间使用定长帧头加 BGRA 像素流；Python 保留最新帧并转换为 NumPy BGR。

辅助程序源码随 Python 包分发，开发模式下首次使用 `swiftc` 编译。正式打包时应预编译、签名，并通过 `OK_MACOS_HELPER` 指定已签名可执行文件，避免终端与临时二进制分别出现在隐私权限列表。

## 4. Retina 坐标约定

所有层必须明确单位：

- `SCWindow.frame`：全局屏幕空间中的 point；
- ScreenCaptureKit 帧：pixel；
- OpenCV/模板坐标：frame pixel；
- Quartz 鼠标事件：全局 point。

点击换算：

```text
global_point_x = window_point_x + frame_x × window_point_width / frame_pixel_width
global_point_y = window_point_y + frame_y × window_point_height / frame_pixel_height
```

不得把 `backingScaleFactor` 固定写成 2；跨显示器、缩放显示模式和未来硬件都需要使用实际窗口与帧尺寸求比例。

## 5. 权限与安全边界

首次运行需要：

- “屏幕与系统音频录制”：窗口枚举、截图和连续抓帧；
- “辅助功能”：合成键盘和鼠标事件。

辅助程序提供权限预检和可选系统提示。用户授权后通常需要重启终端或打包后的应用。

当前实现坚持以下边界：

- 游戏不在前台时跳过自动输入；
- 不尝试绕过 macOS TCC；
- 不声称支持最小化挂机；
- 不访问游戏内存，不注入游戏进程；
- 保留项目原有的封号风险警告。

## 6. 分阶段验收

### 阶段 A：技术探针

运行：

```bash
python scripts/macos_probe.py --prompt-permissions
python scripts/macos_probe.py --snapshot /tmp/ok-ww-macos.png
python scripts/macos_probe.py --key f2
```

通过条件：

- 权限状态准确；
- 能识别游戏的 `SCWindow`、PID、Bundle ID 和 point 几何；
- PNG 内容正确，无黑帧、裁边或色序错误；
- 前台游戏能收到一个无害按键；
- 指定相对 point 后点击位置正确。

### 阶段 B：框架接入

通过条件：

- macOS 导入链不再加载 pywin32/WinDLL；
- Debug 页面连续显示 ScreenCaptureKit 画面；
- 捕获帧为 BGR NumPy 数组；
- Retina 与非整数缩放显示器上点击误差不超过 1 个逻辑 point；
- 游戏失焦时输入被拒绝，重新激活后恢复。

### 阶段 C：低风险任务

依次验证：

1. 登录画面和主界面识别；
2. 手册、背包、奖励和菜单导航；
3. 月卡与签到检测；
4. 短流程日常任务。

每项记录成功率、平均帧率、捕获延迟、误点击次数和 OCR 耗时。

### 阶段 D：连续输入和战斗

重点验证：

- `key_down` / `key_up` 配对；
- 角色切换、技能、闪避和连续移动；
- 相对视角移动是否需要独立的 mouse-delta 后端；
- 60/120 Hz 游戏帧率下 30 fps 自动化捕获是否足够；
- App Store 版客户端是否过滤合成输入。

### 阶段 E：后台能力实验

抓帧和输入分别记录结果：

| 状态 | 抓帧 | 输入 | 是否继续渲染 |
| --- | --- | --- | --- |
| 工具窗口覆盖 | 待测 | 待测 | 待测 |
| 其他窗口部分遮挡 | 待测 | 不承诺 | 待测 |
| 游戏失焦 | 待测 | MVP 禁止 | 待测 |
| 其他 Space | 待测 | 不承诺 | 待测 |
| 最小化 | 待测 | 不承诺 | 待测 |
| 显示器休眠 | 不作为支持目标 | 不支持 | 不承诺 |

只有实测证据充分时才升级产品承诺。

## 7. OCR 与 Apple Silicon

macOS 默认关闭 OpenVINO/NPU 参数，沿用 `onnxocr` CPU 路径。验收时记录：

- 模型能否在 arm64 Python 环境安装；
- 首次初始化时间和单次 OCR 延迟；
- 是否存在 x86_64-only wheel；
- RapidOCR/ONNX Runtime 是否比当前包更易部署。

Core ML OCR 不是 MVP 必需项；只有 CPU OCR 成为明确瓶颈时再投入。

## 8. 打包与维护

正式发布前还需要：

- 将 Swift helper 作为 arm64（必要时 universal2）构建产物；
- 对主应用和 helper 使用一致的 Developer ID 签名；
- 配置 hardened runtime、notarization 与隐私用途说明；
- 将 macOS 修改保持在独立平台目录；
- 为 Windows 导入与现有捕获方式保留回归测试；
- 定期 rebase 上游，避免在任务层形成平台分叉。

## 9. 当前完成度与未验证项

已完成：

- Windows/macOS 原生模块条件导入；
- ScreenCaptureKit 窗口枚举、单帧 PNG 和连续 BGRA 流；
- NumPy BGR 捕获后端；
- 前台激活、键盘、鼠标、滚轮和拖动；
- Retina frame-pixel → global-point 换算；
- 权限探针；
- OK-WW macOS 配置与 OCR 参数分流；
- Windows-only 依赖标记。

当前开发机未安装《鸣潮》，且 Screen Recording/Accessibility 均未授权。因此完成的是“可编译、可测试的后端 MVP”，不是“已证明全部任务能在真机完成”。下一道门槛是阶段 A 的实机验收。

自动化测试已覆盖窗口选择、Retina 坐标换算、BGRA 行填充处理、前台输入保护和现有可移植测试。Qt 的 `offscreen` 平台并不提供真实 `NSView`，`qframelesswindow` 在该模式下会崩溃，因此本轮没有把 offscreen GUI 启动当作 macOS 原生 GUI 的有效验收；GUI 仍需在正常登录会话中人工启动并观察。

## 10. 主要依据

- Apple：ScreenCaptureKit 可枚举并过滤单个 `SCWindow`，并以 `SCStream` 提供帧流：
  <https://developer.apple.com/documentation/screencapturekit/capturing-screen-content-in-macos>
- Apple：`SCScreenshotManager.captureImage` 可用内容过滤器抓取单帧：
  <https://developer.apple.com/documentation/screencapturekit/scscreenshotmanager/captureimage(contentfilter:configuration:)>
- Apple：Quartz Event Services 提供合成并投递系统键鼠事件的 API：
  <https://developer.apple.com/documentation/coregraphics/quartz-event-services>
- Apple：屏幕录制权限说明：
  <https://support.apple.com/guide/mac-help/control-access-screen-system-audio-recording-mchld6aa7d23/mac>
- Apple：辅助功能控制权限说明：
  <https://support.apple.com/guide/mac-help/allow-accessibility-apps-to-access-your-mac-mh43185/mac>
- App Store：《鸣潮》列出 Mac、macOS 12.0+、Apple M1+：
  <https://apps.apple.com/us/app/wuthering-waves/id6475033368?platform=mac>
