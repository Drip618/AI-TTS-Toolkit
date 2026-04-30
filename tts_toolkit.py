#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║           🎙️  AI-TTS-Toolkit  全球TTS工具箱  🎙️            ║
║     跨平台 · 零依赖 · 交互式安装 · 自由选配                 ║
║     支持 macOS / Linux / Windows (WSL/Git Bash)             ║
╚══════════════════════════════════════════════════════════════╝

用法:
    python3 tts_toolkit.py          # 交互式安装
    python3 tts_toolkit.py --list   # 列出所有工具
    python3 tts_toolkit.py --install 1,3,5  # 直接安装指定编号

作者: 灵枢AI导演系统 | 版本: v1.0 | 2026-04-30
"""

import os
import sys
import platform
import subprocess
import shutil
import json
import stat

# ═══════════════════════════════════════════════════════════════
#  ANSI 颜色 & 样式（纯标准库，零依赖）
# ═══════════════════════════════════════════════════════════════

class C:
    """终端颜色"""
    R = '\033[0m'       # Reset
    B = '\033[1m'       # Bold
    D = '\033[2m'       # Dim
    RED = '\033[91m'
    GRN = '\033[92m'
    YEL = '\033[93m'
    BLU = '\033[94m'
    MAG = '\033[95m'
    CYN = '\033[96m'
    WHT = '\033[97m'
    BG_BLK = '\033[40m'
    BG_GRN = '\033[42m'
    BG_YEL = '\033[43m'
    BG_BLU = '\033[44m'

def print_banner():
    banner = f"""
{C.BLU}{C.BG_BLK}╔══════════════════════════════════════════════════════════════╗{C.R}
{C.BLU}{C.BG_BLK}║{C.R}  {C.WHT}{C.B}🎙️  AI-TTS-Toolkit  全球TTS工具箱  v1.0{C.R}              {C.BLU}{C.BG_BLK}║{C.R}
{C.BLU}{C.BG_BLK}║{C.R}  {C.CYN}跨平台 · 零依赖 · 交互式安装 · 自由选配{C.R}              {C.BLU}{C.BG_BLK}║{C.R}
{C.BLU}{C.BG_BLK}║{C.R}  {C.YEL}支持 macOS / Linux / Windows (WSL/Git Bash){C.R}       {C.BLU}{C.BG_BLK}║{C.R}
{C.BLU}{C.BG_BLK}╚══════════════════════════════════════════════════════════════╝{C.R}
"""
    print(banner)

# ═══════════════════════════════════════════════════════════════
#  平台检测
# ═══════════════════════════════════════════════════════════════

def detect_platform():
    """检测操作系统和硬件"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    is_mac = system == 'darwin'
    is_linux = system == 'linux'
    is_windows = system == 'windows'
    is_arm = machine in ('arm64', 'aarch64')
    is_x86 = machine in ('x86_64', 'amd64')
    has_nvidia = False

    if is_linux or is_mac:
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
            has_nvidia = result.returncode == 0
        except:
            pass

    return {
        'system': system,
        'machine': machine,
        'is_mac': is_mac,
        'is_linux': is_linux,
        'is_windows': is_windows,
        'is_arm': is_arm,
        'is_x86': is_x86,
        'has_nvidia': has_nvidia,
        'label': 'macOS (Apple Silicon)' if (is_mac and is_arm) else
                 'macOS (Intel)' if is_mac else
                 'Linux (NVIDIA GPU)' if (is_linux and has_nvidia) else
                 'Linux (CPU only)' if is_linux else
                 'Windows'
    }

# ═══════════════════════════════════════════════════════════════
#  TTS 工具数据库（全球工具完整目录）
# ═══════════════════════════════════════════════════════════════

