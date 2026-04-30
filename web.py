#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║     🎙️  AI-TTS-Studio  全球TTS一体化工作台  v3.3  🎙️      ║
║     零依赖 · 纯Python · 暗色科技风 · 自动扫描本地模型      ║
║     打字即出语音 · 声音克隆 · 语音识别 · 智能文件管理      ║
║     模型热切换 · 自动启动/关闭 · 进度条显示                 ║
╚══════════════════════════════════════════════════════════════╝

启动: python3 web.py
访问: http://localhost:7860
"""

import os
import sys
import json
import time
import shutil
import subprocess
import re
import signal
import tempfile
import threading
import urllib.parse
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# ═══════════════════════════════════════════════════════════════
#  全局配置
# ═══════════════════════════════════════════════════════════════

TOOLKIT_DIR = Path(__file__).parent
CONFIG_DIR = TOOLKIT_DIR / ".config"
CONFIG_FILE = CONFIG_DIR / "config.json"
MODELS_DIR = TOOLKIT_DIR / "models"
OUTPUT_DIR = TOOLKIT_DIR / "output"  # 所有输出统一在项目内
UPLOAD_DIR = TOOLKIT_DIR / ".uploads"
TEMP_DIR = TOOLKIT_DIR / ".temp"
LOG_FILE = TOOLKIT_DIR / ".logs" / "server.log"

for d in [CONFIG_DIR, MODELS_DIR, OUTPUT_DIR, UPLOAD_DIR, TEMP_DIR, TOOLKIT_DIR / ".logs"]:
    d.mkdir(parents=True, exist_ok=True)

# 启动时清理旧临时文件（超过1小时的）
for f in TEMP_DIR.iterdir() if TEMP_DIR.exists() else []:
    try:
        if f.stat().st_mtime < time.time() - 3600:
            f.unlink()
    except:
        pass

DEFAULT_CONFIG = {
    "proxy": "http://127.0.0.1:7890",
    "output_dir": str(OUTPUT_DIR),
    "default_engine": "edge-tts",
    "default_voice": "zh-CN-XiaoyiNeural",
    "default_rate": "+0%",
    "default_pitch": "+0Hz",
    "port": 7860,
}

# ═══════════════════════════════════════════════════════════════
#  配置 & 日志
# ═══════════════════════════════════════════════════════════════

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in cfg:
                        cfg[k] = v
                return cfg
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

config = load_config()
# 强制使用项目内 output/ 目录（忽略配置文件中的旧路径）
OUTPUT_DIR = TOOLKIT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
# 同步更新配置文件
config["output_dir"] = str(OUTPUT_DIR)
save_config(config)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
    except:
        pass

# ═══════════════════════════════════════════════════════════════
#  Multipart 解析器
# ═══════════════════════════════════════════════════════════════

def parse_multipart(body, boundary):
    fields, files = {}, {}
    if not boundary:
        return fields, files
    delimiter = b'--' + boundary.encode('utf-8')
    parts = body.split(delimiter)
    for part in parts[1:]:
        if part.startswith(b'--') or b'\r\n\r\n' not in part:
            continue
        header_section, content = part.split(b'\r\n\r\n', 1)
        if content.endswith(b'\r\n'):
            content = content[:-2]
        headers = {}
        for line in header_section.decode('utf-8', errors='replace').split('\r\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                headers[k.strip().lower()] = v.strip()
        cd = headers.get('content-disposition', '')
        nm = re.search(r'name="([^"]*)"', cd)
        fm = re.search(r'filename="([^"]*)"', cd)
        if not nm:
            continue
        if fm:
            files[nm.group(1)] = {'filename': fm.group(1), 'content': content, 'content_type': headers.get('content-type', 'application/octet-stream')}
        else:
            fields[nm.group(1)] = content.decode('utf-8', errors='replace')
    return fields, files

# ═══════════════════════════════════════════════════════════════
#  本地模型自动扫描
# ═══════════════════════════════════════════════════════════════

KNOWN_MODELS = {
    "GPT-SoVITS": {"markers": ["GPT_SoVITS", "api.py", "webui.py"], "name": "GPT-SoVITS", "description": "少样本语音克隆，3秒参考音频复刻声音", "type": "local", "api_port": 9880, "api_endpoint": "/", "voice_endpoint": "/", "start_command": "conda activate gpt-sovits && python api.py", "api_format": "gpt-sovits"},
    "gpt-sovits": {"markers": ["GPT_SoVITS", "api.py", "webui.py"], "name": "GPT-SoVITS", "description": "少样本语音克隆，3秒参考音频复刻声音", "type": "local", "api_port": 9880, "api_endpoint": "/", "voice_endpoint": "/", "start_command": "conda activate gpt-sovits && python api.py", "api_format": "gpt-sovits"},
    "Qwen3-TTS": {"markers": ["qwen_tts", "pyproject.toml"], "name": "Qwen3-TTS", "description": "通义千问语音合成", "type": "local", "api_port": 5000, "start_command": "conda activate qwen3-tts && python -m qwen_tts.webui"},
    "qwen3-tts": {"markers": ["qwen_tts", "pyproject.toml"], "name": "Qwen3-TTS", "description": "通义千问语音合成", "type": "local", "api_port": 5000, "start_command": "conda activate qwen3-tts && python -m qwen_tts.webui"},
    "IndexTTS2": {"markers": ["index_tts", "webui.py"], "name": "IndexTTS2", "description": "高质量语音合成与声音克隆", "type": "local", "api_port": 7865, "start_command": "uv run python webui.py"},
    "indextts2": {"markers": ["index_tts", "webui.py"], "name": "IndexTTS2", "description": "高质量语音合成与声音克隆", "type": "local", "api_port": 7865, "start_command": "uv run python webui.py"},
    "CosyVoice": {"markers": ["cosyvoice", "webui.py"], "name": "CosyVoice", "description": "阿里通义语音，18种方言", "type": "local", "api_port": 50000, "start_command": "python webui.py"},
    "ChatTTS": {"markers": ["ChatTTS", "webui.py"], "name": "ChatTTS", "description": "口语化语音合成", "type": "local", "api_port": 9966, "start_command": "python webui.py"},
    "Fish-Speech": {"markers": ["fish_speech", "fishaudio"], "name": "Fish-Speech", "description": "50种语言，情感标签", "type": "local", "api_port": 8080, "start_command": "python -m fish_speech.webui"},
}

def scan_local_models():
    found = []
    # 扫描目录：只扫描 models/ 子目录（统一管理）
    scan_dirs = [MODELS_DIR]
    for scan_base in scan_dirs:
        if not scan_base.exists():
            continue
        for item in scan_base.iterdir():
            if not item.is_dir() or item.name.startswith('.') or item.name in ('__pycache__', 'node_modules', '.git'):
                continue
            if (item / "model.json").exists():
                try:
                    with open(item / "model.json", 'r', encoding='utf-8') as f:
                        pcfg = json.load(f)
                    found.append({"id": f"plugin-{item.name}", "name": pcfg.get("name", item.name), "description": pcfg.get("description", "自定义模型"), "type": pcfg.get("type", "plugin"), "path": str(item), "api_port": pcfg.get("port"), "api_url": pcfg.get("api_url", ""), "api_endpoint": pcfg.get("api_endpoint", "/api/tts"), "voice_endpoint": pcfg.get("voice_endpoint", "/api/voices"), "start_command": pcfg.get("start_command", ""), "api_format": pcfg.get("api_format", "standard"), "available": False, "source": "plugin"})
                    log(f"插件: {pcfg.get('name', item.name)}")
                    continue
                except:
                    pass
            mi = KNOWN_MODELS.get(item.name)
            if mi:
                found.append({"id": f"local-{item.name.lower()}", "name": mi["name"], "description": mi["description"], "type": mi["type"], "path": str(item), "api_port": mi["api_port"], "api_url": "", "api_endpoint": mi.get("api_endpoint", "/api/tts"), "voice_endpoint": mi.get("voice_endpoint", "/api/voices"), "start_command": mi["start_command"], "api_format": mi.get("api_format", "standard"), "available": False, "source": "scanned"})
                log(f"模型: {mi['name']} @ {item}")
                continue
            py_files = list(item.glob("*.py"))
            if any(f.name in ('webui.py', 'api.py', 'server.py') for f in py_files) and item.name.lower() not in ('ai-tts-toolkit', 'ai-tts-studio'):
                found.append({"id": f"local-{item.name.lower()}", "name": item.name, "description": f"检测到的模型（{len(py_files)}个py文件）", "type": "local", "path": str(item), "api_port": None, "api_url": "", "api_endpoint": "/api/tts", "voice_endpoint": "/api/voices", "start_command": f"cd {item} && python webui.py", "api_format": "standard", "available": False, "source": "auto-detected"})
                log(f"自动检测: {item.name}")
    return found

# ═══════════════════════════════════════════════════════════════
#  TTS 引擎
# ═══════════════════════════════════════════════════════════════

class TTSEngine:
    name = "base"
    description = ""
    engine_type = "base"
    def __init__(self, cfg):
        self.config = cfg
        self.proxy = cfg.get("proxy", "")
    def is_available(self):
        return False
    def generate(self, text, voice, output_path, rate="+0%", pitch="+0Hz", **kwargs):
        raise NotImplementedError
    def get_voices(self):
        return []
    def get_info(self):
        return {"name": self.name, "type": self.engine_type, "available": self.is_available(), "description": self.description}


# 经过验证的、确定可用的中文声音列表（2026年4月实测）
VERIFIED_VOICES = [
    ("zh-CN-XiaoyiNeural", "晓伊 · 年轻女声"),
    ("zh-CN-YunyangNeural", "云扬 · 成熟男声"),
    ("zh-CN-XiaoxuanNeural", "晓萱 · 甜美女声"),
    ("zh-CN-YunjianNeural", "云健 · 浑厚男声"),
    ("zh-CN-YunxiNeural", "云希 · 阳光男声"),
    ("zh-CN-YunxiaNeural", "云夏 · 温柔女声"),
    ("zh-CN-XiaomoNeural", "晓沫 · 知性女声"),
    ("zh-CN-XiaozhenNeural", "晓甄 · 沉稳女声"),
    ("zh-CN-XiaoruiNeural", "晓瑞 · 活泼女声"),
    ("zh-CN-XiaoshuangNeural", "晓双 · 童声"),
    ("zh-CN-XiaoyanNeural", "晓彦 · 少年"),
    ("zh-CN-XiaomengNeural", "晓梦 · 萌系女声"),
    ("zh-CN-XiaochenNeural", "晓辰 · 青年男声"),
    ("zh-CN-XiaohanNeural", "晓涵 · 文艺女声"),
    ("zh-CN-XiaoyueNeural", "晓悦 · 甜美女声"),
    ("zh-CN-XiaoruiNeural", "晓瑞 · 活泼女声"),
    ("zh-CN-XiaofengNeural", "晓风 · 新闻男声"),
    ("zh-CN-XiaohuiNeural", "晓慧 · 职场女声"),
    ("zh-CN-YunfengNeural", "云枫 · 新闻男声"),
    ("zh-CN-YunhaoNeural", "云皓 · 少年男声"),
    ("zh-CN-YunzeNeural", "云泽 · 磁性男声"),
    ("zh-CN-YunyiNeural", "云逸 · 温柔男声"),
    ("zh-CN-YunjingNeural", "云静 · 知性女声"),
    ("zh-CN-YunluoNeural", "云洛 · 古风女声"),
    ("zh-CN-YunmiaoNeural", "云妙 · 童声"),
    ("zh-CN-YunruoNeural", "云若 · 甜美女声"),
    ("zh-CN-YunshuangNeural", "云双 · 童声"),
    ("zh-CN-YunxinNeural", "云新 · 阳光男声"),
    ("zh-CN-YunxiaoNeural", "云霄 · 磁性男声"),
    ("zh-CN-YunyeNeural", "云野 · 浑厚男声"),
    ("zh-CN-YunzeNeural", "云泽 · 磁性男声"),
    ("zh-CN-liaoning-XiaobeiNeural", "东北 · 小北男声"),
    ("zh-CN-shaanxi-XiaoniNeural", "陕西 · 小妮女声"),
    ("zh-TW-HsiaoChenNeural", "台湾 · 晓辰"),
    ("zh-TW-YunJheNeural", "台湾 · 云哲"),
    ("zh-HK-HiuGaaiNeural", "粤语 · 曉佳"),
    ("zh-HK-WanLungNeural", "粤语 · 雲龍"),
    ("en-US-JennyNeural", "Jenny · English Female"),
    ("en-US-GuyNeural", "Guy · English Male"),
    ("en-US-AriaNeural", "Aria · English Female"),
    ("en-US-DavisNeural", "Davis · English Male"),
    ("en-US-JaneNeural", "Jane · English Female"),
    ("en-US-JasonNeural", "Jason · English Male"),
    ("ja-JP-NanamiNeural", "七海 · 日本語女声"),
    ("ja-JP-KeitaNeural", "圭太 · 日本語男声"),
    ("ko-KR-SunHiNeural", "선히 · 한국어 여성"),
    ("ko-KR-InJoonNeural", "인준 · 한국어 남성"),
]


class EdgeTTSEngine(TTSEngine):
    name = "Edge-TTS"
    description = "微软Edge语音，免费云端API，开箱即用"
    engine_type = "cloud"

    def is_available(self):
        return self._get_cmd() != "edge-tts"

    def _get_cmd(self):
        for p in [shutil.which("edge-tts"), "/opt/homebrew/bin/edge-tts", "/usr/local/bin/edge-tts"]:
            if p and os.path.exists(p):
                return p
        return "edge-tts"

    def generate(self, text, voice, output_path, rate=0, pitch=0, **kwargs):
        text, voice = text.strip(), voice.strip()
        # rate: 数字 → edge-tts 格式（如 20 → "+20%", -10 → "-10%"）
        # pitch: 数字 → edge-tts 格式（如 5 → "+5Hz", -10 → "-10Hz"）
        # 注意：edge-tts 负数必须用 --option=value 格式，否则 argparse 会把负数当成选项
        try:
            rate_val = float(rate)
            rate_str = f"{rate_val:+.0f}%" if rate_val != 0 else "+0%"
        except (ValueError, TypeError):
            rate_str = str(rate).strip() or "+0%"
        try:
            pitch_val = float(pitch)
            pitch_str = f"{pitch_val:+.0f}Hz" if pitch_val != 0 else "+0Hz"
        except (ValueError, TypeError):
            pitch_str = str(pitch).strip() or "+0Hz"
        cmd = [self._get_cmd(), "--proxy", self.proxy,
               "--voice", voice or "zh-CN-XiaoyiNeural",
               "--text", text,
               f"--rate={rate_str}", f"--pitch={pitch_str}",
               "--write-media", str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            err = result.stderr[-500:] if result.stderr else "未知错误"
            raise RuntimeError(err)
        # 验证文件非空
        if os.path.exists(output_path) and os.path.getsize(output_path) == 0:
            os.unlink(output_path)
            raise RuntimeError(f"声音 {voice} 无法生成音频，请换一个声音试试")
        return str(output_path)

    def get_voices(self):
        """返回经过验证的声音列表（名称 + 中文描述）"""
        return list(VERIFIED_VOICES)


class LocalModelEngine(TTSEngine):
    def __init__(self, cfg, model_info):
        super().__init__(cfg)
        self.model_info = model_info
        self.name = model_info["name"]
        self.description = model_info["description"]
        self.engine_type = model_info.get("type", "local")
        self.model_path = model_info.get("path", "")
        self.api_port = model_info.get("api_port")
        self.api_url = model_info.get("api_url", "")
        self.api_endpoint = model_info.get("api_endpoint", "/api/tts")
        self.voice_endpoint = model_info.get("voice_endpoint", "/api/voices")
        self.start_command = model_info.get("start_command", "")
        self.api_format = model_info.get("api_format", "standard")  # "standard" 或 "gpt-sovits"

    def _get_base_url(self):
        return self.api_url or (f"http://127.0.0.1:{self.api_port}" if self.api_port else None)

    def _is_api_running(self):
        base = self._get_base_url()
        if not base:
            return False
        try:
            import urllib.request
            req = urllib.request.Request(base, method='GET')
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status < 400
        except:
            return False

    def is_available(self):
        return self._is_api_running()

    def generate(self, text, voice, output_path, rate=0, pitch=0, **kwargs):
        base = self._get_base_url()
        if not base or not self._is_api_running():
            raise RuntimeError(f"{self.name} API 未运行！\n请先在 UI 中切换到该引擎，系统会自动启动。")
        import urllib.request

        if self.api_format == "gpt-sovits":
            # GPT-SoVITS 专用格式：POST / {"text", "text_language", "speed"}
            try:
                speed = 1.0 + float(rate) / 100
            except (ValueError, TypeError):
                speed = 1.0
            payload = json.dumps({
                "text": text.strip(),
                "text_language": "zh",
                "speed": speed,
            }).encode('utf-8')
            endpoint = self.api_endpoint or "/"
            req = urllib.request.Request(f"{base}{endpoint}", data=payload, headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    audio_data = resp.read()
            except urllib.error.HTTPError as e:
                err_body = e.read().decode('utf-8', errors='replace')
                raise RuntimeError(f"{self.name} 生成失败 (HTTP {e.code}): {err_body}")
            if not audio_data or len(audio_data) < 100:
                raise RuntimeError(f"{self.name} 生成了无效音频（{len(audio_data)} bytes）")
            with open(output_path, 'wb') as f:
                f.write(audio_data)
        else:
            # 标准格式：POST /api/tts {"text", "voice", "speed", "pitch"}
            try:
                speed = 1.0 + float(rate) / 100
            except (ValueError, TypeError):
                speed = 1.0
            payload = json.dumps({
                "text": text.strip(),
                "voice": voice,
                "speed": speed,
                "pitch": float(pitch) if str(pitch).lstrip('-').isdigit() else 0,
            }).encode('utf-8')
            req = urllib.request.Request(f"{base}{self.api_endpoint}", data=payload, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=120) as resp:
                with open(output_path, 'wb') as f:
                    f.write(resp.read())

        if os.path.exists(output_path) and os.path.getsize(output_path) == 0:
            os.unlink(output_path)
            raise RuntimeError(f"{self.name} 生成了空文件")
        return str(output_path)

    def get_voices(self):
        base = self._get_base_url()
        if base and self._is_api_running():
            try:
                import urllib.request
                req = urllib.request.Request(f"{base}{self.voice_endpoint}", method='GET')
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    if isinstance(data, list):
                        return [(v, v) for v in data]
            except:
                pass
        return [("默认（需启动API）", "默认")]

    def get_info(self):
        info = super().get_info()
        info["path"] = self.model_path
        info["start_command"] = self.start_command
        info["api_url"] = self._get_base_url() or ""
        info["source"] = self.model_info.get("source", "scanned")
        return info


# ═══════════════════════════════════════════════════════════════
#  模型进程管理器 — 异步启动/关闭 API 服务
# ═══════════════════════════════════════════════════════════════

class ModelProcessManager:
    """管理本地模型的 API 子进程"""

    def __init__(self):
        self.processes = {}       # {engine_id: subprocess.Popen}
        self.lock = threading.Lock()
        self._current_running = None
        self._status = {}         # {engine_id: {"state":"starting"/"ready"/"failed"/"stopped", "message":""}}
        # 日志文件
        self._log_dir = TOOLKIT_DIR / ".logs" / "engines"
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_path(self, engine_id):
        return self._log_dir / f"{engine_id}.log"

    def _build_shell_cmd(self, engine):
        """构建启动命令，处理 conda 环境和模型特殊参数"""
        model_path = engine.model_path
        start_cmd = engine.start_command

        # GPT-SoVITS 特殊处理
        if engine.api_format == "gpt-sovits":
            # 自动添加模型权重参数（-s SoVITS, -g GPT）
            if "-s " not in start_cmd:
                pretrained = self._find_gpt_sovits_pretrained(model_path)
                if pretrained.get("sovits") and pretrained.get("gpt"):
                    start_cmd = f'{start_cmd} -s "{pretrained["sovits"]}" -g "{pretrained["gpt"]}"'
                    log(f"GPT-SoVITS 使用预训练模型: {pretrained['sovits']}")

            # 自动添加参考音频参数
            if "-dr" not in start_cmd:
                refer_wav, refer_text = self._find_gpt_sovits_refer(model_path)
                if refer_wav:
                    start_cmd = f'{start_cmd} -dr "{refer_wav}" -dt "{refer_text}" -dl zh'
                    log(f"GPT-SoVITS 参考音频: {refer_wav}")

        # 查找 conda 的初始化脚本
        conda_init = ""
        for p in [
            Path.home() / "miniconda3" / "etc" / "profile.d" / "conda.sh",
            Path.home() / "anaconda3" / "etc" / "profile.d" / "conda.sh",
            Path.home() / "miniforge3" / "etc" / "profile.d" / "conda.sh",
            Path("/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh"),
            Path("/opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh"),
        ]:
            if p.exists():
                conda_init = f"source {p} && "
                break

        # 如果命令包含 conda activate，需要先 source conda.sh
        if "conda activate" in start_cmd and conda_init:
            shell_cmd = f"{conda_init}{start_cmd}"
        else:
            shell_cmd = start_cmd

        return f'cd "{model_path}" && {shell_cmd}'

    def _find_gpt_sovits_pretrained(self, model_path):
        """查找 GPT-SoVITS 预训练模型权重文件"""
        mp = Path(model_path)
        # 预训练模型目录
        pretrained_dirs = [
            mp / "GPT_SoVITS" / "pretrained_models" / "gsv-v2final-pretrained",
            mp / "GPT_SoVITS" / "pretrained_models",
            mp / "pretrained_models",
        ]
        result = {}
        for d in pretrained_dirs:
            if not d.exists():
                continue
            # 查找 SoVITS 模型（s2D*.pth）
            if not result.get("sovits"):
                for f in d.glob("s2D*.pth"):
                    result["sovits"] = str(f)
                    break
            # 查找 GPT 模型（s2G*.pth 或 s1*.ckpt）
            if not result.get("gpt"):
                for f in d.glob("s2G*.pth"):
                    result["gpt"] = str(f)
                    break
                if not result.get("gpt"):
                    for f in d.glob("s1*.ckpt"):
                        result["gpt"] = str(f)
                        break
            if result.get("sovits") and result.get("gpt"):
                break
        return result

    def _find_gpt_sovits_refer(self, model_path):
        """在 GPT-SoVITS 目录中自动查找参考音频"""
        mp = Path(model_path)
        # 常见参考音频位置
        search_dirs = [
            mp / "SoVITS_weights",
            mp / "GPT_weights",
            mp / "raw",
            mp / "output",
            mp,
        ]
        audio_exts = {'.wav', '.mp3', '.flac', '.ogg', '.m4a'}
        for d in search_dirs:
            if not d.exists():
                continue
            for f in sorted(d.iterdir()):
                if f.suffix.lower() in audio_exts and f.stat().st_size > 1000:
                    # 尝试找同名的 .txt 标注文件
                    txt_file = f.with_suffix('.txt')
                    if txt_file.exists():
                        try:
                            text = txt_file.read_text('utf-8').strip()[:100]
                            if text:
                                return str(f), text
                        except:
                            pass
                    # 没有标注文件，使用默认文本
                    return str(f), "请使用此音频作为参考。"
        return None, None

    def start_engine(self, engine_id, engine):
        """启动引擎（非阻塞，立即返回，后台启动）"""
        with self.lock:
            # Edge-TTS 不需要启动
            if engine_id == "edge-tts" or engine.engine_type == "cloud":
                self._current_running = engine_id
                self._status[engine_id] = {"state": "ready", "message": "云端 API，无需启动"}
                return {"success": True, "message": "Edge-TTS 云端 API，无需启动", "async": False}

            # 已经在运行
            if engine_id in self.processes:
                proc = self.processes[engine_id]
                if proc.poll() is None:
                    self._current_running = engine_id
                    self._status[engine_id] = {"state": "ready", "message": "已在运行"}
                    return {"success": True, "message": f"{engine.name} 已在运行", "async": False}

            if not engine.start_command:
                self._status[engine_id] = {"state": "failed", "message": "未配置启动命令"}
                return {"success": False, "message": f"{engine.name} 未配置启动命令", "async": False}

            # 关闭上一个引擎
            if self._current_running and self._current_running != engine_id:
                self._stop_engine_unlocked(self._current_running)

            # 自动清理端口占用（防止上次进程没杀干净）
            if engine.api_port:
                self._kill_port_users(engine.api_port)

            # 标记为启动中
            self._status[engine_id] = {"state": "starting", "message": f"正在启动 {engine.name}..."}

            # 在后台线程中启动（不阻塞 HTTP 响应）
            log_path = self._get_log_path(engine_id)
            shell_cmd = self._build_shell_cmd(engine)
            log(f"启动引擎: {engine.name}")
            log(f"命令: {shell_cmd}")

            try:
                log_file = open(log_path, 'w')
                proc = subprocess.Popen(
                    ["bash", "-l", "-c", shell_cmd],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    preexec_fn=os.setsid if sys.platform != 'win32' else None,
                    cwd=engine.model_path,
                )
                self.processes[engine_id] = proc
                self._current_running = engine_id

                # 后台线程等待就绪
                t = threading.Thread(target=self._wait_and_check, args=(engine_id, engine), daemon=True)
                t.start()

                return {"success": True, "message": f"{engine.name} 正在启动，请稍候...", "async": True, "log_file": str(log_path)}

            except Exception as e:
                self._status[engine_id] = {"state": "failed", "message": str(e)}
                return {"success": False, "message": f"启动失败: {e}", "async": False}

    def _wait_and_check(self, engine_id, engine):
        """后台等待 API 就绪"""
        proc = self.processes.get(engine_id)
        if not proc:
            return

        # 轮询等待端口就绪（最多120秒）
        for i in range(60):  # 60 * 2秒 = 120秒
            time.sleep(2)
            # 检查进程是否已退出
            if proc.poll() is not None:
                log_path = self._get_log_path(engine_id)
                err = ""
                try:
                    err = log_path.read_text(encoding='utf-8', errors='replace')[-800:]
                except:
                    pass
                self._status[engine_id] = {"state": "failed", "message": f"进程已退出。日志:\n{err}"}
                log(f"引擎 {engine_id} 启动失败，进程已退出")
                return
            # 检查 API 是否就绪
            if engine._is_api_running():
                self._status[engine_id] = {"state": "ready", "message": "启动成功"}
                log(f"引擎 {engine.name} 启动成功")
                return

        # 超时
        if proc.poll() is None:
            self._status[engine_id] = {"state": "ready", "message": "启动中（可能需要更长时间），请尝试生成语音测试"}
            log(f"引擎 {engine_id} 启动等待超时，但进程仍在运行")

    def stop_engine(self, engine_id):
        with self.lock:
            return self._stop_engine_unlocked(engine_id)

    def _stop_engine_unlocked(self, engine_id):
        if engine_id not in self.processes:
            self._status[engine_id] = {"state": "stopped", "message": "未在运行"}
            return {"success": True, "message": "未在运行"}
        proc = self.processes[engine_id]
        if proc.poll() is not None:
            del self.processes[engine_id]
            self._status[engine_id] = {"state": "stopped", "message": "已停止"}
            return {"success": True, "message": "已停止"}
        try:
            if sys.platform != 'win32':
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            else:
                proc.terminate()
        except:
            try:
                proc.kill()
            except:
                pass
        del self.processes[engine_id]
        self._status[engine_id] = {"state": "stopped", "message": "已停止"}

    def _kill_port_users(self, port):
        """自动杀掉占用指定端口的进程"""
        try:
            import subprocess as sp
            result = sp.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True, timeout=5)
            pids = result.stdout.strip().split('\n')
            pids = [p for p in pids if p.strip()]
            if pids:
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                        log(f"自动清理端口 {port} 上的进程 PID={pid}")
                    except:
                        pass
                time.sleep(1)  # 等待端口释放
        except:
            pass
        log(f"已停止引擎: {engine_id}")
        return {"success": True, "message": "已停止"}

    def get_status(self):
        """获取所有引擎状态"""
        return self._status

    def get_engine_status(self, engine_id):
        return self._status.get(engine_id, {"state": "unknown", "message": ""})

    def shutdown_all(self):
        for eid in list(self.processes.keys()):
            self._stop_engine_unlocked(eid)


# 全局进程管理器
process_manager = ModelProcessManager()


# ═══════════════════════════════════════════════════════════════
#  初始化引擎
# ═══════════════════════════════════════════════════════════════

engines = {"edge-tts": EdgeTTSEngine(config)}
local_models = scan_local_models()
for m in local_models:
    engines[m["id"]] = LocalModelEngine(config, m)

def get_engine(eid):
    return engines.get(eid, engines["edge-tts"])

def get_engine_list():
    return [{"id": k, **e.get_info()} for k, e in engines.items()]

# ═══════════════════════════════════════════════════════════════
#  文件处理
# ═══════════════════════════════════════════════════════════════

def extract_text(filepath):
    """从文件中提取文本。返回 (text, error) 元组"""
    filepath = Path(filepath)
    ext = filepath.suffix.lower()
    if ext in ('.txt', '.md', '.srt', '.vtt', '.ass'):
        for enc in ['utf-8', 'gbk', 'gb2312', 'big5', 'utf-16']:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    text = f.read()
                if ext in ('.srt', '.vtt'):
                    text = '\n'.join(l.strip() for l in text.split('\n') if l.strip() and '-->' not in l and not re.match(r'^\d+$', l))
                elif ext == '.ass':
                    clean, in_events = [], False
                    for line in text.split('\n'):
                        if line.strip().startswith('[Events]'): in_events = True; continue
                        if in_events and line.strip().startswith('['): break
                        if in_events and line.strip().startswith('Dialogue:'):
                            parts = line.split(',', 9)
                            if len(parts) >= 10: clean.append(parts[9].replace('\\N', '\n'))
                    text = '\n'.join(clean)
                if text.strip():
                    return text, None
                return "", "文件内容为空"
            except (UnicodeDecodeError, UnicodeError):
                continue
        return "", "无法解码文件，可能编码不支持"
    elif ext == '.pdf':
        try:
            import fitz; doc = fitz.open(str(filepath)); text = "".join(p.get_text() for p in doc); doc.close(); text = text.strip()
            if text: return text, None
            return "", "PDF内容为空"
        except ImportError: return "", "需安装 pymupdf: pip install pymupdf"
        except Exception as e: return "", f"PDF解析失败: {e}"
    elif ext == '.docx':
        try:
            from docx import Document
            text = '\n'.join(p.text for p in Document(str(filepath)).paragraphs if p.text.strip())
            if text: return text, None
            return "", "DOCX内容为空"
        except ImportError: return "", "需安装 python-docx: pip install python-docx"
        except Exception as e: return "", f"DOCX解析失败: {e}"
    return "", f"不支持的文件格式: {ext}"

def extract_audio_from_video(video_path):
    output_path = TEMP_DIR / f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    cmd = ["ffmpeg", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1", str(output_path), "-y"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"音频提取失败: {result.stderr[-500:]}")
    return str(output_path)

def get_audio_duration(file_path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)], capture_output=True, text=True, timeout=10)
        return float(r.stdout.strip())
    except:
        return 0.0

def transcribe_audio(audio_path):
    """语音识别：在线优先（最准确），离线兜底"""
    audio_path = Path(audio_path)
    if not audio_path.exists():
        return "[音频文件不存在]"

    # 检测网络是否可用
    def is_online():
        try:
            import urllib.request
            urllib.request.urlopen("https://www.google.com", timeout=3)
            return True
        except:
            return False

    online = is_online()

    # ★ 在线方案：faster-whisper（最准确，需要网络下载模型）
    if online:
        try:
            from faster_whisper import WhisperModel
            wav_path = TEMP_DIR / f"stt_{audio_path.stem}.wav"
            subprocess.run(["ffmpeg", "-i", str(audio_path), "-ar", "16000", "-ac", "1",
                            "-sample_fmt", "s16", "-acodec", "pcm_s16le", str(wav_path), "-y"],
                           capture_output=True, text=True, timeout=30)
            if wav_path.exists() and wav_path.stat().st_size > 0:
                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                segments, info = model.transcribe(str(wav_path), language="zh", beam_size=3)
                text = " ".join(seg.text for seg in segments).strip()
                wav_path.unlink(missing_ok=True)
                if text:
                    return text
        except ImportError:
            pass
        except Exception as e:
            log(f"faster-whisper 失败: {e}")

    # 在线方案2：openai whisper
    if online and shutil.which("whisper"):
        try:
            r = subprocess.run(
                ["whisper", str(audio_path), "--model", "tiny", "--language", "zh",
                 "--output_format", "txt", "--output_dir", str(TEMP_DIR)],
                capture_output=True, text=True, timeout=120
            )
            txt_path = audio_path.with_suffix('.txt')
            if txt_path.exists():
                text = txt_path.read_text(encoding='utf-8').strip()
                txt_path.unlink()
                if text:
                    return text
        except Exception as e:
            log(f"Whisper 失败: {e}")

    # ★ 离线方案：vosk（不需要网络）
    try:
        import importlib
        if importlib.util.find_spec("vosk"):
            import wave
            import json as _json
            from vosk import Model, KaldiRecognizer

            model_paths = [
                Path.home() / ".vosk" / "model",
                TOOLKIT_DIR / "vosk-model",
            ]
            model_dir = None
            for mp in model_paths:
                if mp.exists():
                    model_dir = mp; break

            if model_dir:
                wav_path = TEMP_DIR / f"vosk_{audio_path.stem}.wav"
                subprocess.run(["ffmpeg", "-i", str(audio_path), "-ar", "16000", "-ac", "1",
                               "-sample_fmt", "s16", str(wav_path), "-y"],
                              capture_output=True, text=True, timeout=30)
                model = Model(str(model_dir))
                rec = KaldiRecognizer(model, 16000)
                wf = wave.open(str(wav_path), "rb")
                result_text = []
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0: break
                    if rec.AcceptWaveform(data):
                        r = _json.loads(rec.Result())
                        if r.get("text"): result_text.append(r["text"])
                final = _json.loads(rec.FinalResult())
                if final.get("text"): result_text.append(final["text"])
                wf.close()
                wav_path.unlink(missing_ok=True)
                if result_text:
                    mode = "离线" if not online else "在线"
                    return f"[{mode}识别] " + " ".join(result_text)
    except Exception as e:
        log(f"Vosk 失败: {e}")

    # 所有方案都不可用
    return (
        "[语音识别不可用，请安装以下任一工具：]\n\n"
        "  方案1（在线，最准确）:\n"
        "    pip install faster-whisper\n\n"
        "  方案2（离线，无需网络）:\n"
        "    pip install vosk\n"
        "    mkdir -p ~/.vosk/model\n"
        "    cd ~/.vosk/model && curl -LO https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip\n"
        "    unzip vosk-model-small-cn-0.22.zip && mv vosk-model-small-cn-0.22/* ."
    )

def parse_script(text, max_chars=200):
    segments = re.split(r'(?<=[。！？\n])', text.strip())
    result, current = [], ""
    for seg in segments:
        seg = seg.strip()
        if not seg: continue
        if len(current) + len(seg) > max_chars and current:
            result.append(current.strip()); current = seg
        else:
            current += seg
    if current.strip():
        result.append(current.strip())
    return result

# ═══════════════════════════════════════════════════════════════
#  HTML
# ═══════════════════════════════════════════════════════════════

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI-TTS Studio</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0a0a0f;--bg2:#12121a;--bg3:#1a1a2e;--border:#2a2a3a;--border2:#333355;--text:#e0e0e0;--text2:#a0a0c0;--text3:#6060a0;--accent:#6c63ff;--accent2:#00d2ff;--green:#00ff88;--red:#ff4466;--yellow:#ffaa00;--radius:12px;--radius2:8px}
body{background:var(--bg);color:var(--text);font-family:'SF Pro Display',-apple-system,BlinkMacSystemFont,sans-serif;min-height:100vh;line-height:1.6}
.container{max-width:1100px;margin:0 auto;padding:20px}
.header{text-align:center;padding:20px 0 14px;border-bottom:1px solid var(--border);margin-bottom:16px}
.header h1{font-size:26px;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header p{color:var(--text3);font-size:12px;margin-top:3px}
.tabs{display:flex;gap:3px;margin-bottom:16px;background:var(--bg2);border-radius:var(--radius);padding:3px;border:1px solid var(--border)}
.tab{flex:1;padding:9px 14px;text-align:center;cursor:pointer;border-radius:var(--radius2);color:var(--text2);font-size:13px;transition:all .2s;border:none;background:transparent;font-weight:500}
.tab:hover{background:var(--bg3);color:var(--text)}
.tab.active{background:var(--accent);color:#fff;box-shadow:0 2px 10px rgba(108,99,255,.3)}
.panel{display:none}.panel.active{display:block}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:18px;margin-bottom:14px}
.card-title{font-size:14px;font-weight:600;color:var(--accent2);margin-bottom:10px;display:flex;align-items:center;gap:6px}
.form-row{display:flex;gap:10px;margin-bottom:10px;flex-wrap:wrap}
.form-group{flex:1;min-width:180px}
.form-group label{display:block;font-size:11px;color:var(--text2);margin-bottom:3px;font-weight:500}
input[type="text"],input[type="number"],textarea,select{width:100%;padding:9px 12px;background:var(--bg3);border:1px solid var(--border2);border-radius:var(--radius2);color:var(--text);font-size:13px;outline:none;transition:border-color .2s}
input:focus,textarea:focus,select:focus{border-color:var(--accent);box-shadow:0 0 0 2px rgba(108,99,255,.2)}
textarea{resize:vertical;min-height:100px;font-family:inherit}
select{cursor:pointer}
.btn{padding:9px 20px;border:none;border-radius:var(--radius2);font-size:13px;font-weight:600;cursor:pointer;transition:all .2s;display:inline-flex;align-items:center;gap:5px}
.btn-primary{background:linear-gradient(135deg,var(--accent),#4834d4);color:#fff}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 4px 15px rgba(108,99,255,.4)}
.btn-secondary{background:var(--bg3);color:var(--text2);border:1px solid var(--border2)}
.btn-secondary:hover{background:var(--border);color:var(--text)}
.btn-success{background:linear-gradient(135deg,#00c853,#009624);color:#fff}
.btn-success:hover{box-shadow:0 4px 15px rgba(0,200,83,.4)}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none!important}
.status-bar{background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius2);padding:10px 14px;font-size:12px;min-height:40px;margin-top:10px;white-space:pre-wrap;word-break:break-all}
.status-bar.success{border-color:var(--green);color:var(--green)}
.status-bar.error{border-color:var(--red);color:var(--red)}
.status-bar.info{border-color:var(--accent);color:var(--accent2)}
.engine-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}
.engine-card{background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius2);padding:14px;transition:border-color .2s}
.engine-card:hover{border-color:var(--accent)}
.engine-card .name{font-weight:600;font-size:14px;margin-bottom:3px;display:flex;align-items:center;gap:6px}
.engine-card .desc{font-size:11px;color:var(--text2);margin-bottom:6px}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;flex-shrink:0}
.dot.on{background:var(--green);box-shadow:0 0 6px var(--green)}
.dot.off{background:var(--red);box-shadow:0 0 6px var(--red)}
.upload-zone{border:2px dashed var(--border2);border-radius:var(--radius);padding:24px;text-align:center;cursor:pointer;transition:all .2s;color:var(--text2)}
.upload-zone:hover{border-color:var(--accent);background:rgba(108,99,255,.05)}
.upload-zone input[type="file"]{display:none}
.upload-zone .icon{font-size:28px;margin-bottom:6px}
.upload-zone .hint{font-size:12px;color:var(--text3)}
.audio-player{background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius2);padding:14px;margin-top:10px}
.audio-player audio,.audio-player video{width:100%;border-radius:var(--radius2)}
.progress-bar{height:4px;background:var(--bg3);border-radius:2px;overflow:hidden;margin-top:6px}
.progress-bar .fill{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:2px;transition:width .3s;width:0%}
.plugin-template{background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius2);padding:14px;margin-bottom:10px;font-family:'SF Mono','Fira Code',monospace;font-size:12px;white-space:pre-wrap;color:var(--text2)}
.voice-group{font-size:11px;color:var(--text3);padding:4px 0 2px;border-bottom:1px solid var(--border);margin-top:4px}
.voice-group:first-child{margin-top:0}
.action-row{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
@media(max-width:768px){.container{padding:10px}.form-row{flex-direction:column}.tabs{flex-wrap:wrap}.tab{flex:1 1 auto;min-width:70px;font-size:11px;padding:7px 10px}}
</style>
</head>
<body>
<div class="container">
<div class="header">
    <h1>🎙️ AI-TTS Studio</h1>
    <p>打字即出语音 · 声音克隆 · 语音识别 · 自动扫描模型 · v3.3</p>
</div>
<div class="tabs">
    <button class="tab active" onclick="switchTab('tts')">🎙️ 语音合成</button>
    <button class="tab" onclick="switchTab('batch')">📜 批量配音</button>
    <button class="tab" onclick="switchTab('audio')">🎵 音频处理</button>
    <button class="tab" onclick="switchTab('models')">🔌 模型管理</button>
    <button class="tab" onclick="switchTab('settings')">⚙️ 设置</button>
</div>

<!-- ═══ 语音合成 ═══ -->
<div id="panel-tts" class="panel active">
    <div class="card">
        <div class="card-title">🎙️ 文字转语音 — 打字就能出声音</div>
        <div class="form-row">
            <div class="form-group" style="max-width:200px">
                <label>🤖 引擎</label>
                <select id="engine" onchange="onEngineChange()"></select>
            </div>
            <div class="form-group" style="max-width:280px">
                <label>🗣️ 声音</label>
                <select id="voice"></select>
            </div>
            <div class="form-group" style="max-width:130px">
                <label>⚡ 语速 <span id="rateVal" style="color:var(--accent2)">0</span>%</label>
                <input type="range" id="rate" min="-100" max="200" value="0" step="5" oninput="document.getElementById('rateVal').textContent=this.value" style="padding:0;height:8px;cursor:pointer;accent-color:var(--accent)">
            </div>
            <div class="form-group" style="max-width:130px">
                <label>🎵 音调 <span id="pitchVal" style="color:var(--accent2)">0</span>Hz</label>
                <input type="range" id="pitch" min="-50" max="50" value="0" step="1" oninput="document.getElementById('pitchVal').textContent=this.value" style="padding:0;height:8px;cursor:pointer;accent-color:var(--accent)">
            </div>
        </div>
        <div class="form-group" style="margin-bottom:10px">
            <textarea id="inputText" placeholder="在这里输入文字，点击下方按钮即可生成语音...&#10;&#10;支持中文、英文、日文等多语言"></textarea>
        </div>
        <div class="form-row" style="align-items:flex-end">
            <div class="form-group">
                <label>📎 或上传文件读取文字（txt/pdf/docx/srt）</label>
                <input type="file" id="fileUpload" accept=".txt,.md,.pdf,.docx,.srt,.vtt,.ass" onchange="onFileUpload(this)" style="padding:6px">
            </div>
            <div style="display:flex;gap:6px;padding-bottom:2px">
                <button class="btn btn-primary" onclick="generateSpeech()" id="genBtn">🔊 生成语音</button>
                <button class="btn btn-secondary" onclick="refreshVoices()">🔄 刷新声音</button>
            </div>
        </div>
        <div id="ttsStatus" class="status-bar" style="display:none"></div>
        <div id="ttsAudio" class="audio-player" style="display:none">
            <audio id="audioPlayer" controls></audio>
            <div class="action-row">
                <button class="btn btn-success" onclick="downloadAudio()" id="dlBtn" style="display:none">💾 保存到本地</button>
                <button class="btn btn-secondary" onclick="openFolder()" id="folderBtn" style="display:none">📂 打开文件夹</button>
                <button class="btn btn-secondary" onclick="discardAudio()" id="discardBtn" style="display:none">🗑️ 丢弃</button>
            </div>
            <div id="audioMeta" style="margin-top:6px;font-size:11px;color:var(--text3)"></div>
        </div>
    </div>
</div>

<!-- ═══ 批量配音 ═══ -->
<div id="panel-batch" class="panel">
    <div class="card">
        <div class="card-title">📜 批量剧本配音</div>
        <div class="form-group" style="margin-bottom:10px">
            <textarea id="scriptText" rows="8" placeholder="粘贴剧本内容...&#10;自动按句号/换行分段配音"></textarea>
        </div>
        <div class="form-row">
            <div class="form-group" style="max-width:150px">
                <label>📏 每段最大字数</label>
                <input type="number" id="maxChars" value="200" min="50" max="1000">
            </div>
            <div style="display:flex;gap:6px;align-items:flex-end;padding-bottom:2px">
                <button class="btn btn-secondary" onclick="previewScript()">📋 预览分段</button>
                <button class="btn btn-primary" onclick="batchGenerate()" id="batchBtn">🚀 批量配音</button>
            </div>
        </div>
        <div id="batchStatus" class="status-bar" style="display:none"></div>
        <div id="batchProgress" class="progress-bar" style="display:none"><div class="fill" id="batchFill"></div></div>
    </div>
</div>

<!-- ═══ 音频处理 ═══ -->
<div id="panel-audio" class="panel">
    <div class="card">
        <div class="card-title">🎵 音频文件处理</div>
        <p style="font-size:12px;color:var(--text2);margin-bottom:10px">上传音频文件，可预览播放、识别文字内容、或用作声音克隆的参考音频。</p>
        <div class="upload-zone" onclick="document.getElementById('audioFileInput').click()">
            <div class="icon">🎵</div>
            <div>点击上传音频文件</div>
            <div class="hint">MP3 / WAV / OGG / FLAC / M4A（仅限音频）</div>
            <input type="file" id="audioFileInput" accept=".mp3,.wav,.ogg,.flac,.m4a,.aac,.wma,.opus" onchange="onAudioUpload(this)">
        </div>
        <div id="audioPreview" class="audio-player" style="display:none;margin-top:10px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                <span id="audioFileName" style="font-size:12px;color:var(--text2)"></span>
                <button class="btn btn-secondary" onclick="clearAudio()" style="padding:3px 10px;font-size:11px">✕ 清除</button>
            </div>
            <audio id="uploadedAudio" controls style="width:100%"></audio>
            <div id="audioInfo" style="margin-top:6px;font-size:11px;color:var(--text3)"></div>
            <div class="action-row">
                <button class="btn btn-secondary" onclick="transcribeUploadedAudio()">📝 识别文字内容</button>
                <button class="btn btn-secondary" onclick="useAsCloneRef()">🎤 用作克隆参考音频</button>
                <button class="btn btn-success" onclick="saveUploadedAudio()">💾 保存音频</button>
            </div>
            <div id="transcribeResult" class="status-bar" style="display:none"></div>
        </div>
    </div>
    <div class="card">
        <div class="card-title">🎬 视频音频提取</div>
        <div class="upload-zone" onclick="document.getElementById('videoFileInput').click()">
            <div class="icon">🎬</div>
            <div>点击上传视频文件</div>
            <div class="hint">MP4 / AVI / MKV / MOV / WebM</div>
            <input type="file" id="videoFileInput" accept=".mp4,.avi,.mkv,.mov,.webm,.flv,.wmv" onchange="onVideoUpload(this)">
        </div>
        <div id="videoStatus" class="status-bar" style="display:none;margin-top:10px"></div>
        <div id="videoPreview" style="display:none;margin-top:10px">
            <video id="uploadedVideo" controls style="width:100%;max-height:360px;border-radius:var(--radius2);background:#000" preload="metadata"></video>
            <div class="action-row">
                <button class="btn btn-success" onclick="extractVideoAudio()">🎵 提取音频</button>
                <button class="btn btn-secondary" onclick="clearVideo()">✕ 清除视频</button>
            </div>
        </div>
        <div id="videoAudio" class="audio-player" style="display:none;margin-top:10px">
            <div style="font-size:12px;color:var(--text2);margin-bottom:6px">提取的音频预览</div>
            <audio id="extractedAudio" controls style="width:100%"></audio>
            <div class="action-row">
                <button class="btn btn-success" onclick="saveExtractedAudio()">💾 保存音频</button>
                <button class="btn btn-secondary" onclick="transcribeVideoAudio()">📝 识别文字</button>
                <button class="btn btn-secondary" onclick="useExtractedAsClone()">🎤 用作克隆参考</button>
            </div>
            <div id="videoTranscribeResult" class="status-bar" style="display:none"></div>
        </div>
    </div>
</div>

<!-- ═══ 模型管理 ═══ -->
<div id="panel-models" class="panel">
    <div class="card">
        <div class="card-title">🔌 已检测到的引擎</div>
        <div id="engineGrid" class="engine-grid"></div>
        <div style="margin-top:10px"><button class="btn btn-secondary" onclick="refreshEngines()">🔄 重新扫描</button></div>
    </div>
    <div class="card">
        <div class="card-title">📦 添加自定义模型</div>
        <p style="font-size:12px;color:var(--text2);margin-bottom:10px">在 <code style="background:var(--bg3);padding:2px 5px;border-radius:3px">models/</code> 下创建子文件夹 + <code style="background:var(--bg3);padding:2px 5px;border-radius:3px">model.json</code></p>
        <div class="plugin-template">{
  "name": "我的模型",
  "description": "模型描述",
  "type": "plugin",
  "port": 8080,
  "api_endpoint": "/api/tts",
  "voice_endpoint": "/api/voices",
  "start_command": "cd ~/my-model && python server.py"
}</div>
        <div style="margin-top:10px"><button class="btn btn-secondary" onclick="scanNewPlugins()">🔍 重新扫描插件</button></div>
    </div>
</div>

<!-- ═══ 设置 ═══ -->
<div id="panel-settings" class="panel">
    <div class="card">
        <div class="card-title">⚙️ 全局设置</div>
        <div class="form-row">
            <div class="form-group"><label>🌐 代理地址</label><input type="text" id="settingProxy"></div>
            <div class="form-group"><label>📁 输出目录</label><input type="text" id="settingOutput"></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>🤖 默认引擎</label><select id="settingEngine"></select></div>
            <div class="form-group"><label>🗣️ 默认声音</label><input type="text" id="settingVoice"></div>
        </div>
        <div style="margin-top:10px"><button class="btn btn-primary" onclick="saveSettings()">💾 保存</button></div>
        <div id="settingsStatus" class="status-bar" style="display:none;margin-top:10px"></div>
    </div>
</div>
</div>

<script>
let currentAudioUrl='',currentAudioPath='',currentTempPath='',uploadedAudioPath='',extractedAudioPath='',uploadedVideoPath='';

function switchTab(name){
    document.querySelectorAll('.tab').forEach((t,i)=>{
        const panels=['tts','batch','audio','models','settings'];
        t.classList.toggle('active',panels[i]===name);
    });
    document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
    document.getElementById('panel-'+name).classList.add('active');
    if(name==='models') refreshEngines();
}

async function api(path,options={}){
    try{const r=await fetch(path,options);return await r.json();}
    catch(e){return{error:'请求失败: '+e.message};}
}

async function init(){
    const data=await api('/api/engines');
    if(data.engines){
        const sel=document.getElementById('engine');sel.innerHTML='';
        data.engines.forEach(e=>{const o=document.createElement('option');o.value=e.id;o.textContent=e.name+(e.available?'':' (需启动)');sel.appendChild(o);});
        const sel2=document.getElementById('settingEngine');sel2.innerHTML='';
        data.engines.forEach(e=>{const o=document.createElement('option');o.value=e.id;o.textContent=e.name;sel2.appendChild(o);});
    }
    const cfg=await api('/api/config');
    if(cfg.proxy)document.getElementById('settingProxy').value=cfg.proxy;
    if(cfg.output_dir)document.getElementById('settingOutput').value=cfg.output_dir;
    if(cfg.default_engine){document.getElementById('engine').value=cfg.default_engine;document.getElementById('settingEngine').value=cfg.default_engine;}
    if(cfg.default_voice)document.getElementById('settingVoice').value=cfg.default_voice;
    await refreshVoices();
}

async function onEngineChange(){
    const eid=document.getElementById('engine').value;
    const engineSel=document.getElementById('engine');
    const engineName=engineSel.options[engineSel.selectedIndex].textContent.split(' (')[0];
    // Edge-TTS 不需要启动
    if(eid==='edge-tts'){await refreshVoices();return;}
    // 禁用控件
    engineSel.disabled=true;
    document.getElementById('genBtn').disabled=true;
    showStatus('ttsStatus','info','🔄 正在切换到 '+engineName+'...\n（自动关闭上一个引擎，启动新引擎）');
    try{
        const d=await api('/api/switch-engine?engine='+encodeURIComponent(eid));
        if(!d.success){showStatus('ttsStatus','error','❌ '+d.message);engineSel.disabled=false;document.getElementById('genBtn').disabled=false;return;}
        if(d.async){
            // 异步启动，轮询状态
            showStatus('ttsStatus','info','🔄 '+engineName+' 正在启动...\n首次加载模型可能需要 30-120 秒，请耐心等待');
            const poll=setInterval(async()=>{
                try{
                    const s=await api('/api/engine-status?engine='+encodeURIComponent(eid));
                    if(s.state==='ready'){
                        clearInterval(poll);
                        showStatus('ttsStatus','success','✅ '+engineName+' 启动成功！可以开始使用了');
                        // 刷新引擎列表
                        const ed=await api('/api/engines');
                        if(ed.engines){engineSel.innerHTML='';ed.engines.forEach(e=>{const o=document.createElement('option');o.value=e.id;o.textContent=e.name+(e.available?'':' (需启动)');engineSel.appendChild(o);});engineSel.value=eid;}
                        await refreshVoices();
                        engineSel.disabled=false;document.getElementById('genBtn').disabled=false;
                    }else if(s.state==='failed'){
                        clearInterval(poll);
                        showStatus('ttsStatus','error','❌ '+engineName+' 启动失败:\n'+s.message);
                        engineSel.disabled=false;document.getElementById('genBtn').disabled=false;
                    }
                    // state==='starting' 继续等待
                }catch(e){clearInterval(poll);engineSel.disabled=false;document.getElementById('genBtn').disabled=false;}
            },3000);
        }else{
            showStatus('ttsStatus','success','✅ '+d.message);
            await refreshVoices();
            engineSel.disabled=false;document.getElementById('genBtn').disabled=false;
        }
    }catch(e){showStatus('ttsStatus','error','❌ 切换失败: '+e.message);engineSel.disabled=false;document.getElementById('genBtn').disabled=false;}
}

async function refreshVoices(){
    const eid=document.getElementById('engine').value;
    const data=await api('/api/voices?engine='+encodeURIComponent(eid));
    const sel=document.getElementById('voice');sel.innerHTML='';
    if(data.voices){
        let lastGroup='';
        data.voices.forEach(v=>{
            const name=typeof v==='string'?v:v[0];
            const desc=typeof v==='string'?v:v[1];
            let group='其他语言';
            if(name.startsWith('zh-CN-'))group='中文（大陆）';
            else if(name.startsWith('zh-TW-'))group='中文（台湾）';
            else if(name.startsWith('zh-HK-'))group='中文（粤语）';
            else if(name.startsWith('en-'))group='英文声音';
            else if(name.startsWith('ja-'))group='日文声音';
            else if(name.startsWith('ko-'))group='韩文声音';
            if(group!==lastGroup){
                const optg=document.createElement('optgroup');optg.label=group;
                const o=document.createElement('option');o.value=name;o.textContent=desc||name;optg.appendChild(o);
                sel.appendChild(optg);lastGroup=group;
            }else{
                const o=document.createElement('option');o.value=name;o.textContent=desc||name;sel.appendChild(o);
            }
        });
    }
}

async function onFileUpload(input){
    if(!input.files.length)return;
    const file=input.files[0];const fd=new FormData();fd.append('file',file);
    showStatus('ttsStatus','info','📄 读取文件: '+file.name+'...');
    try{
        const r=await fetch('/api/extract-text',{method:'POST',body:fd});const d=await r.json();
        if(d.text){document.getElementById('inputText').value=d.text;showStatus('ttsStatus','success','✅ 已读取 '+d.text.length+' 字');}
        else showStatus('ttsStatus','error','❌ '+(d.error||'读取失败'));
    }catch(e){showStatus('ttsStatus','error','❌ '+e.message);}
}

async function generateSpeech(){
    const text=document.getElementById('inputText').value.trim();
    if(!text){showStatus('ttsStatus','error','❌ 请输入文字或上传文件');return;}
    const engine=document.getElementById('engine').value;
    const voice=document.getElementById('voice').value;
    const rate=document.getElementById('rate').value;
    const pitch=document.getElementById('pitch').value;
    const btn=document.getElementById('genBtn');btn.disabled=true;btn.textContent='⏳ 生成中...';
    showStatus('ttsStatus','info','🔊 正在生成语音...');
    document.getElementById('ttsAudio').style.display='none';
    try{
        const r=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,engine,voice,rate,pitch})});
        const d=await r.json();
        if(d.audio_url){
            currentAudioUrl=d.audio_url;currentTempPath=d.temp_path||'';currentAudioPath=d.file_path||'';
            document.getElementById('audioPlayer').src=d.audio_url;
            document.getElementById('ttsAudio').style.display='block';
            document.getElementById('dlBtn').style.display='inline-flex';
            document.getElementById('folderBtn').style.display='none';
            document.getElementById('discardBtn').style.display='inline-flex';
            document.getElementById('audioMeta').textContent='⏱️ '+(d.duration||'?')+'秒 · '+text.length+'字 · 💡 点击「保存到本地」才会存入文件夹';
            showStatus('ttsStatus','success','✅ 生成成功！试听后点「保存到本地」');
        }else showStatus('ttsStatus','error','❌ '+(d.error||'生成失败'));
    }catch(e){showStatus('ttsStatus','error','❌ '+e.message);}
    finally{btn.disabled=false;btn.textContent='🔊 生成语音';}
}

async function downloadAudio(){
    if(!currentTempPath){showStatus('ttsStatus','error','❌ 没有可保存的音频');return;}
    showStatus('ttsStatus','info','💾 保存中...');
    const d=await api('/api/save-audio',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({temp_path:currentTempPath})});
    if(d.success){
        currentAudioPath=d.saved_path||'';
        document.getElementById('folderBtn').style.display='inline-flex';
        document.getElementById('discardBtn').style.display='none';
        document.getElementById('audioMeta').textContent='✅ 已保存到: '+(d.filename||'');
        showStatus('ttsStatus','success','✅ 已保存到 '+d.saved_path);
    }else showStatus('ttsStatus','error','❌ '+(d.error||'保存失败'));
}

function openFolder(){if(currentAudioPath)fetch('/api/open-folder?path='+encodeURIComponent(currentAudioPath));}

function discardAudio(){
    if(currentTempPath)fetch('/api/discard-audio?path='+encodeURIComponent(currentTempPath));
    document.getElementById('ttsAudio').style.display='none';
    document.getElementById('audioPlayer').src='';
    currentAudioUrl='';currentTempPath='';currentAudioPath='';
    showStatus('ttsStatus','info','🗑️ 已丢弃');
}

async function previewScript(){
    const text=document.getElementById('scriptText').value.trim();
    if(!text){showStatus('batchStatus','error','❌ 请输入剧本');return;}
    const mc=parseInt(document.getElementById('maxChars').value)||200;
    const d=await api('/api/parse-script',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,max_chars:mc})});
    if(d.segments){const p=d.segments.map((s,i)=>'【第'+(i+1)+'段】('+s.length+'字)\n'+s).join('\n\n');showStatus('batchStatus','info','📋 共 '+d.segments.length+' 段, '+d.total_chars+' 字\n\n'+p);}
    else showStatus('batchStatus','error','❌ '+(d.error||''));
}

async function batchGenerate(){
    const text=document.getElementById('scriptText').value.trim();
    if(!text){showStatus('batchStatus','error','❌ 请输入剧本');return;}
    const engine=document.getElementById('engine').value,voice=document.getElementById('voice').value;
    const rate=document.getElementById('rate').value,pitch=document.getElementById('pitch').value;
    const mc=parseInt(document.getElementById('maxChars').value)||200;
    const btn=document.getElementById('batchBtn');btn.disabled=true;btn.textContent='⏳ 生成中...';
    document.getElementById('batchProgress').style.display='block';
    try{
        const r=await fetch('/api/batch-generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,engine,voice,rate,pitch,max_chars:mc})});
        const d=await r.json();document.getElementById('batchFill').style.width='100%';
        if(d.results)showStatus('batchStatus','success','✅ 成功: '+d.success+' 段 | ❌ 失败: '+d.failed+' 段\n📁 '+d.output_dir);
        else showStatus('batchStatus','error','❌ '+(d.error||''));
    }catch(e){showStatus('batchStatus','error','❌ '+e.message);}
    finally{btn.disabled=false;btn.textContent='🚀 批量配音';setTimeout(()=>{document.getElementById('batchProgress').style.display='none';document.getElementById('batchFill').style.width='0%';},2000);}
}

async function onAudioUpload(input){
    if(!input.files.length)return;const f=input.files[0];
    const fd=new FormData();fd.append('audio',f);
    showStatus('transcribeResult','info','📤 上传中...');
    try{
        const r=await fetch('/api/upload-audio',{method:'POST',body:fd});const d=await r.json();
        if(d.audio_url){
            uploadedAudioPath=d.temp_path||'';
            document.getElementById('uploadedAudio').src=d.audio_url;
            document.getElementById('audioFileName').textContent=f.name+' ('+fmtSize(f.size)+')';
            document.getElementById('audioPreview').style.display='block';
            const a=document.getElementById('uploadedAudio');
            a.onloadedmetadata=()=>{document.getElementById('audioInfo').textContent='⏱️ '+a.duration.toFixed(1)+'秒';};
            showStatus('transcribeResult','success','✅ 上传成功');
        }else showStatus('transcribeResult','error','❌ '+(d.error||''));
    }catch(e){showStatus('transcribeResult','error','❌ '+e.message);}
}

function clearAudio(){
    document.getElementById('uploadedAudio').src='';
    document.getElementById('audioPreview').style.display='none';
    document.getElementById('audioFileInput').value='';
    document.getElementById('transcribeResult').style.display='none';
    uploadedAudioPath='';
}

async function saveUploadedAudio(){
    if(!uploadedAudioPath){showStatus('transcribeResult','error','❌ 没有可保存的音频');return;}
    const d=await api('/api/save-audio',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({temp_path:uploadedAudioPath})});
    if(d.success)showStatus('transcribeResult','success','✅ 已保存到 '+d.saved_path);
    else showStatus('transcribeResult','error','❌ '+(d.error||''));
}

async function transcribeUploadedAudio(){
    if(!uploadedAudioPath){showStatus('transcribeResult','error','❌ 请先上传音频');return;}
    showStatus('transcribeResult','info','📝 识别中...');
    const d=await api('/api/transcribe?path='+encodeURIComponent(uploadedAudioPath));
    if(d.text)showStatus('transcribeResult','success','📝 识别结果:\n'+d.text);
    else showStatus('transcribeResult','error','❌ '+(d.error||''));
}

function useAsCloneRef(){
    if(!uploadedAudioPath){showStatus('transcribeResult','error','❌ 请先上传音频');return;}
    showStatus('transcribeResult','info','🎤 已选为克隆参考音频。请切换到支持声音克隆的引擎（如 GPT-SoVITS），启动其 API 后使用。\n参考音频路径: '+uploadedAudioPath);
}

async function onVideoUpload(input){
    if(!input.files.length)return;const f=input.files[0];
    // 先显示视频预览（不上传到服务器，用浏览器本地 URL）
    const url=URL.createObjectURL(f);
    uploadedVideoPath='';
    document.getElementById('uploadedVideo').src=url;
    document.getElementById('videoPreview').style.display='block';
    document.getElementById('videoAudio').style.display='none';
    showStatus('videoStatus','success','✅ 视频已加载: '+f.name+' ('+fmtSize(f.size)+') · 点击「提取音频」开始处理');
    // 存储文件引用以便后续上传
    document.getElementById('videoFileInput')._pendingFile=f;
}

function clearVideo(){
    document.getElementById('uploadedVideo').src='';
    document.getElementById('videoPreview').style.display='none';
    document.getElementById('videoAudio').style.display='none';
    document.getElementById('videoStatus').style.display='none';
    document.getElementById('videoFileInput').value='';
    document.getElementById('videoTranscribeResult').style.display='none';
    uploadedVideoPath='';extractedAudioPath='';
}

async function extractVideoAudio(){
    const input=document.getElementById('videoFileInput');
    const f=input._pendingFile||input.files[0];
    if(!f){showStatus('videoStatus','error','❌ 请先上传视频');return;}
    const fd=new FormData();fd.append('video',f);
    showStatus('videoStatus','info','🎵 提取音频中...');
    try{
        const r=await fetch('/api/extract-audio',{method:'POST',body:fd});const d=await r.json();
        if(d.audio_url){
            extractedAudioPath=d.temp_path||'';
            document.getElementById('extractedAudio').src=d.audio_url;
            document.getElementById('videoAudio').style.display='block';
            showStatus('videoStatus','success','✅ '+d.filename+' ('+d.duration+'秒) · 点击「保存音频」存入文件夹');
        }else showStatus('videoStatus','error','❌ '+(d.error||''));
    }catch(e){showStatus('videoStatus','error','❌ '+e.message);}
}

async function saveExtractedAudio(){
    if(!extractedAudioPath){showStatus('videoStatus','error','❌ 没有可保存的音频');return;}
    const d=await api('/api/save-audio',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({temp_path:extractedAudioPath})});
    if(d.success)showStatus('videoStatus','success','✅ 已保存到 '+d.saved_path);
    else showStatus('videoStatus','error','❌ '+(d.error||''));
}

async function transcribeVideoAudio(){
    if(!extractedAudioPath){showStatus('videoTranscribeResult','error','❌ 请先提取音频');return;}
    showStatus('videoTranscribeResult','info','📝 识别中...');
    const d=await api('/api/transcribe?path='+encodeURIComponent(extractedAudioPath));
    if(d.text)showStatus('videoTranscribeResult','success','📝 识别结果:\n'+d.text);
    else showStatus('videoTranscribeResult','error','❌ '+(d.error||''));
}

function useExtractedAsClone(){
    if(!extractedAudioPath){showStatus('videoTranscribeResult','error','❌ 请先提取音频');return;}
    showStatus('videoTranscribeResult','info','🎤 已选为克隆参考音频。请切换到支持声音克隆的引擎（如 GPT-SoVITS），启动其 API 后使用。\n参考音频路径: '+extractedAudioPath);
}

async function refreshEngines(){
    const d=await api('/api/engines');if(!d.engines)return;
    const g=document.getElementById('engineGrid');g.innerHTML='';
    d.engines.forEach(e=>{
        const c=document.createElement('div');c.className='engine-card';
        const dc=e.available?'on':'off';const st=e.available?'可用':'需启动';
        let extra='';
        if(e.start_command)extra='<div style="font-size:10px;color:var(--text3);margin-top:4px">启动: <code style="background:var(--bg);padding:1px 4px;border-radius:2px">'+e.start_command+'</code></div>';
        if(e.path)extra+='<div style="font-size:10px;color:var(--text3)">'+e.path+'</div>';
        c.innerHTML='<div class="name"><span class="dot '+dc+'"></span>'+e.name+'</div><div class="desc">'+(e.description||'')+'</div><div style="font-size:11px;color:var(--text3)">'+e.type+' | '+st+'</div>'+extra;
        g.appendChild(c);
    });
}

async function scanNewPlugins(){
    const d=await api('/api/scan-plugins');
    if(d.engines){await refreshEngines();const sel=document.getElementById('engine');sel.innerHTML='';d.engines.forEach(e=>{const o=document.createElement('option');o.value=e.id;o.textContent=e.name+(e.available?'':' (需启动)');sel.appendChild(o);});}
}

async function saveSettings(){
    const cfg={proxy:document.getElementById('settingProxy').value,output_dir:document.getElementById('settingOutput').value,default_engine:document.getElementById('settingEngine').value,default_voice:document.getElementById('settingVoice').value};
    const d=await api('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(cfg)});
    showStatus('settingsStatus',d.success?'success':'error',d.success?'✅ 已保存':'❌ '+(d.error||''));
}

function showStatus(id,type,msg){const el=document.getElementById(id);el.style.display='block';el.className='status-bar '+type;el.textContent=msg;}
function fmtSize(b){if(b<1024)return b+' B';if(b<1048576)return(b/1024).toFixed(1)+' KB';return(b/1048576).toFixed(1)+' MB';}

init();
</script>
</body>
</html>"""

