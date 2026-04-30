#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  🎙️ AI-TTS-Studio 一键安装脚本
#  适用于 macOS (Apple Silicon / Intel)
#  用法: chmod +x install.sh && ./install.sh
# ═══════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     🎙️  AI-TTS-Studio  一键安装  🎙️                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ═══════════════════════════════════════════════════════════════
#  1. 检测并安装 Homebrew
# ═══════════════════════════════════════════════════════════════
echo -e "${CYAN}[1/6] 检查 Homebrew...${NC}"
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}  Homebrew 未安装，正在安装...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo -e "${GREEN}  ✅ Homebrew 已安装${NC}"
fi

# ═══════════════════════════════════════════════════════════════
#  2. 检测并安装 Python 3
# ═══════════════════════════════════════════════════════════════
echo -e "${CYAN}[2/6] 检查 Python 3...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}  正在安装 Python...${NC}"
    brew install python
else
    PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}  ✅ Python ${PY_VER} 已安装${NC}"
fi

# ═══════════════════════════════════════════════════════════════
#  3. 安装 Edge-TTS（核心引擎，必须）
# ═══════════════════════════════════════════════════════════════
echo -e "${CYAN}[3/6] 安装 Edge-TTS...${NC}"
if command -v edge-tts &> /dev/null; then
    echo -e "${GREEN}  ✅ Edge-TTS 已安装${NC}"
else
    pip3 install edge-tts --break-system-packages 2>/dev/null || \
    pip3 install edge-tts
    echo -e "${GREEN}  ✅ Edge-TTS 安装完成${NC}"
fi

# ═══════════════════════════════════════════════════════════════
#  4. 安装 Python 依赖（文件解析 + 语音识别 + 代理支持）
# ═══════════════════════════════════════════════════════════════
echo -e "${CYAN}[4/6] 安装 Python 依赖...${NC}"
# 使用 requirements.txt（与本脚本同目录）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip3 install -r "$SCRIPT_DIR/requirements.txt" --break-system-packages 2>/dev/null || \
    pip3 install -r "$SCRIPT_DIR/requirements.txt"
    echo -e "${GREEN}  ✅ Python 依赖安装完成${NC}"
else
    # 手动安装核心依赖
    echo -e "${YELLOW}  未找到 requirements.txt，手动安装核心依赖...${NC}"
    pip3 install python-docx pymupdf 'httpx[socks]' certifi --break-system-packages 2>/dev/null || \
    pip3 install python-docx pymupdf 'httpx[socks]' certifi
    echo -e "${GREEN}  ✅ 核心依赖安装完成${NC}"
fi

# ═══════════════════════════════════════════════════════════════
#  5. 检测并安装 ffmpeg（音频/视频处理）
# ═══════════════════════════════════════════════════════════════
echo -e "${CYAN}[5/6] 检查 ffmpeg...${NC}"
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}  ✅ ffmpeg 已安装${NC}"
else
    echo -e "${YELLOW}  正在安装 ffmpeg...${NC}"
    brew install ffmpeg
    echo -e "${GREEN}  ✅ ffmpeg 安装完成${NC}"
fi

# ═══════════════════════════════════════════════════════════════
#  6. 创建输出目录
# ═══════════════════════════════════════════════════════════════
echo -e "${CYAN}[6/6] 创建目录结构...${NC}"
mkdir -p "$SCRIPT_DIR/models"
mkdir -p "$SCRIPT_DIR/output"
mkdir -p "$SCRIPT_DIR/.temp"
mkdir -p "$SCRIPT_DIR/.logs"
echo -e "${GREEN}  ✅ 目录结构创建完成${NC}"
echo -e "${GREEN}     models/  → TTS 模型存放${NC}"
echo -e "${GREEN}     output/  → 生成的音频输出${NC}"

# ═══════════════════════════════════════════════════════════════
#  完成
# ═══════════════════════════════════════════════════════════════
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     ✅ 安装完成！                                        ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║  启动方式:                                               ║"
echo "║    ./start.sh                                            ║"
echo "║    或: python3 web.py                                    ║"
echo "║                                                          ║"
echo "║  访问地址:                                               ║"
echo "║    http://localhost:7860                                 ║"
echo "║                                                          ║"
echo "║  已安装功能:                                             ║"
echo "║    ✅ Edge-TTS（云端语音，开箱即用）                      ║"
echo "║    ✅ 文件解析（txt/pdf/docx/srt）                        ║"
echo "║    ✅ 音频/视频处理（ffmpeg）                             ║"
echo "║    ✅ 代理支持（自动检测）                                ║"
echo "║                                                          ║"
echo "║  可选安装（语音识别）:                                    ║"
echo "║    pip3 install faster-whisper --break-system-packages    ║"
echo "║    或: pip3 install vosk --break-system-packages          ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