TTS_TOOLS = [
    # ─── 第一类：云端API（无需GPU，最简单） ───
    {
        'id': 1,
        'name': 'Edge-TTS',
        'name_cn': '微软Edge语音',
        'category': '☁️ 云端API',
        'tags': ['免费', '零配置', '300+音色', '40+语言'],
        'desc': '微软Azure语音引擎Python封装，完全免费无限制',
        'desc_cn': '一行pip安装，300+音色，40+语言，完全免费',
        'github': 'https://github.com/rany2/edge-tts',
        'lang': 'Python',
        'need_gpu': False,
        'need_conda': False,
        'disk_mb': 50,
        'ram_mb': 100,
        'difficulty': '⭐',
        'platforms': ['mac', 'linux', 'windows'],
        'install': [
            'pip install edge-tts',
        ],
        'test': 'edge-tts --text "你好世界" --write-media test.mp3',
        'note': '最简单的TTS工具，调用微软云端API，无需本地GPU。适合快速配音、批量生成。',
    },
    {
        'id': 2,
        'name': 'ChatTTS',
        'name_cn': '对话式TTS',
        'category': '🤖 开源本地',
        'tags': ['免费', '口语化', '情感丰富', '中英双语'],
        'desc': '专为对话场景设计，口语化程度极高，呼吸停顿自然',
        'desc_cn': '中文口语化天花板，情感丰富，适合对话/播客/有声书',
        'github': 'https://github.com/2noise/ChatTTS',
        'lang': 'Python',
        'need_gpu': False,  # CPU也能跑，只是慢
        'need_conda': True,
        'disk_mb': 3000,
        'ram_mb': 4000,
        'difficulty': '⭐⭐',
        'platforms': ['mac', 'linux', 'windows'],
        'install': [
            'conda create -n chattts python=3.10 -y',
            'conda activate chattts',
            'pip install ChatTTS',
        ],
        'test': 'python -c "import ChatTTS; chat=ChatTTS.Chat(); chat.load(); print(\'ChatTTS OK\')"',
        'note': '口语化效果极佳，自动添加语气词和呼吸声。CPU可跑但较慢，推荐有GPU。',
    },

    # ─── 第二类：声音克隆（开源本地） ───
    {
        'id': 3,
        'name': 'Qwen3-TTS',
        'name_cn': '通义千问TTS',
        'category': '🧬 声音克隆',
        'tags': ['免费', '3秒克隆', '语音设计', '97ms延迟'],
        'desc': '阿里通义2026开源，3秒克隆+自然语言描述音色',
        'desc_cn': '3秒极速克隆，用文字描述创造声音（"温柔女声，略带沙哑"）',
        'github': 'https://github.com/QwenLM/Qwen3-TTS',
        'lang': 'Python',
        'need_gpu': True,
        'need_conda': True,
        'disk_mb': 5000,
        'ram_mb': 6000,
        'difficulty': '⭐⭐',
        'platforms': ['mac', 'linux', 'windows'],
        'install': [
            'conda create -n qwen3tts python=3.10 -y',
            'conda activate qwen3tts',
            'pip install torch torchvision torchaudio',
            '# Mac Apple Silicon 加速:',
            'pip install mlx mlx-lm',
            'git clone https://github.com/QwenLM/Qwen3-TTS.git',
            'cd Qwen3-TTS && pip install -r requirements.txt',
        ],
        'test': 'python webui.py  # 或 python app.py',
        'note': '独有"语音设计"功能：用文字描述想要的音色特征，无需参考音频。Mac用MLX加速。',
    },
    {
        'id': 4,
        'name': 'GPT-SoVITS',
        'name_cn': '专业声音克隆',
        'category': '🧬 声音克隆',
        'tags': ['免费', '1-3分钟训练', 'WebUI', '中文顶尖'],
        'desc': '国产精品，1-3分钟音频训练专属音色，中文效果业界领先',
        'desc_cn': '1-3分钟音频训练专属音色，WebUI操作，中文克隆效果顶尖',
        'github': 'https://github.com/X-T-E/GPT-SoVITS',
        'lang': 'Python',
        'need_gpu': True,
        'need_conda': True,
        'disk_mb': 10000,
        'ram_mb': 12000,
        'difficulty': '⭐⭐⭐',
        'platforms': ['mac', 'linux', 'windows'],
        'install': [
            'conda create -n gpt-sovits python=3.10 -y',
            'conda activate gpt-sovits',
            'pip install torch torchvision torchaudio',
            'git clone https://github.com/X-T-E/GPT-SoVITS.git',
            'cd GPT-SoVITS && pip install -r requirements.txt',
            '# Mac专用: export PYTORCH_ENABLE_MPS_FALLBACK=1',
        ],
        'test': 'python GPT_SoVITS/inference_webui.py',
        'note': '最专业的声音克隆工具。Mac用MPS加速（比NVIDIA慢30%）。首次需下载预训练模型8-10GB。',
    },
    {
        'id': 5,
        'name': 'IndexTTS2',
        'name_cn': 'B站情感TTS',
        'category': '🧬 声音克隆',
        'tags': ['免费', '情感独立控制', '精确时长', '中英双语'],
        'desc': 'B站开源，音色与情感解耦，精确控制音频时长',
        'desc_cn': '同一句话切换开心/悲伤/愤怒音色不变，精确控制时长对齐视频',
        'github': 'https://github.com/index-tts/index-tts',
        'lang': 'Python',
        'need_gpu': True,
        'need_conda': True,
        'disk_mb': 4000,
        'ram_mb': 6000,
        'difficulty': '⭐⭐',
        'platforms': ['mac', 'linux', 'windows'],
        'install': [
            'conda activate gpt-sovits  # 复用GPT-SoVITS环境',
            'git clone https://github.com/index-tts/index-tts.git IndexTTS2',
            'cd IndexTTS2 && pip install -r requirements.txt',
        ],
        'test': 'python webui.py  # 或 python app.py',
        'note': '情感独立控制是独有优势。可复用GPT-SoVITS的conda环境，节省空间。',
    },
    {
        'id': 6,
        'name': 'CosyVoice',
        'name_cn': '阿里通义语音',
        'category': '🧬 声音克隆',
        'tags': ['免费', '3秒克隆', '18种方言', '150ms延迟'],
        'desc': '阿里通义实验室开源，支持18种中文方言，零样本克隆',
        'desc_cn': '18种中文方言支持，3秒克隆，适合多方言/多语言场景',
        'github': 'https://github.com/FunAudioLLM/CosyVoice',
        'lang': 'Python',
        'need_gpu': True,
        'need_conda': True,
        'disk_mb': 8000,
        'ram_mb': 10000,
        'difficulty': '⭐⭐',
        'platforms': ['mac', 'linux'],
        'install': [
            'conda create -n cosyvoice python=3.10 -y',
            'conda activate cosyvoice',
            'pip install torch torchvision torchaudio',
            '# Mac加速: pip install mlx',
            'git clone https://github.com/FunAudioLLM/CosyVoice.git',
            'cd CosyVoice && pip install -r requirements.txt',
        ],
        'test': 'python webui.py',
        'note': '方言支持是最大优势（粤语、四川话、东北话等18种）。Mac用MLX加速。',
    },
    {
        'id': 7,
        'name': 'Fish-Speech',
        'name_cn': 'Fish语音',
        'category': '🧬 声音克隆',
        'tags': ['免费', '50语言', '情感标签', '流式输出'],
        'desc': '10M+小时训练，50种语言，支持[laugh][whispers]情感标签',
        'desc_cn': '50种语言，情感标签控制（笑声/耳语/超级开心），流式输出',
        'github': 'https://github.com/fishaudio/fish-speech',
        'lang': 'Python',
        'need_gpu': True,
        'need_conda': True,
        'disk_mb': 5000,
        'ram_mb': 6000,
        'difficulty': '⭐⭐',
        'platforms': ['mac', 'linux'],
        'install': [
            'conda create -n fishspeech python=3.10 -y',
            'conda activate fishspeech',
            'pip install torch torchvision torchaudio',
            'pip install fish-speech',
        ],
        'test': 'fish-server --host 0.0.0.0 --port 8080',
        'note': '情感标签系统独特：[laugh]笑声、[whispers]耳语、[super happy]超开心。',
    },
    {
        'id': 8,
        'name': 'Bark',
        'name_cn': 'Suno语音',
        'category': '🤖 开源本地',
        'tags': ['免费', '多语言', '音乐生成', '音效'],
        'desc': 'Suno出品，支持笑声/叹息/背景音乐，输入♪生成旋律',
        'desc_cn': '能生成笑声、叹息、背景音乐，输入♪符号自动哼唱',
        'github': 'https://github.com/suno-ai/bark',
        'lang': 'Python',
        'need_gpu': True,
        'need_conda': True,
        'disk_mb': 4000,
        'ram_mb': 4000,
        'difficulty': '⭐⭐',
        'platforms': ['mac', 'linux', 'windows'],
        'install': [
            'conda create -n bark python=3.10 -y',
            'conda activate bark',
            'pip install git+https://github.com/suno-ai/bark.git',
        ],
        'test': 'python -c "from bark import SAMPLE_RATE, generate_audio, preload_models; preload_models(); audio=generate_audio(\'你好世界\'); print(\'Bark OK\')"',
        'note': '独特功能：能生成非语言声音（笑声、音乐、环境音）。适合创意配音。',
    },

    # ─── 第三类：传统TTS引擎 ───
    {
        'id': 9,
        'name': 'Mozilla TTS',
        'name_cn': '火狐TTS',
        'category': '🔧 传统引擎',
        'tags': ['免费', '40+语言', 'Tacotron2', 'WaveRNN'],
        'desc': 'Mozilla开源，Tacotron2+WaveRNN双引擎，40+语言',
        'desc_cn': '双引擎架构，音质优秀，支持自定义训练，GitHub 9.7k+星',
        'github': 'https://github.com/mozilla/TTS',
        'lang': 'Python',
        'need_gpu': True,
        'need_conda': True,
        'disk_mb': 3000,
        'ram_mb': 4000,
        'difficulty': '⭐⭐',
        'platforms': ['mac', 'linux', 'windows'],
        'install': [
            'conda create -n mozilla-tts python=3.10 -y',
            'conda activate mozilla-tts',
            'pip install TTS',
        ],
        'test': 'tts --list_models',
        'note': '经典开源TTS，社区活跃。支持自定义模型训练，适合有开发经验的用户。',
    },
    {
        'id': 10,
        'name': 'Coqui TTS',
        'name_cn': 'Coqui语音',
        'category': '🔧 传统引擎',
        'tags': ['免费', '300+语言', '5分钟上手', '企业级'],
        'desc': '300+语言预训练模型，企业级稳定性，XTTS多语言克隆',
        'desc_cn': '300+语言，企业级稳定性，XTTS支持多语言声音克隆',
        'github': 'https://github.com/coqui-ai/TTS',
        'lang': 'Python',
        'need_gpu': True,
        'need_conda': True,
        'disk_mb': 5000,
        'ram_mb': 6000,
        'difficulty': '⭐⭐',
        'platforms': ['mac', 'linux', 'windows'],
        'install': [
            'conda create -n coqui python=3.10 -y',
            'conda activate coqui',
            'pip install TTS',
        ],
        'test': 'tts --text "Hello World" --out_path output.wav --model_name "tts_models/multilingual/multi-dataset/xtts_v2"',
        'note': 'XTTS v2支持17种语言的声音克隆。Coqui公司虽已停止运营，但社区仍在维护。',
    },
    {
        'id': 11,
        'name': 'VITS',
        'name_cn': 'VITS语音',
        'category': '🔧 传统引擎',
        'tags': ['免费', '端到端', '高音质', '多说话人'],
        'desc': '变分推理+对抗训练，端到端模型，音质媲美真人',
        'desc_cn': '音质天花板级引擎，端到端架构，支持多说话人模型训练',
        'github': 'https://github.com/jaywalnut310/vits',
        'lang': 'Python',
        'need_gpu': True,
        'need_conda': True,
        'disk_mb': 2000,
        'ram_mb': 3000,
        'difficulty': '⭐⭐⭐',
        'platforms': ['mac', 'linux', 'windows'],
        'install': [
            'conda create -n vits python=3.10 -y',
            'conda activate vits',
            'pip install torch torchvision torchaudio',
            'git clone https://github.com/jaywalnut310/vits.git',
            'cd vits && pip install -r requirements.txt',
        ],
        'test': 'python inference.py --config configs/ljs_base.json --checkpoint_path checkpoints/base.pth --text "测试文本"',
        'note': '音质极高的传统引擎。需要自己准备训练数据集，适合有AI经验的用户。',
    },
    {
        'id': 12,
        'name': 'OpenVoice',
        'name_cn': 'MIT语音克隆',
        'category': '🧬 声音克隆',
        'tags': ['免费', '即时克隆', '音色组合', 'MIT出品'],
        'desc': 'MIT+MyShell出品，即时声音克隆，音色情感自由组合',
        'desc_cn': '即时克隆，可自由组合音色+情感+口音（如御姐声+东北口音）',
        'github': 'https://github.com/myshell-ai/OpenVoice',
        'lang': 'Python',
        'need_gpu': True,
        'need_conda': True,
        'disk_mb': 3000,
        'ram_mb': 4000,
        'difficulty': '⭐⭐',
        'platforms': ['mac', 'linux', 'windows'],
        'install': [
            'conda create -n openvoice python=3.10 -y',
            'conda activate openvoice',
            'pip install torch torchvision torchaudio',
            'git clone https://github.com/myshell-ai/OpenVoice.git',
            'cd OpenVoice && pip install -r requirements.txt',
        ],
        'test': 'python api.py --source_se source.wav --target_se target.wav --output_dir output/',
        'note': '音色+情感+口音三维独立控制。MIT出品，学术级质量。',
    },

    # ─── 第四类：实时语音克隆 ───
    {
        'id': 13,
        'name': 'Real-Time Voice Cloning',
        'name_cn': '实时语音克隆',
        'category': '⚡ 实时克隆',
        'tags': ['免费', '5秒克隆', '实时生成', '英文强'],
        'desc': '5秒录音实时克隆，支持任意文本即时生成',
        'desc_cn': '5秒录音即可实时克隆，适合游戏NPC/虚拟主播/恶搞配音',
        'github': 'https://github.com/CorentinJ/Real-Time-Voice-Cloning',
        'lang': 'Python',
        'need_gpu': True,
        'need_conda': True,
        'disk_mb': 4000,
        'ram_mb': 6000,
        'difficulty': '⭐⭐⭐',
        'platforms': ['linux', 'windows'],  # Mac支持有限
        'install': [
            'conda create -n rtvc python=3.10 -y',
            'conda activate rtvc',
            'pip install torch torchvision torchaudio',
            'git clone https://github.com/CorentinJ/Real-Time-Voice-Cloning.git',
            'cd Real-Time-Voice-Cloning && pip install -r requirements.txt',
        ],
        'test': 'python demo_cli.py',
        'note': '实时克隆速度极快，但中文支持一般。Mac上可能有兼容性问题。',
    },

    # ─── 第五类：专业级/企业级 ───
    {
        'id': 14,
        'name': 'VALL-E',
        'name_cn': 'Meta语音',
        'category': '🏢 企业级',
        'tags': ['免费', '3秒克隆', '环境音效', '16GB显存'],
        'desc': 'Meta出品，3秒克隆+环境音效生成（如教堂回声）',
        'desc_cn': 'Meta出品，可生成带环境音效的语音（教堂回声、山谷回音等）',
        'github': 'https://github.com/enhuiz/vall-e',
        'lang': 'Python',
        'need_gpu': True,
        'need_conda': True,
        'disk_mb': 8000,
        'ram_mb': 16000,
        'difficulty': '⭐⭐⭐⭐',
        'platforms': ['linux'],
        'install': [
            'conda create -n valle python=3.10 -y',
            'conda activate valle',
            'pip install torch torchvision torchaudio',
            'git clone https://github.com/enhuiz/vall-e.git',
            'cd vall-e && pip install -r requirements.txt',
        ],
        'test': 'python inference.py',
        'note': '需要16GB+显存，Mac无法运行。独有环境音效生成能力。仅推荐Linux+NVIDIA高端显卡用户。',
    },
    {
        'id': 15,
        'name': 'So-VITS-SVC',
        'name_cn': '歌声转换',
        'category': '🎵 歌声转换',
        'tags': ['免费', '歌声克隆', '变声器', '中文优化'],
        'desc': '歌声转换/变声器，中文优化，音色情感双调节',
        'desc_cn': 'AI歌声转换，让AI唱你写的歌，或实时变声器聊天',
        'github': 'https://github.com/svc-develop-team/so-vits-svc',
        'lang': 'Python',
        'need_gpu': True,
        'need_conda': True,
        'disk_mb': 5000,
        'ram_mb': 8000,
        'difficulty': '⭐⭐⭐',
        'platforms': ['mac', 'linux', 'windows'],
        'install': [
            'conda create -n sovits python=3.10 -y',
            'conda activate sovits',
            'pip install torch torchvision torchaudio',
            'git clone https://github.com/svc-develop-team/so-vits-svc.git',
            'cd so-vits-svc && pip install -r requirements.txt',
        ],
        'test': 'python webui.py',
        'note': '专注歌声转换（不是普通TTS）。可以训练歌手音色模型，让AI翻唱歌曲。',
    },
]

