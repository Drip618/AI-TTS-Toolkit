#!/bin/bash
# ============================================================
# 灵枢TTS工具箱 一键安装脚本
# 适配：MacBook M5 / Apple Silicon / macOS
# 安装路径：/Users/Drip/Documents/AI-TTS-Toolkit/
# 包含：Edge-TTS / Qwen3-TTS / GPT-SoVITS / IndexTTS2
# ============================================================

set -e  # 遇到错误立即停止

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  灵枢TTS工具箱 一键安装${NC}"
echo -e "${BLUE}  适配 MacBook M5 / Apple Silicon${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查系统
if [[ $(uname -m) != "arm64" ]]; then
    echo -e "${RED}⚠️  检测到非Apple Silicon芯片，部分功能可能需要调整${NC}"
fi

# 检查存储空间
AVAILABLE_GB=$(df -g /Users/Drip | awk 'NR==2{print $4}')
if [[ $AVAILABLE_GB -lt 30 ]]; then
    echo -e "${RED}❌ 可用存储空间不足30GB（当前${AVAILABLE_GB}GB），请清理空间后重试${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 存储空间充足（可用${AVAILABLE_GB}GB）${NC}"

# 检查Homebrew
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}📦 正在安装Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi
echo -e "${GREEN}✅ Homebrew 已安装${NC}"

# 检查conda
if ! command -v conda &> /dev/null; then
    echo -e "${YELLOW}📦 正在安装Miniconda...${NC}"
    brew install --cask miniconda
    conda init zsh
    source ~/.zshrc
fi
echo -e "${GREEN}✅ Conda 已安装${NC}"

# ============================================================
# 创建目录结构
# ============================================================
BASE_DIR="/Users/Drip/Documents/AI-TTS-Toolkit"
mkdir -p "$BASE_DIR"

echo ""
echo -e "${BLUE}📁 目录结构：${NC}"
echo "$BASE_DIR/"
echo "├── 01_Edge-TTS/          # 微软免费TTS（最简单）"
echo "├── 02_Qwen3-TTS/         # 阿里通义TTS（3秒克隆+语音设计）"
echo "├── 03_GPT-SoVITS/        # 专业声音克隆（1-3分钟训练）"
echo "├── 04_IndexTTS2/         # B站开源（情感独立控制）"
echo "├── shared-venv/          # 共享Python虚拟环境"
echo "└── toolkit-scripts/      # 便捷使用脚本"
echo ""

# ============================================================
# 安装1：Edge-TTS（最简单，5分钟）
# ============================================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  [1/4] 安装 Edge-TTS（微软免费TTS）${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

mkdir -p "$BASE_DIR/01_Edge-TTS"

# 创建共享虚拟环境
if [ ! -d "$BASE_DIR/shared-venv" ]; then
    python3 -m venv "$BASE_DIR/shared-venv"
fi
source "$BASE_DIR/shared-venv/bin/activate"

pip install --upgrade pip -q
pip install edge-tts -q

echo -e "${GREEN}✅ Edge-TTS 安装完成${NC}"

# 创建便捷使用脚本
cat > "$BASE_DIR/toolkit-scripts/edge-tts-quick.sh" << 'EDGEEOF'
#!/bin/bash
# Edge-TTS 快速配音脚本
# 用法: ./edge-tts-quick.sh "要说的话" output.mp3
# 用法: ./edge-tts-quick.sh "要说的话" output.mp3 zh-CN-YunyangNeural

source /Users/Drip/Documents/AI-TTS-Toolkit/shared-venv/bin/activate

TEXT="$1"
OUTPUT="${2:-output.mp3}"
VOICE="${3:-zh-CN-XiaoyiNeural}"

if [ -z "$TEXT" ]; then
    echo "用法: $0 \"文本内容\" [输出文件.mp3] [声音]"
    echo ""
    echo "常用中文声音："
    echo "  zh-CN-XiaoyiNeural    晓晓（女声，温柔）"
    echo "  zh-CN-YunyangNeural   云扬（男声，新闻播报）"
    echo "  zh-CN-YunjianNeural   云健（男声，沉稳）"
    echo "  zh-CN-XiaoxuanNeural  晓萱（女声，活泼）"
    echo "  zh-CN-YunxiNeural     云希（男声，自然）"
    echo ""
    echo "示例："
    echo "  $0 \"大家好，欢迎收听本期节目\" demo.mp3 zh-CN-YunyangNeural"
    exit 1
fi

edge-tts --voice "$VOICE" --text "$TEXT" --write-media "$OUTPUT"
echo "✅ 已生成: $OUTPUT"
EDGEEOF
chmod +x "$BASE_DIR/toolkit-scripts/edge-tts-quick.sh"

# 创建批量配音脚本
cat > "$BASE_DIR/toolkit-scripts/edge-tts-batch.sh" << 'BATCHEDGEEOF'
#!/bin/bash
# Edge-TTS 批量配音脚本
# 从文本文件批量生成音频，每行一句
# 用法: ./edge-tts-batch.sh lines.txt output_dir zh-CN-XiaoyiNeural

