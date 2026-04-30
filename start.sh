#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  🎙️ AI-TTS-Studio 一键启动脚本
#  用法: chmod +x start.sh && ./start.sh
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     🎙️  AI-TTS-Studio  启动中...  🎙️                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 检查 python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 python3，请先运行 ./install.sh 安装依赖${NC}"
    exit 1
fi

# 检查 edge-tts
if ! python3 -c "import edge_tts" 2>/dev/null; then
    echo -e "${RED}❌ edge-tts 未安装，请先运行 ./install.sh 安装依赖${NC}"
    exit 1
fi

# 检查 ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}❌ ffmpeg 未安装，请先运行 ./install.sh 安装依赖${NC}"
    exit 1
fi

# 清理旧临时文件
if [ -d ".temp" ]; then
    find .temp -type f -mmin +60 -delete 2>/dev/null
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"
echo -e "${CYAN}🌐 访问地址: http://localhost:7860${NC}"
echo -e "${CYAN}⏹️  按 Ctrl+C 停止服务${NC}"
echo ""

# 启动
python3 web.py
