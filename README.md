# 🎙️ AI-TTS-Toolkit

<p align="center">
  <strong>全球开源TTS工具箱 · 一键安装 · 零门槛使用</strong><br>
  <em>15 Text-to-Speech Tools · Cross-Platform · Zero Dependencies · Interactive Installer</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/macOS-✓-black.svg" alt="macOS">
  <img src="https://img.shields.io/badge/Linux-✓-orange.svg" alt="Linux">
  <img src="https://img.shields.io/badge/Windows-✓-cyan.svg" alt="Windows">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Tools-15-purple.svg" alt="Tools">
</p>

---

## ✨ 这是什么？

一个 **纯 Python 脚本**，帮你一键安装全球最好的 15 个开源 TTS（文字转语音）工具。

> **🔒 零门槛承诺：不需要管理员权限、不需要 root、不需要 sudo、不需要任何付费。下载后直接运行。**

### 你能用它做什么？

- 🎬 **视频配音** — 为短视频、影视剧解说生成专业配音
- 📖 **有声书制作** — 批量将小说/文章转为语音
- 🎮 **游戏NPC配音** — 克隆角色声音，生成游戏对话
- 🎙️ **播客制作** — 生成自然口语化的对话语音
- 🎵 **AI翻唱** — 训练歌手音色模型，让AI翻唱歌曲
- 📺 **数字人** — 为虚拟主播/数字人提供语音能力

---

## 🚀 30秒上手

### 第一步：下载

```bash
# 方式一：git clone（推荐）
git clone https://github.com/Drip618/AI-TTS-Toolkit.git
cd AI-TTS-Toolkit

# 方式二：直接下载 ZIP
# 在 GitHub 页面点击绿色 "Code" 按钮 → Download ZIP
# 解压后进入文件夹
```

### 第二步：运行

```bash
# ✅ 推荐（不需要任何权限设置）
python3 tts_toolkit.py

# 或者（如果遇到权限问题，用这个）
python tts_toolkit.py
```

> **⚠️ 权限问题？** 如果提示 `Permission denied`，请用 `python3 tts_toolkit.py` 而不是 `./tts_toolkit.py`。本脚本不需要 `chmod +x`，也不需要 `sudo`。

**就这样！** 脚本会自动：
1. 检测你的系统（Mac / Linux / Windows）
2. 检测你的硬件（Apple Silicon / NVIDIA GPU / CPU）
3. 显示所有可用工具，标注哪些能在你的设备上运行
4. 让你自由勾选要安装的工具
5. 让你选择安装路径
6. 自动安装所有依赖

### 其他用法

```bash
# 查看所有工具列表
python3 tts_toolkit.py --list

# 直接安装指定工具（跳过交互）
python3 tts_toolkit.py --install 1,3,4
```

---

## ❓ 权限问题完全指南

> **99% 的用户不需要看这个部分**，直接 `python3 tts_toolkit.py` 就能运行。
> 如果你遇到了权限问题，看这里：

### macOS 用户

```bash
# 如果 python3 命令不存在：
# 1. 打开 "终端" App（在 应用程序 → 实用工具 里）
# 2. 输入以下命令安装 Python：
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python3

# 然后运行：
cd ~/Downloads/AI-TTS-Toolkit    # 或你解压到的目录
python3 tts_toolkit.py
```

### Windows 用户

```bash
# 如果提示 "python3 不是内部命令"：
# 1. 下载 Python: https://www.python.org/downloads/
# 2. 安装时 ⚠️ 勾选 "Add Python to PATH"
# 3. 打开 PowerShell 或 CMD，运行：

cd $HOME\Downloads\AI-TTS-Toolkit
python tts_toolkit.py
```

### Linux 用户

```bash
# Ubuntu/Debian:
sudo apt install python3 python3-pip git -y

# Fedora:
sudo dnf install python3 python3-pip git -y

# 然后运行：
python3 tts_toolkit.py
```

### 如果 ZIP 下载后无法运行

```bash
# macOS 可能会标记下载文件为"来自未验证开发者"
# 解决方法：在终端中运行（不需要改系统设置）：
xattr -cr ~/Downloads/AI-TTS-Toolkit
python3 ~/Downloads/AI-TTS-Toolkit/tts_toolkit.py
```

---

## 📦 包含的 15 个工具

### ☁️ 云端 API（无需 GPU，最简单）