source /Users/Drip/Documents/AI-TTS-Toolkit/shared-venv/bin/activate

INPUT_FILE="$1"
OUTPUT_DIR="${2:-./output}"
VOICE="${3:-zh-CN-XiaoyiNeural}"

if [ -z "$INPUT_FILE" ]; then
    echo "用法: $0 文本文件.txt [输出目录] [声音]"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
LINE_NUM=0
while IFS= read -r line; do
    LINE_NUM=$((LINE_NUM + 1))
    if [ -n "$line" ]; then
        OUTPUT_FILE=$(printf "%s/line_%03d.mp3" "$OUTPUT_DIR" "$LINE_NUM")
        edge-tts --voice "$VOICE" --text "$line" --write-media "$OUTPUT_FILE"
        echo "✅ 第${LINE_NUM}句 → $OUTPUT_FILE"
    fi
done < "$INPUT_FILE"
echo "✅ 共生成${LINE_NUM}个音频文件到 $OUTPUT_DIR"
BATCHEDGEEOF
chmod +x "$BASE_DIR/toolkit-scripts/edge-tts-batch.sh"

echo -e "${GREEN}✅ Edge-TTS 便捷脚本已创建${NC}"

# ============================================================
# 安装2：Qwen3-TTS（30分钟）
# ============================================================
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  [2/4] 安装 Qwen3-TTS（阿里通义TTS）${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

mkdir -p "$BASE_DIR/02_Qwen3-TTS"

# 创建Qwen3-TTS专用conda环境
conda create -n qwen3tts python=3.10 -y 2>&1 | tail -3
eval "$(conda shell.bash hook)"
conda activate qwen3tts

# 安装PyTorch（Apple Silicon版本）
pip install torch torchvision torchaudio -q

# 安装MLX加速框架
pip install mlx mlx-lm -q

# 克隆Qwen3-TTS
cd "$BASE_DIR/02_Qwen3-TTS"
if [ ! -d "Qwen3-TTS" ]; then
    git clone https://github.com/QwenLM/Qwen3-TTS.git 2>&1 | tail -3
fi

cd "$BASE_DIR/02_Qwen3-TTS/Qwen3-TTS"
pip install -r requirements.txt -q 2>&1 | tail -3

echo -e "${GREEN}✅ Qwen3-TTS 安装完成${NC}"
echo -e "${YELLOW}⚠️  首次运行需要下载模型（约3-5GB），请耐心等待${NC}"

# ============================================================
# 安装3：GPT-SoVITS（1小时）
# ============================================================
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  [3/4] 安装 GPT-SoVITS（专业声音克隆）${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

mkdir -p "$BASE_DIR/03_GPT-SoVITS"

# 创建GPT-SoVITS专用conda环境
conda create -n gpt-sovits python=3.10 -y 2>&1 | tail -3
eval "$(conda shell.bash hook)"
conda activate gpt-sovits

# 安装PyTorch（Apple Silicon版本，MPS后端）
pip install torch torchvision torchaudio -q

# 克隆GPT-SoVITS
cd "$BASE_DIR/03_GPT-SoVITS"
if [ ! -d "GPT-SoVITS" ]; then
    git clone https://github.com/X-T-E/GPT-SoVITS.git 2>&1 | tail -3
fi

cd "$BASE_DIR/03_GPT-SoVITS/GPT-SoVITS"
pip install -r requirements.txt -q 2>&1 | tail -3

# Mac专用：设置MPS后端
cat > "$BASE_DIR/03_GPT-SoVITS/mac_config.sh" << 'MACCONF'
#!/bin/bash
# GPT-SoVITS Mac启动配置
# 使用Metal Performance Shaders加速

export PYTORCH_ENABLE_MPS_FALLBACK=1
export CUDA_VISIBLE_DEVICES=""  # 禁用CUDA，强制使用MPS

echo "🚀 GPT-SoVITS Mac模式已启用（MPS加速）"
echo "启动WebUI: python GPT_SoVITS/inference_webui.py"
MACCONF
chmod +x "$BASE_DIR/03_GPT-SoVITS/mac_config.sh"

echo -e "${GREEN}✅ GPT-SoVITS 安装完成${NC}"
echo -e "${YELLOW}⚠️  Mac上使用MPS后端，速度比NVIDIA慢约30%，但32GB内存完全够用${NC}"
echo -e "${YELLOW}⚠️  首次运行需下载预训练模型（约8-10GB）${NC}"

# ============================================================
# 安装4：IndexTTS2（按需安装）
# ============================================================
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  [4/4] 安装 IndexTTS2（B站开源，情感控制）${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

mkdir -p "$BASE_DIR/04_IndexTTS2"

# 复用GPT-SoVITS环境（依赖类似）
eval "$(conda shell.bash hook)"
conda activate gpt-sovits

# 克隆IndexTTS2
cd "$BASE_DIR/04_IndexTTS2"
if [ ! -d "IndexTTS2" ]; then
    git clone https://github.com/index-tts/index-tts.git IndexTTS2 2>&1 | tail -3
fi

cd "$BASE_DIR/04_IndexTTS2/IndexTTS2"
pip install -r requirements.txt -q 2>&1 | tail -3

echo -e "${GREEN}✅ IndexTTS2 安装完成${NC}"

# ============================================================
# 创建总启动脚本
# ============================================================
cat > "$BASE_DIR/start.sh" << 'STARTEOF'
#!/bin/bash
# 灵枢TTS工具箱 - 启动菜单

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  🎙️ 灵枢TTS工具箱${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "选择要启动的工具："
echo ""
echo "  1) Edge-TTS      微软免费TTS（最简单，推荐日常使用）"
echo "  2) Qwen3-TTS     阿里通义TTS（3秒克隆+语音设计）"
echo "  3) GPT-SoVITS    专业声音克隆（1-3分钟训练）"
echo "  4) IndexTTS2     情感独立控制（精确时长）"
echo "  5) 查看所有中文声音列表（Edge-TTS）"
echo "  0) 退出"
echo ""
read -p "请输入编号: " choice

case $choice in
    1)
        echo -e "${GREEN}🚀 启动 Edge-TTS 快速配音...${NC}"
        echo "用法: edge-tts-quick.sh \"文本\" 输出.mp3 声音"
        echo "示例: edge-tts-quick.sh \"大家好\" demo.mp3 zh-CN-YunyangNeural"
        echo ""
        read -p "输入文本: " text
        read -p "输出文件名(默认output.mp3): " output
        output=${output:-output.mp3}
        read -p "声音(默认zh-CN-XiaoyiNeural): " voice
        voice=${voice:-zh-CN-XiaoyiNeural}
        /Users/Drip/Documents/AI-TTS-Toolkit/toolkit-scripts/edge-tts-quick.sh "$text" "$output" "$voice"
        ;;
    2)
        echo -e "${GREEN}🚀 启动 Qwen3-TTS...${NC}"
        eval "$(conda shell.bash hook)"
        conda activate qwen3tts
        cd /Users/Drip/Documents/AI-TTS-Toolkit/02_Qwen3-TTS/Qwen3-TTS
        python webui.py 2>/dev/null || python app.py 2>/dev/null || echo "请查看README.md获取启动命令"
        ;;
    3)
        echo -e "${GREEN}🚀 启动 GPT-SoVITS...${NC}"
        source /Users/Drip/Documents/AI-TTS-Toolkit/03_GPT-SoVITS/mac_config.sh
        eval "$(conda shell.bash hook)"
        conda activate gpt-sovits
        cd /Users/Drip/Documents/AI-TTS-Toolkit/03_GPT-SoVITS/GPT-SoVITS
        python GPT_SoVITS/inference_webui.py
        ;;
    4)
        echo -e "${GREEN}🚀 启动 IndexTTS2...${NC}"
        eval "$(conda shell.bash hook)"
        conda activate gpt-sovits
        cd /Users/Drip/Documents/AI-TTS-Toolkit/04_IndexTTS2/IndexTTS2
        python webui.py 2>/dev/null || python app.py 2>/dev/null || echo "请查看README.md获取启动命令"
        ;;
    5)
        echo -e "${YELLOW}📋 所有中文声音：${NC}"
        source /Users/Drip/Documents/AI-TTS-Toolkit/shared-venv/bin/activate
        edge-tts --list-voices | grep "zh-CN" | while read line; do
            echo "  $line"
        done
        ;;
    0)
        echo "再见！"
        exit 0
        ;;
    *)
        echo "无效选择"
        ;;
