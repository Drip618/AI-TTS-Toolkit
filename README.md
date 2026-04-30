# 🎙️ AI-TTS-Studio v3.3

<p align="center">
  <strong>全球TTS一体化工作台 · WebUI · 开箱即用</strong><br>
  <em>打字即出语音 · 声音克隆 · 语音识别 · 模型热切换</em>
</p>

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 🎤 **文字转语音** | 输入文字 → 一键生成语音，支持 48 个精选音色 |
| 🎛️ **语速/音调** | 滑块调节，实时预览，自动适配各引擎格式 |
| 📂 **文件解析** | 支持 txt / pdf / docx / srt / vtt / ass |
| 🎬 **视频转音频** | 上传视频 → 提取音频 → 语音识别 |
| 🎙️ **声音克隆** | 上传音频 → 克隆音色 → 用新音色生成语音 |
| 👂 **语音识别** | 多引擎自动切换（faster-whisper / vosk） |
| 🔄 **模型热切换** | UI 内一键切换引擎，自动启动/关闭，进度条显示 |
| 💾 **智能保存** | 生成到临时目录，用户确认后才保存到输出文件夹 |
| 🌐 **代理支持** | 自动检测系统代理，支持 HTTP/SOCKS5 |
| 🔍 **本地模型扫描** | 自动发现本地已安装的 TTS 模型并加载 |

---

## 🚀 30秒上手

### 第一步：安装

```bash
# 打开终端，进入项目目录
cd AI-TTS-Toolkit

# 一键安装所有依赖
chmod +x install.sh
./install.sh
```

安装脚本会自动处理：
- ✅ Homebrew（如未安装）
- ✅ Python 3
- ✅ edge-tts（核心语音引擎）
- ✅ python-docx / pymupdf（文件解析）
- ✅ httpx[socks] / certifi（代理支持）
- ✅ ffmpeg（音频/视频处理）

### 第二步：启动

```bash
# 一键启动
chmod +x start.sh
./start.sh

# 或直接运行
python3 web.py
```

### 第三步：使用

浏览器打开 **http://localhost:7860** ，开始使用！

---

## 📁 文件说明

```
AI-TTS-Toolkit/
├── web.py              # 主程序（WebUI，纯 Python，零框架依赖）
├── install.sh          # 一键安装脚本
├── start.sh            # 一键启动脚本
├── requirements.txt    # Python 依赖列表
├── tts_toolkit.py      # CLI 工具箱（可选）
├── README.md           # 本文件
├── LICENSE             # MIT 许可证
├── .config/            # 用户配置（自动创建）
├── .temp/              # 临时生成文件（自动清理）
├── .logs/              # 日志文件
├── .uploads/           # 上传文件
├── models/             # 本地 TTS 模型（自动扫描）
└── ~/Downloads/最终输出/音频文件/  # 用户保存的音频
```

---

## 🎤 支持的语音（48个精选）

### 中文
| 音色 | 说明 |
|------|------|
| 晓伊 (XiaoyiNeural) | 女声，温柔亲切 |
| 晓辰 (XiaochenNeural) | 女声，活泼开朗 |
| 晓涵 (XiaohanNeural) | 女声，知性大方 |
| 晓梦 (XiaomengNeural) | 女声，甜美可爱 |
| 晓秋 (XiaoqiuNeural) | 女声，成熟稳重 |
| 晓瑞 (XiaoruiNeural) | 女声，专业播报 |
| 晓思 (XiaosuNeural) | 女声，清新自然 |
| 晓颜 (XiaoyanNeural) | 女声，优雅知性 |
| 晓悠 (XiaoyouNeural) | 女声，轻松随意 |
| 云枫 (YunfengNeural) | 男声，成熟磁性 |
| 云皓 (YunhaoNeural) | 男声，阳光少年 |
| 云健 (YunjianNeural) | 男声，专业新闻 |
| 云夏 (YunxiaNeural) | 男声，年轻活力 |
| 云扬 (YunyangNeural) | 男声，纪录片风 |
| 云野 (YunyeNeural) | 男声，沉稳大气 |
| 云泽 (YunzeNeural) | 男声，温暖亲切 |

### 英文 / 日文 / 韩文 / 粤语等
更多音色请查看 WebUI 中的语音列表。

---

## 🔧 可选安装（语音识别）

```bash
# 在线识别（推荐，更准确）
pip3 install faster-whisper --break-system-packages

# 离线识别（无需网络，轻量）
pip3 install vosk --break-system-packages
```

---

## 🤖 本地模型支持

将 TTS 模型放在项目 `models/` 目录下，WebUI 会自动扫描并加载。

支持通过 API 接口对接的模型：
- GPT-SoVITS
- ChatTTS
- CosyVoice
- Fish-Speech
- 其他提供 HTTP API 的 TTS 模型

---

## ❓ 常见问题

<details>
<summary><strong>macOS 提示"已损坏"怎么办？</strong></summary>

```bash
xattr -cr ~/Downloads/AI-TTS-Toolkit
```
</details>

<details>
<summary><strong>pip 安装报错 PEP 668？</strong></summary>

install.sh 已自动处理。手动安装时加 `--break-system-packages`：
```bash
pip3 install edge-tts --break-system-packages
```
</details>

<details>
<summary><strong>edge-tts 负数语速报错？</strong></summary>

v3.3 已修复。使用 `--rate=-10%` 格式（等号连接），不再使用空格。
</details>

<details>
<summary><strong>如何使用本地模型？</strong></summary>

1. 将模型文件夹放入 `models/` 目录
2. 确保 `model_info.json` 包含 API 端口和启动命令
3. 在 WebUI 引擎列表中选择对应模型
4. 系统会自动启动 API 服务
</details>

---

## 📄 许可证

[MIT License](LICENSE) — 自由使用、修改、分发。

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Drip618">Drip618</a> · 灵枢AI导演系统
</p>