| # | 工具 | 说明 | 难度 | GPU |
|---|------|------|------|-----|
| 1 | **[Edge-TTS](https://github.com/rany2/edge-tts)** | 微软 Azure 语音引擎，300+ 音色，40+ 语言，完全免费 | ⭐ | ❌ |

> 💡 **新手首选！** 一行 `pip install edge-tts` 就能用，零配置。

### 🤖 开源本地部署

| # | 工具 | 说明 | 难度 | GPU |
|---|------|------|------|-----|
| 2 | **[ChatTTS](https://github.com/2noise/ChatTTS)** | 中文口语化天花板，情感丰富，适合对话/播客 | ⭐⭐ | 可选 |
| 8 | **[Bark](https://github.com/suno-ai/bark)** | Suno 出品，能生成笑声/音乐/环境音，输入 ♪ 自动哼唱 | ⭐⭐ | ✅ |

### 🧬 声音克隆（复制任何人的声音）

| # | 工具 | 说明 | 难度 | GPU |
|---|------|------|------|-----|
| 3 | **[Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)** | 阿里通义 2026 开源，3 秒克隆，**用文字描述创造声音** | ⭐⭐ | ✅ |
| 4 | **[GPT-SoVITS](https://github.com/X-T-E/GPT-SoVITS)** | 国产精品，1-3 分钟训练专属音色，中文克隆效果顶尖 | ⭐⭐⭐ | ✅ |
| 5 | **[IndexTTS2](https://github.com/index-tts/index-tts)** | B 站开源，**情感独立控制**（同一句话切换开心/悲伤/愤怒） | ⭐⭐ | ✅ |
| 6 | **[CosyVoice](https://github.com/FunAudioLLM/CosyVoice)** | 阿里通义，**18 种中文方言**（粤语/四川话/东北话等） | ⭐⭐ | ✅ |
| 7 | **[Fish-Speech](https://github.com/fishaudio/fish-speech)** | 50 种语言，情感标签 `[laugh]` `[whispers]` | ⭐⭐ | ✅ |
| 12 | **[OpenVoice](https://github.com/myshell-ai/OpenVoice)** | MIT 出品，音色+情感+口音三维独立控制 | ⭐⭐ | ✅ |

### 🔧 传统 TTS 引擎

| # | 工具 | 说明 | 难度 | GPU |
|---|------|------|------|-----|
| 9 | **[Mozilla TTS](https://github.com/mozilla/TTS)** | Mozilla 开源，Tacotron2 + WaveRNN 双引擎，40+ 语言 | ⭐⭐ | ✅ |
| 10 | **[Coqui TTS](https://github.com/coqui-ai/TTS)** | 300+ 语言，XTTS v2 多语言克隆，企业级稳定性 | ⭐⭐ | ✅ |
| 11 | **[VITS](https://github.com/jaywalnut310/vits)** | 端到端模型，音质媲美真人，支持多说话人训练 | ⭐⭐⭐ | ✅ |

### ⚡ 实时语音克隆

| # | 工具 | 说明 | 难度 | GPU |
|---|------|------|------|-----|
| 13 | **[Real-Time Voice Cloning](https://github.com/CorentinJ/Real-Time-Voice-Cloning)** | 5 秒录音实时克隆，适合游戏 NPC / 虚拟主播 | ⭐⭐⭐ | ✅ |

### 🏢 企业级

| # | 工具 | 说明 | 难度 | GPU |
|---|------|------|------|-----|
| 14 | **[VALL-E](https://github.com/enhuiz/vall-e)** | Meta 出品，可生成带**环境音效**的语音（教堂回声等） | ⭐⭐⭐⭐ | ✅ 16GB |

### 🎵 歌声转换

| # | 工具 | 说明 | 难度 | GPU |
|---|------|------|------|-----|
| 15 | **[So-VITS-SVC](https://github.com/svc-develop-team/so-vits-svc)** | AI 歌声转换，训练歌手音色，让 AI 翻唱歌曲 | ⭐⭐⭐ | ✅ |

---

## 💻 系统要求

### 最低要求（运行 Edge-TTS）
- Python 3.8+
- 网络连接
- 任何操作系统

### 推荐配置（运行全部工具）
| 组件 | 最低 | 推荐 |
|------|------|------|
| **内存** | 8 GB | 16 GB+ |
| **磁盘** | 10 GB | 50 GB+ |
| **GPU** | 不需要 | NVIDIA 6GB+ 或 Apple Silicon M1+ |

### 平台支持

| 平台 | 状态 | 说明 |
|------|------|------|
| **macOS (Apple Silicon)** | ✅ 完美支持 | M1/M2/M3/M4/M5，MPS Metal 加速 |
| **macOS (Intel)** | ✅ 支持 | CPU 模式运行 |
| **Linux (NVIDIA GPU)** | ✅ 完美支持 | CUDA 加速 |
| **Linux (CPU only)** | ✅ 支持 | 速度较慢 |
| **Windows (WSL)** | ✅ 支持 | 通过 WSL2 运行 |
| **Windows (Git Bash)** | ⚠️ 部分支持 | 原生 Windows 兼容性有限 |

---

## 🛠️ 前置工具

脚本会自动检测，如果缺少会提示安装方法：

| 工具 | 安装方法 |
|------|---------|
| **Python 3.8+** | [python.org](https://www.python.org/downloads/) 或 `brew install python3` |
| **Git** | [git-scm.com](https://git-scm.com/) 或 `brew install git` |
| **Conda**（推荐） | [conda.io](https://docs.conda.io/) 或 `brew install --cask miniconda` |

> 💡 **不需要管理员权限！** 所有工具都安装在用户目录下。

---

## 📖 使用示例

### Edge-TTS 快速配音
```bash
# 安装
pip install edge-tts

# 生成语音
edge-tts --voice zh-CN-XiaoyiNeural --text "大家好，欢迎收听" --write-media hello.mp3

# 调节语速和音调
edge-tts --voice zh-CN-YunyangNeural --rate=-10% --pitch=+5Hz --text "影视解说配音" --write-media demo.mp3
```

### Qwen3-TTS 语音设计
```python
# 用文字描述创造声音（无需参考音频！）
# "温柔的中年女性声音，略带沙哑"
# "低沉的男声，适合纪录片解说"
# "活泼的少女声，适合动画配音"
```

### GPT-SoVITS 声音克隆
```
1. 准备 1-3 分钟清晰人声录音
2. 启动 WebUI: python GPT_SoVITS/inference_webui.py
3. 上传音频 → 训练 → 生成任意文本的语音
```

---

## ❓ 常见问题

<details>
<summary><strong>🔧 遇到权限问题怎么办？</strong></summary>

**请始终使用 `python3 tts_toolkit.py` 运行，不要用 `./tts_toolkit.py`。**

- ❌ `./tts_toolkit.py` → 可能提示 Permission denied
- ✅ `python3 tts_toolkit.py` → 始终可用，无需任何权限设置
- ✅ `python tts_toolkit.py` → Windows 用户用这个

**本脚本不需要：**
- ❌ 不需要 `chmod +x`
- ❌ 不需要 `sudo`
- ❌ 不需要管理员/root 权限
- ❌ 不需要修改系统安全设置（macOS 不需要关 Gatekeeper）

</details>

<details>
<summary><strong>没有 NVIDIA GPU 能用吗？</strong></summary>

能！Edge-TTS 完全不需要 GPU。其他工具可以用 CPU 运行（速度较慢）。
Apple Silicon Mac（M1-M5）使用 Metal 加速，效果接近 NVIDIA GPU。
</details>

<details>
<summary><strong>安装失败怎么办？</strong></summary>

1. 确保已安装 Python 3.8+、Git、Conda
2. 检查网络连接（需要下载模型文件）
3. 查看各工具目录下的 README_灵枢TTS工具箱.txt
4. 在 GitHub Issues 提问
</details>

<details>
<summary><strong>可以只安装部分工具吗？</strong></summary>

当然可以！运行脚本后自由勾选，想装哪个装哪个。
</details>

<details>
<summary><strong>声音克隆合法吗？</strong></summary>

只能克隆自己或已获授权的声音。严禁用于伪造、诈骗等违法用途。
</details>

<details>
<summary><strong>下载 ZIP 后 macOS 提示"已损坏"怎么办？</strong></summary>

这是 macOS 的安全机制。在终端运行：
```bash
xattr -cr ~/Downloads/AI-TTS-Toolkit
```
然后正常 `python3 tts_toolkit.py` 运行即可。不需要改系统设置。
</details>

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 添加新工具
编辑 `tts_toolkit.py` 中的 `TTS_TOOLS` 列表，按照现有格式添加：

```python
{
    'id': 16,
    'name': '工具名称',
    'name_cn': '中文名',
    'category': '分类',
    'tags': ['标签1', '标签2'],
    'desc': 'English description',
    'desc_cn': '中文描述',
    'github': 'https://github.com/...',
    'lang': 'Python',
    'need_gpu': False,
    'need_conda': False,
    'disk_mb': 100,
    'ram_mb': 200,
    'difficulty': '⭐',
    'platforms': ['mac', 'linux', 'windows'],
    'install': ['pip install xxx'],
    'test': 'python -c "..."',
    'note': '使用说明',
},
```

---

## 📄 许可证

[MIT License](LICENSE) — 自由使用、修改、分发。

---

## 🙏 致谢

- 所有开源 TTS 项目的开发者
- [Mozilla TTS](https://github.com/mozilla/TTS) · [Coqui TTS](https://github.com/coqui-ai/TTS)
- [GPT-SoVITS](https://github.com/X-T-E/GPT-SoVITS) · [CosyVoice](https://github.com/FunAudioLLM/CosyVoice)
- [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) · [Fish-Speech](https://github.com/fishaudio/fish-speech)
- [ChatTTS](https://github.com/2noise/ChatTTS) · [Bark](https://github.com/suno-ai/bark)
- [Edge-TTS](https://github.com/rany2/edge-tts) · [OpenVoice](https://github.com/myshell-ai/OpenVoice)
- [VALL-E](https://github.com/enhuiz/vall-e) · [VITS](https://github.com/jaywalnut310/vits)
- [Real-Time Voice Cloning](https://github.com/CorentinJ/Real-Time-Voice-Cloning) · [So-VITS-SVC](https://github.com/svc-develop-team/so-vits-svc)
- [IndexTTS2](https://github.com/index-tts/index-tts)

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Drip618">Drip618</a> · 灵枢AI导演系统
</p>