esac
STARTEOF
chmod +x "$BASE_DIR/start.sh"

# ============================================================
# 完成
# ============================================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ 全部安装完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📂 安装路径：${NC}$BASE_DIR"
echo ""
echo -e "${BLUE}🚀 快速开始：${NC}"
echo ""
echo -e "  ${YELLOW}Edge-TTS（最简单）：${NC}"
echo -e "    cd $BASE_DIR"
echo -e "    ./start.sh  → 选1"
echo ""
echo -e "  ${YELLOW}Qwen3-TTS（3秒克隆）：${NC}"
echo -e "    cd $BASE_DIR"
echo -e "    ./start.sh  → 选2"
echo ""
echo -e "  ${YELLOW}GPT-SoVITS（专业克隆）：${NC}"
echo -e "    cd $BASE_DIR"
echo -e "    ./start.sh  → 选3"
echo ""
echo -e "  ${YELLOW}批量配音：${NC}"
echo -e "    ./toolkit-scripts/edge-tts-batch.sh 台词.txt ./audio zh-CN-YunyangNeural"
echo ""
echo -e "${YELLOW}⚠️  注意事项：${NC}"
echo "  - 首次运行Qwen3-TTS/GPT-SoVITS需下载模型（3-10GB）"
echo "  - GPT-SoVITS在Mac上使用MPS加速，比NVIDIA慢约30%"
echo "  - 如遇问题，查看各工具目录下的README.md"
echo ""