# ═══════════════════════════════════════════════════════════════
#  安装引擎
# ═══════════════════════════════════════════════════════════════

def run_cmd(cmd, cwd=None, check=True):
    """执行shell命令"""
    print(f"  {C.D}$ {cmd}{C.R}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True, timeout=600
    )
    if result.stdout:
        for line in result.stdout.strip().split('\n')[-3:]:
            print(f"    {C.D}{line}{C.R}")
    if result.returncode != 0 and check:
        print(f"  {C.RED}⚠️  命令返回非零退出码: {result.returncode}{C.R}")
        if result.stderr:
            for line in result.stderr.strip().split('\n')[-3:]:
                print(f"    {C.RED}{line}{C.R}")
    return result

def check_prerequisites(platform_info):
    """检查前置条件，缺失的自动安装"""
    print(f"\n{C.BLU}📋 系统检测{C.R}")
    print(f"  系统: {C.WHT}{platform_info['label']}{C.R}")
    print(f"  架构: {C.WHT}{platform_info['machine']}{C.R}")
    print(f"  GPU:  {C.GRN}NVIDIA ✓{C.R}" if platform_info['has_nvidia'] else f"  GPU:  {C.YEL}无独立GPU（部分工具仅CPU模式）{C.R}")

    # 检查各项
    conda_ok = shutil.which('conda') is not None
    pip_ok = shutil.which('pip') is not None or shutil.which('pip3') is not None
    git_ok = shutil.which('git') is not None
    brew_ok = shutil.which('brew') is not None

    print(f"  Brew:  {C.GRN}✓{C.R}" if brew_ok else f"  Brew:  {C.RED}✗{C.R}")
    print(f"  Conda: {C.GRN}✓{C.R}" if conda_ok else f"  Conda: {C.RED}✗{C.R}")
    print(f"  Pip:   {C.GRN}✓{C.R}" if pip_ok else f"  Pip:   {C.RED}✗{C.R}")
    print(f"  Git:   {C.GRN}✓{C.R}" if git_ok else f"  Git:   {C.RED}✗{C.R}")

    all_ok = conda_ok and pip_ok and git_ok
    if all_ok:
        return True

    # ─── 自动安装缺失环境 ───
    missing = []
    if not brew_ok and platform_info['is_mac']:
        missing.append('Homebrew')
    if not git_ok:
        missing.append('Git')
    if not conda_ok:
        missing.append('Miniconda')
    if not pip_ok:
        missing.append('Pip')

    print(f"\n{C.YEL}⚠️  检测到缺少: {', '.join(missing)}{C.R}")
    print(f"  {C.WHT}是否自动安装这些环境？(需要网络连接){C.R}")

    try:
        choice = input(f"  {C.B}▶ 自动安装？(y/n): {C.R}").strip().lower()
        if choice != 'y':
            print(f"\n{C.RED}❌ 缺少必要工具，请手动安装后再运行。{C.R}")
            print(f"  {C.D}Homebrew:  /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"{C.R}")
            print(f"  {C.D}Git:       brew install git{C.R}")
            print(f"  {C.D}Miniconda: brew install --cask miniconda{C.R}")
            print(f"  {C.D}Pip:       python3 -m ensurepip --upgrade{C.R}")
            return False
    except KeyboardInterrupt:
        print(f"\n  {C.YEL}已取消。{C.R}")
        return False

    # ─── 执行安装 ───
    print(f"\n{C.GRN}{C.B}  🔧 开始安装环境...{C.R}\n")

    # 1. Homebrew (macOS)
    if not brew_ok and platform_info['is_mac']:
        print(f"  {C.BLU}[1] 安装 Homebrew...{C.R}")
        run_cmd('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"', check=False)
        # 添加到 PATH
        if platform_info['is_arm']:
            run_cmd('eval "$(/opt/homebrew/bin/brew shellenv)" && brew --version', check=False)
        else:
            run_cmd('eval "$(/usr/local/bin/brew shellenv)" && brew --version', check=False)
        brew_ok = shutil.which('brew') is not None
        print(f"  Homebrew: {C.GRN}✓ 安装成功{C.R}" if brew_ok else f"  Homebrew: {C.RED}✗ 安装失败{C.R}")

    # 禁止 Homebrew 自动更新（加速后续安装）
    os.environ['HOMEBREW_NO_AUTO_UPDATE'] = '1'

    # 2. Git
    if not git_ok:
        print(f"  {C.BLU}[2] 安装 Git...{C.R}")
        if platform_info['is_mac'] and brew_ok:
            run_cmd('brew install git')
        elif platform_info['is_linux']:
            run_cmd('sudo apt install git -y', check=False)
        git_ok = shutil.which('git') is not None
        print(f"  Git: {C.GRN}✓ 安装成功{C.R}" if git_ok else f"  Git: {C.RED}✗ 安装失败{C.R}")

    # 3. Miniconda
    if not conda_ok:
        print(f"  {C.BLU}[3] 安装 Miniconda...{C.R}")
        if platform_info['is_mac'] and brew_ok:
            run_cmd('brew install --cask miniconda')
        elif platform_info['is_linux']:
            # Linux: 下载安装脚本
            run_cmd('curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh && bash /tmp/miniconda.sh -b -p $HOME/miniconda3', check=False)
        elif platform_info['is_windows']:
            run_cmd('conda install miniconda -y', check=False)
        # 初始化 conda
        if shutil.which('conda'):
            if platform_info['is_mac']:
                run_cmd('eval "$($(brew --prefix)/Caskroom/miniconda/base/bin/conda shell.bash hook)" && conda init zsh', check=False)
            else:
                run_cmd('eval "$(conda shell.bash hook)" && conda init', check=False)
        conda_ok = shutil.which('conda') is not None
        print(f"  Conda: {C.GRN}✓ 安装成功{C.R}" if conda_ok else f"  Conda: {C.RED}✗ 安装失败{C.R}")

    # 4. Pip
    if not pip_ok:
        print(f"  {C.BLU}[4] 安装 Pip...{C.R}")
        run_cmd('python3 -m ensurepip --upgrade 2>/dev/null || python3 -m pip install --upgrade pip', check=False)
        pip_ok = shutil.which('pip') is not None or shutil.which('pip3') is not None
        print(f"  Pip: {C.GRN}✓ 安装成功{C.R}" if pip_ok else f"  Pip: {C.RED}✗ 安装失败{C.R}")

    # 最终检查
    print(f"\n{C.BLU}{'═' * 50}{C.R}")
    print(f"{C.BLU}  📊 环境安装总结{C.R}")
    print(f"{C.BLU}{'═' * 50}{C.R}")
    print(f"  Brew:  {C.GRN}✓{C.R}" if shutil.which('brew') else f"  Brew:  {C.RED}✗{C.R}")
    print(f"  Git:   {C.GRN}✓{C.R}" if shutil.which('git') else f"  Git:   {C.RED}✗{C.R}")
    print(f"  Conda: {C.GRN}✓{C.R}" if shutil.which('conda') else f"  Conda: {C.RED}✗{C.R}")
    print(f"  Pip:   {C.GRN}✓{C.R}" if (shutil.which('pip') or shutil.which('pip3')) else f"  Pip:   {C.RED}✗{C.R}")
    print()

    final_ok = shutil.which('conda') and (shutil.which('pip') or shutil.which('pip3')) and shutil.which('git')
    if not final_ok:
        print(f"  {C.YEL}⚠️  部分环境安装失败，但不影响 Edge-TTS 等简单工具的使用。{C.R}")
        print(f"  {C.YEL}   如需安装全部工具，请手动安装缺失项后重新运行。{C.R}")
        # 不返回 False，让用户继续选择工具（Edge-TTS 不需要 conda）
    return True

def install_tool(tool, base_dir, platform_info):
    """安装单个TTS工具"""
    tool_dir = os.path.join(base_dir, f"{tool['id']:02d}_{tool['name']}")

    print(f"\n{C.BLU}{'━' * 50}{C.R}")
    print(f"{C.BLU}  [{tool['id']}] {tool['name']} - {tool['name_cn']}{C.R}")
    print(f"{C.BLU}{'━' * 50}{C.R}")
    print(f"  {C.D}{tool['desc_cn']}{C.R}")
    print(f"  📁 安装路径: {tool_dir}")
    print(f"  💾 预计占用: {tool['disk_mb']}MB 磁盘 / {tool['ram_mb']}MB 内存")
    print(f"  ⚙️  难度: {tool['difficulty']}  |  GPU: {'需要' if tool['need_gpu'] else '不需要'}")
    print()

    # 创建目录
    os.makedirs(tool_dir, exist_ok=True)

    # Mac特殊处理
    mac_extra = []
    if platform_info['is_mac'] and platform_info['is_arm']:
        if tool['need_gpu']:
            mac_extra = [
                'export PYTORCH_ENABLE_MPS_FALLBACK=1  # Mac Metal加速',
            ]

    # 执行安装命令
    for cmd in tool['install']:
        if cmd.startswith('#'):
            print(f"  {C.YEL}  💡 {cmd[2:].strip()}{C.R}")
            continue

        # 替换conda activate为实际命令
        if 'conda activate' in cmd:
            env_name = cmd.split('conda activate')[-1].strip()
            if platform_info['is_mac']:
                actual_cmd = f'source $(conda info --base)/etc/profile.d/conda.sh && conda activate {env_name} && echo "环境 {env_name} 已激活"'
            else:
                actual_cmd = f'eval "$(conda shell.bash hook)" && conda activate {env_name} && echo "环境 {env_name} 已激活"'
            run_cmd(actual_cmd)
        else:
            run_cmd(cmd, cwd=tool_dir)

    # Mac额外设置
    for cmd in mac_extra:
        print(f"  {C.YEL}  💡 {cmd}{C.R}")

    # 写入说明文件
    readme_path = os.path.join(tool_dir, 'README_灵枢TTS工具箱.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(f"{'=' * 50}\n")
        f.write(f"  {tool['name']} ({tool['name_cn']})\n")
        f.write(f"  灵枢TTS工具箱 自动安装\n")
        f.write(f"{'=' * 50}\n\n")
        f.write(f"描述: {tool['desc_cn']}\n")
        f.write(f"GitHub: {tool['github']}\n")
        f.write(f"分类: {tool['category']}\n")
        f.write(f"标签: {', '.join(tool['tags'])}\n")
        f.write(f"磁盘占用: ~{tool['disk_mb']}MB\n")
        f.write(f"内存占用: ~{tool['ram_mb']}MB\n\n")
        f.write(f"--- 安装命令 ---\n")
        for cmd in tool['install']:
            f.write(f"  {cmd}\n")
        f.write(f"\n--- 测试命令 ---\n")
        f.write(f"  {tool['test']}\n")
        f.write(f"\n--- 使用说明 ---\n")
        f.write(f"  {tool['note']}\n")
        f.write(f"\n--- Mac Apple Silicon 注意 ---\n")
        if platform_info['is_mac'] and platform_info['is_arm']:
            f.write(f"  export PYTORCH_ENABLE_MPS_FALLBACK=1\n")
            f.write(f"  使用MPS(Metal)加速，比NVIDIA慢约30%\n")
        f.write(f"\n安装时间: 2026-04-30\n")

    print(f"\n  {C.GRN}✅ {tool['name']} 安装完成{C.R}")
    print(f"  📄 说明文件: {readme_path}")

    return True

# ═══════════════════════════════════════════════════════════════
#  交互式 TUI
# ═══════════════════════════════════════════════════════════════

def print_tool_list(platform_info):
    """打印工具列表"""
    categories = {}
    for tool in TTS_TOOLS:
        cat = tool['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tool)

    for cat, tools in categories.items():
        print(f"\n  {C.B}{cat}{C.R}")
        print(f"  {'─' * 60}")
        for tool in tools:
            # 平台兼容性
            compatible = any(p in tool['platforms'] for p in
                           (['mac'] if platform_info['is_mac'] else
                            ['linux'] if platform_info['is_linux'] else
                            ['windows'] if platform_info['is_windows'] else []))
            gpu_ok = not tool['need_gpu'] or platform_info['has_nvidia'] or (platform_info['is_mac'] and platform_info['is_arm'])

            status = f"{C.GRN}✓{C.R}" if (compatible and gpu_ok) else f"{C.RED}✗{C.R}"
            warn = f"{C.YEL}⚠{C.R}" if compatible and not gpu_ok else ""

            tags_str = f"{C.D}{' | '.join(tool['tags'][:3])}{C.R}"
            print(f"  {status} {C.WHT}{tool['id']:>2}.{C.R} {C.B}{tool['name']:<22}{C.R} {C.D}{tool['name_cn']:<12}{C.R}  {tags_str}")
            if warn:
                print(f"      {C.YEL}  ⚠ 无GPU，将以CPU模式运行（速度较慢）{C.R}")

def get_selection(platform_info):
    """获取用户选择"""
    print(f"\n  {C.BLU}请选择要安装的工具（输入编号，逗号分隔）:{C.R}")
    print(f"  {C.D}示例: 1,3,4,5  或  all  或  1-5{C.R}")
    print()

    while True:
        try:
            choice = input(f"  {C.B}▶ {C.R}").strip()

            if choice.lower() in ('q', 'quit', 'exit'):
                return []

            if choice.lower() == 'all':
                return [t['id'] for t in TTS_TOOLS]

            # 解析范围 (如 1-5)
            ids = set()
            for part in choice.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = part.split('-', 1)
                    ids.update(range(int(start), int(end) + 1))
                else:
                    ids.add(int(part))

            # 验证
            valid_ids = {t['id'] for t in TTS_TOOLS}
            invalid = ids - valid_ids
            if invalid:
                print(f"  {C.RED}无效编号: {invalid}，可用范围: 1-{len(TTS_TOOLS)}{C.R}")
                continue

            return list(ids)

        except (ValueError, KeyboardInterrupt):
            print(f"  {C.RED}输入无效，请重新输入{C.R}")

def get_install_dir():
    """获取安装目录"""
    home = os.path.expanduser('~')
    default = os.path.join(home, 'Documents', 'AI-TTS-Toolkit')

    print(f"\n  {C.BLU}选择安装目录:{C.R}")
    print(f"  {C.D}默认: {default}{C.R}")

    while True:
        try:
            choice = input(f"  {C.B}▶ {C.R}").strip()
            if not choice:
                return default
            # 展开 ~
            choice = os.path.expanduser(choice)
            # 验证
            parent = os.path.dirname(choice) or choice
            if os.path.isdir(parent) or parent == choice:
                return choice
            print(f"  {C.RED}父目录不存在: {parent}{C.R}")
        except KeyboardInterrupt:
            return default

# ═══════════════════════════════════════════════════════════════
#  主程序
# ═══════════════════════════════════════════════════════════════

def main():
    print_banner()

    # 平台检测
    platform_info = detect_platform()

    # 命令行参数处理
    if '--list' in sys.argv:
        print_tool_list(platform_info)
        return

    if '--install' in sys.argv:
        idx = sys.argv.index('--install')
        if idx + 1 < len(sys.argv):
            ids = [int(x.strip()) for x in sys.argv[idx + 1].split(',')]
        else:
            print(f"{C.RED}用法: python3 tts_toolkit.py --install 1,3,5{C.R}")
            return
        base_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'AI-TTS-Toolkit')
        for tool_id in ids:
            tool = next((t for t in TTS_TOOLS if t['id'] == tool_id), None)
            if tool:
                install_tool(tool, base_dir, platform_info)
        return

    # ─── 交互式安装流程 ───
    print(f"  {C.WHT}检测到系统: {platform_info['label']}{C.R}\n")

    # 检查前置条件（缺失的会自动安装）
    if not check_prerequisites(platform_info):
        return

    # 显示工具列表
    print(f"\n{C.B}  📦 可用TTS工具（共{len(TTS_TOOLS)}个）{C.R}\n")
    print_tool_list(platform_info)

    # 获取安装目录
    base_dir = get_install_dir()
    print(f"\n  {C.GRN}📁 安装目录: {base_dir}{C.R}")
    os.makedirs(base_dir, exist_ok=True)

    # 获取用户选择
    selected_ids = get_selection(platform_info)

    if not selected_ids:
        print(f"\n  {C.YEL}未选择任何工具，退出。{C.R}")
        return

    # 确认安装
    selected_tools = [t for t in TTS_TOOLS if t['id'] in selected_ids]
    total_disk = sum(t['disk_mb'] for t in selected_tools)
    total_ram = max(t['ram_mb'] for t in selected_tools) if selected_tools else 0

    print(f"\n{C.B}  📋 安装计划{C.R}")
    print(f"  {'─' * 50}")
    for tool in selected_tools:
        print(f"  {C.GRN}✓{C.R} [{tool['id']:>2}] {C.B}{tool['name']:<22}{C.R} {tool['name_cn']}")
    print(f"  {'─' * 50}")
    print(f"  {C.WHT}共 {len(selected_tools)} 个工具{C.R}")
    print(f"  {C.WHT}预计磁盘: ~{total_disk}MB{C.R}")
    print(f"  {C.WHT}最大内存: ~{total_ram}MB{C.R}")
    print()

    confirm = input(f"  {C.YEL}确认安装？(y/n): {C.R}").strip().lower()
    if confirm != 'y':
        print(f"  {C.YEL}已取消。{C.R}")
        return

    # 执行安装
    print(f"\n{C.GRN}{C.B}  🚀 开始安装...{C.R}\n")

    success = []
    failed = []
    for i, tool in enumerate(selected_tools):
        print(f"\n{C.BLU}[{i+1}/{len(selected_tools)}]{C.R}")
        try:
            install_tool(tool, base_dir, platform_info)
            success.append(tool['name'])
        except Exception as e:
            print(f"  {C.RED}❌ {tool['name']} 安装失败: {e}{C.R}")
            failed.append(tool['name'])

    # 安装总结
    print(f"\n{C.BLU}{'═' * 50}{C.R}")
    print(f"{C.BLU}  📊 安装总结{C.R}")
    print(f"{C.BLU}{'═' * 50}{C.R}")
    print(f"  ✅ 成功: {C.GRN}{len(success)}{C.R} {', '.join(success)}")
    if failed:
        print(f"  ❌ 失败: {C.RED}{len(failed)}{C.R} {', '.join(failed)}")
    print(f"  📁 路径: {base_dir}")
    print(f"\n  {C.YEL}💡 使用提示:{C.R}")
    print(f"  {C.D}  - 首次运行需下载模型，请耐心等待{C.R}")
    print(f"  {C.D}  - 各工具目录下有 README_灵枢TTS工具箱.txt 说明文件{C.R}")
    print(f"  {C.D}  - Edge-TTS 最简单: pip install edge-tts && edge-tts --text '你好' --write-media test.mp3{C.R}")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {C.YEL}已中断。{C.R}")
        sys.exit(0)