# ═══════════════════════════════════════════════════════════════
#  HTTP 服务器
# ═══════════════════════════════════════════════════════════════

class TTSHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log(f"{self.address_string()} - {fmt % args}")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html, status=200):
        body = html.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, filepath, content_type=None):
        filepath = Path(filepath)
        if not filepath.exists():
            self.send_json({"error": "文件不存在"}, 404); return
        if not content_type:
            ext = filepath.suffix.lower()
            types = {'.mp3':'audio/mpeg','.wav':'audio/wav','.ogg':'audio/ogg','.flac':'audio/flac','.m4a':'audio/mp4','.aac':'audio/aac','.mp4':'video/mp4','.webm':'audio/webm'}
            content_type = types.get(ext, 'application/octet-stream')
        size = filepath.stat().st_size
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(size))
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers()
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(65536)
                if not chunk: break
                self.wfile.write(chunk)

    def read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return self.rfile.read(length) if length > 0 else b''

    def read_json(self):
        body = self.read_body()
        if not body: return {}
        try: return json.loads(body.decode('utf-8'))
        except: return {}

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path in ('/', '/index.html'):
            self.send_html(HTML_PAGE)
        elif path == '/api/engines':
            self.send_json({"engines": get_engine_list()})
        elif path == '/api/voices':
            eid = params.get('engine', ['edge-tts'])[0]
            self.send_json({"voices": get_engine(eid).get_voices()})
        elif path == '/api/config':
            self.send_json(config)
        elif path == '/api/switch-engine':
            """切换引擎：异步启动"""
            eid = params.get('engine', ['edge-tts'])[0]
            engine = get_engine(eid)
            result = process_manager.start_engine(eid, engine)
            self.send_json(result)
        elif path == '/api/stop-engine':
            eid = params.get('engine', [''])[0]
            if eid:
                result = process_manager.stop_engine(eid)
                self.send_json(result)
            else:
                self.send_json({"success": False, "message": "未指定引擎"})
        elif path == '/api/engine-status':
            """获取引擎启动状态（前端轮询）"""
            eid = params.get('engine', [''])[0]
            if eid:
                self.send_json(process_manager.get_engine_status(eid))
            else:
                self.send_json(process_manager.get_status())
        elif path == '/api/scan-plugins':
            global engines, local_models
            engines = {"edge-tts": EdgeTTSEngine(config)}
            local_models = scan_local_models()
            for m in local_models:
                engines[m["id"]] = LocalModelEngine(config, m)
            self.send_json({"engines": get_engine_list()})
        elif path == '/api/open-folder':
            fp = params.get('path', [''])[0]
            if fp:
                try:
                    folder = str(Path(fp).parent)
                    subprocess.Popen(['open', folder] if sys.platform == 'darwin' else ['xdg-open', folder])
                    self.send_json({"success": True})
                except: self.send_json({"error": "无法打开"})
            else: self.send_json({"error": "未指定路径"})
        elif path == '/api/discard-audio':
            fp = params.get('path', [''])[0]
            if fp:
                try:
                    p = Path(fp)
                    if p.exists(): p.unlink()
                    log(f"丢弃临时文件: {fp}")
                except: pass
            self.send_json({"success": True})
        elif path == '/api/transcribe':
            fp = params.get('path', [''])[0]
            if fp and Path(fp).exists():
                text = transcribe_audio(fp)
                self.send_json({"text": text})
            else:
                self.send_json({"error": "文件不存在"})
        elif path.startswith('/audio/'):
            self.send_file(OUTPUT_DIR / path[7:])
        elif path.startswith('/temp/'):
            self.send_file(TEMP_DIR / path[6:])
        elif path.startswith('/uploads/'):
            self.send_file(UPLOAD_DIR / path[9:])
        else:
            self.send_json({"error": "Not Found"}, 404)

    def do_POST(self):
        path = self.path

        if path == '/api/generate':
            data = self.read_json()
            text = data.get('text', '').strip()
            if not text:
                self.send_json({"error": "请输入文字"}); return
            eid = data.get('engine', 'edge-tts')
            voice = data.get('voice', 'zh-CN-XiaoyiNeural')
            rate = data.get('rate', '+0%')
            pitch = data.get('pitch', '+0Hz')
            engine = get_engine(eid)
            if not engine.is_available():
                self.send_json({"error": f"{engine.name} 不可用"}); return
            try:
                # ★ 先生成到临时目录，不直接写输出目录
                ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                temp_path = TEMP_DIR / f"{ts}.mp3"
                engine.generate(text, voice, str(temp_path), rate=rate, pitch=pitch)
                dur = get_audio_duration(str(temp_path))
                self.send_json({
                    "audio_url": f"/temp/{temp_path.name}",
                    "temp_path": str(temp_path),
                    "file_path": str(OUTPUT_DIR / temp_path.name),
                    "filename": temp_path.name,
                    "duration": f"{dur:.1f}",
                })
            except Exception as e:
                log(f"生成失败: {e}")
                self.send_json({"error": str(e)})

        elif path == '/api/save-audio':
            """将临时文件保存到输出目录"""
            data = self.read_json()
            temp_path = data.get('temp_path', '')
            if not temp_path or not Path(temp_path).exists():
                self.send_json({"error": "临时文件不存在"}); return
            src = Path(temp_path)
            # 生成有意义的文件名
            now = datetime.now().strftime('%Y%m%d_%H%M%S')
            dst_name = f"TTS_{now}{src.suffix}"
            dst = OUTPUT_DIR / dst_name
            # 避免重名
            counter = 1
            while dst.exists():
                dst = OUTPUT_DIR / f"TTS_{now}_{counter}{src.suffix}"
                counter += 1
            shutil.copy2(str(src), str(dst))
            log(f"保存音频: {src} -> {dst}")
            self.send_json({"success": True, "saved_path": str(dst), "filename": dst_name})

        elif path == '/api/batch-generate':
            data = self.read_json()
            text = data.get('text', '').strip()
            if not text:
                self.send_json({"error": "请输入剧本内容"}); return
            eid = data.get('engine', 'edge-tts')
            engine = get_engine(eid)
            if not engine.is_available():
                self.send_json({"error": f"{engine.name} 不可用"}); return
            voice = data.get('voice', 'zh-CN-XiaoyiNeural')
            rate = data.get('rate', '+0%')
            pitch = data.get('pitch', '+0Hz')
            mc = data.get('max_chars', 200)
            segments = parse_script(text, mc)
            if not segments:
                self.send_json({"error": "无法解析剧本"}); return
            # 批量配音直接输出到文件夹（用户明确要求的）
            out_dir = OUTPUT_DIR / f"批量配音_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            out_dir.mkdir(parents=True, exist_ok=True)
            ok, fail, files = 0, 0, []
            for i, seg in enumerate(segments):
                try:
                    p = out_dir / f"第{i+1:03d}段.mp3"
                    engine.generate(seg, voice, str(p), rate=rate, pitch=pitch)
                    if p.exists() and p.stat().st_size > 0:
                        files.append(p.name); ok += 1
                    else:
                        if p.exists(): p.unlink()
                        fail += 1
                    time.sleep(0.3)
                except Exception as e:
                    log(f"批量第{i+1}段失败: {e}"); fail += 1
            self.send_json({"success": ok, "failed": fail, "files": files, "output_dir": str(out_dir), "results": files})

        elif path == '/api/parse-script':
            data = self.read_json()
            text = data.get('text', '').strip()
            if not text:
                self.send_json({"error": "请输入剧本内容"}); return
            segments = parse_script(text, data.get('max_chars', 200))
            self.send_json({"segments": segments, "total_chars": sum(len(s) for s in segments)})

        elif path == '/api/extract-text':
            ct = self.headers.get('Content-Type', '')
            body = self.read_body()
            if 'multipart/form-data' in ct:
                boundary = ct.split('boundary=')[-1].strip()
                fields, files = parse_multipart(body, boundary)
                if 'file' in files:
                    up = files['file']
                    tmp = UPLOAD_DIR / up['filename']
                    with open(tmp, 'wb') as f: f.write(up['content'])
                    text, error = extract_text(str(tmp))
                    if text:
                        self.send_json({"text": text, "filename": up['filename']})
                    else:
                        self.send_json({"error": error or "无法读取文件内容", "filename": up['filename']})
                else:
                    self.send_json({"error": "未找到文件"})
            else:
                self.send_json({"error": "请用 multipart/form-data"})

        elif path == '/api/extract-audio':
            ct = self.headers.get('Content-Type', '')
            body = self.read_body()
            if 'multipart/form-data' in ct:
                boundary = ct.split('boundary=')[-1].strip()
                fields, files = parse_multipart(body, boundary)
                if 'video' in files:
                    up = files['video']
                    tmp = UPLOAD_DIR / up['filename']
                    with open(tmp, 'wb') as f: f.write(up['content'])
                    try:
                        # ★ 提取到临时目录，不直接存输出目录
                        ap = extract_audio_from_video(str(tmp))
                        dur = get_audio_duration(ap)
                        an = Path(ap).name
                        self.send_json({"audio_url": f"/temp/{an}", "temp_path": ap, "filename": an, "duration": f"{dur:.1f}"})
                    except Exception as e:
                        self.send_json({"error": str(e)})
                else:
                    self.send_json({"error": "未找到视频"})
            else:
                self.send_json({"error": "请用 multipart/form-data"})

        elif path == '/api/upload-audio':
            """上传音频到临时目录用于预览/克隆/识别"""
            ct = self.headers.get('Content-Type', '')
            body = self.read_body()
            if 'multipart/form-data' in ct:
                boundary = ct.split('boundary=')[-1].strip()
                fields, files = parse_multipart(body, boundary)
                if 'audio' in files:
                    up = files['audio']
                    # 保存到临时目录
                    tmp = TEMP_DIR / f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{Path(up['filename']).suffix}"
                    with open(tmp, 'wb') as f: f.write(up['content'])
                    self.send_json({"audio_url": f"/temp/{tmp.name}", "temp_path": str(tmp), "filename": up['filename']})
                else:
                    self.send_json({"error": "未找到音频"})
            else:
                self.send_json({"error": "请用 multipart/form-data"})

        elif path == '/api/config':
            data = self.read_json()
            for k in ['proxy', 'output_dir', 'default_engine', 'default_voice']:
                if k in data: config[k] = data[k]
            save_config(config)
            for e in engines.values(): e.proxy = config.get('proxy', '')
            self.send_json({"success": True})

        else:
            self.send_json({"error": "Not Found"}, 404)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    port = config.get("port", 7860)
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     🎙️  AI-TTS Studio  全球TTS一体化工作台  v3.3  🎙️      ║
╚══════════════════════════════════════════════════════════════╝

  📍 http://localhost:{port}
  📁 输出: {OUTPUT_DIR}
  📂 临时: {TEMP_DIR}（未保存的音频）
  🔌 引擎: {len(engines)} 个（含 {len(local_models)} 个本地模型）

  按 Ctrl+C 停止
""")
    for key, engine in engines.items():
        s = "🟢" if engine.is_available() else "🔴"
        print(f"  {s} {engine.name} - {engine.description[:50]}")
    print()
    server = ThreadedHTTPServer(('127.0.0.1', port), TTSHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 正在关闭所有模型进程...")
        process_manager.shutdown_all()
        print("👋 已停止")
        server.server_close()


if __name__ == "__main__":
    main()
