#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║        🎙️  AI-TTS-Studio  全球TTS一体化工作台  🎙️          ║
║     暗色科技风 · Gradio WebUI · 模块化插件系统              ║
║     支持 Edge-TTS / GPT-SoVITS / Qwen3-TTS / IndexTTS2     ║
╚══════════════════════════════════════════════════════════════╝

启动: python3 app.py
访问: http://localhost:7860
"""

import os
import sys
import json
import time
import shutil
import subprocess
import tempfile
import re
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#  配置管理
# ═══════════════════════════════════════════════════════════════

CONFIG_DIR = Path.home() / ".ai-tts-studio"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_OUTPUT = Path.home() / "Downloads" / "最终输出" / "音频文件"
TOOLKIT_DIR = Path.home() / "Documents" / "AI-TTS-Toolkit"

DEFAULT_CONFIG = {
    "proxy": "http://127.0.0.1:7890",
    "output_dir": str(DEFAULT_OUTPUT),
    "default_engine": "edge-tts",
    "default_voice": "zh-CN-XiaoyiNeural",
    "default_rate": "+0%",
    "default_pitch": "+0Hz",
    "engines": {
        "edge-tts": {
            "name": "微软Edge语音",
            "type": "cloud",
            "installed": True,
            "path": "",
        },
        "gpt-sovits": {
            "name": "GPT-SoVITS",
            "type": "local",
            "installed": False,
            "path": str(TOOLKIT_DIR / "GPT-SoVITS"),
        },
        "qwen3-tts": {
            "name": "Qwen3-TTS",
            "type": "local",
            "installed": False,
            "path": str(TOOLKIT_DIR / "Qwen3-TTS"),
        },
        "indextts2": {
            "name": "IndexTTS2",
            "type": "local",
            "installed": False,
            "path": str(TOOLKIT_DIR / "IndexTTS2"),
        },
    },
}


def load_config():
    """加载配置"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            # 合并默认值（防止新增字段丢失）
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    """保存配置"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  TTS 引擎抽象层
# ═══════════════════════════════════════════════════════════════

class TTSEngine:
    """TTS 引擎基类"""
    name = "base"
    engine_type = "base"

    def __init__(self, config):
        self.config = config
        self.proxy = config.get("proxy", "")

    def generate(self, text, voice, output_path, **kwargs):
        raise NotImplementedError

    def get_voices(self):
        return []

    def is_available(self):
        return False


class EdgeTTSEngine(TTSEngine):
    """微软 Edge-TTS 引擎"""
    name = "Edge-TTS"
    engine_type = "cloud"

    def __init__(self, config):
        super().__init__(config)
        self._voices_cache = None

    def is_available(self):
        return shutil.which("edge-tts") is not None

    def generate(self, text, voice, output_path, rate="+0%", pitch="+0Hz", **kwargs):
        cmd = ["edge-tts"]
        if self.proxy:
            cmd.extend(["--proxy", self.proxy])
        cmd.extend([
            "--voice", voice or "zh-CN-XiaoyiNeural",
            "--text", text,
            "--rate", rate,
            "--pitch", pitch,
            "--write-media", str(output_path),
        ])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"Edge-TTS 失败: {result.stderr}")
        return str(output_path)

    def get_voices(self):
        if self._voices_cache:
            return self._voices_cache
        try:
            cmd = ["edge-tts", "--list-voices"]
            if self.proxy:
                cmd.extend(["--proxy", self.proxy])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            voices = []
            for line in result.stdout.strip().split('\n'):
                if 'Name:' in line:
                    name = line.split('Name:')[1].strip().split()[0]
                    voices.append(name)
            self._voices_cache = voices
            return voices
        except:
            return ["zh-CN-XiaoyiNeural", "zh-CN-YunyangNeural", "zh-CN-XiaoxuanNeural",
                    "zh-CN-YunjianNeural", "zh-CN-XiaomengNeural", "zh-CN-XiaomoNeural",
                    "zh-CN-YunxiNeural", "zh-CN-YunxiaNeural",
                    "zh-CN-liaoning-XiaobeiNeural", "zh-CN-shaanxi-XiaoniNeural"]


class GPTSoVITSEngine(TTSEngine):
    """GPT-SoVITS 引擎"""
    name = "GPT-SoVITS"
    engine_type = "local"

    def is_available(self):
        path = Path(self.config.get("engines", {}).get("gpt-sovits", {}).get("path", ""))
        return path.exists() and (path / "GPT_SoVITS").exists()

    def generate(self, text, voice, output_path, **kwargs):
        # TODO: 调用 GPT-SoVITS API
        raise NotImplementedError("GPT-SoVITS 接口开发中，请先用 Edge-TTS")

    def get_voices(self):
        return ["请参考音色模型"]


class Qwen3TTSEngine(TTSEngine):
    """Qwen3-TTS 引擎"""
    name = "Qwen3-TTS"
    engine_type = "local"

    def is_available(self):
        path = Path(self.config.get("engines", {}).get("qwen3-tts", {}).get("path", ""))
        return path.exists() and (path / "qwen_tts").exists()

    def generate(self, text, voice, output_path, **kwargs):
        raise NotImplementedError("Qwen3-TTS 接口开发中，请先用 Edge-TTS")

    def get_voices(self):
        return ["请参考音色模型"]


class IndexTTS2Engine(TTSEngine):
    """IndexTTS2 引擎"""
    name = "IndexTTS2"
    engine_type = "local"

    def is_available(self):
        path = Path(self.config.get("engines", {}).get("indextts2", {}).get("path", ""))
        return path.exists()

    def generate(self, text, voice, output_path, **kwargs):
        raise NotImplementedError("IndexTTS2 接口开发中，请先用 Edge-TTS")

    def get_voices(self):
        return ["请参考音色模型"]


# ═══════════════════════════════════════════════════════════════
#  剧本解析器
# ═══════════════════════════════════════════════════════════════

def parse_script(text, max_chars=200):
    """将剧本文本按句子分段，每段不超过 max_chars 字"""
    # 按换行、句号、问号、感叹号分段
    segments = re.split(r'(?<=[。！？\n])', text.strip())
    result = []
    current = ""
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        if len(current) + len(seg) > max_chars and current:
            result.append(current.strip())
            current = seg
        else:
            current += seg
    if current.strip():
        result.append(current.strip())
    return result


def extract_audio_from_video(video_path, output_dir):
    """从视频中提取音频"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    cmd = ["ffmpeg", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le",
           "-ar", "44100", "-ac", "1", str(output_path), "-y"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"音频提取失败: {result.stderr[-500:]}")
    return str(output_path)


# ═══════════════════════════════════════════════════════════════
#  Gradio WebUI
# ═══════════════════════════════════════════════════════════════

def create_ui():
    import gradio as gr

    config = load_config()

    # 初始化引擎
    engines = {
        "edge-tts": EdgeTTSEngine(config),
        "gpt-sovits": GPTSoVITSEngine(config),
        "qwen3-tts": Qwen3TTSEngine(config),
        "indextts2": IndexTTS2Engine(config),
    }

    # 确保输出目录存在
    Path(config["output_dir"]).mkdir(parents=True, exist_ok=True)

    # ─── 自定义暗色主题 CSS ───
    DARK_CSS = """
    /* 全局暗色主题 */
    .gradio-container {
        background: #0a0a0f !important;
        color: #e0e0e0 !important;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .gr-panel, .gr-box, .gr-form, .gr-input-label, .gr-checkbox-label {
        background: #12121a !important;
        border: 1px solid #2a2a3a !important;
        color: #e0e0e0 !important;
        border-radius: 12px !important;
    }
    .gr-input, .gr-textbox, .gr-dropdown, .gr-number {
        background: #1a1a2e !important;
        border: 1px solid #333355 !important;
        color: #e0e0e0 !important;
        border-radius: 8px !important;
    }
    .gr-input:focus, .gr-textbox:focus, .gr-dropdown:focus {
        border-color: #6c63ff !important;
        box-shadow: 0 0 0 2px rgba(108, 99, 255, 0.2) !important;
    }
    .gr-button, .gr-button-primary {
        background: linear-gradient(135deg, #6c63ff, #4834d4) !important;
        border: none !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
    }
    .gr-button:hover, .gr-button-primary:hover {
        background: linear-gradient(135deg, #7c74ff, #5844e4) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(108, 99, 255, 0.4) !important;
    }
    .gr-button-secondary {
        background: #1a1a2e !important;
        border: 1px solid #333355 !important;
        color: #a0a0c0 !important;
        border-radius: 8px !important;
    }
    .gr-tab-nav {
        background: #0e0e18 !important;
        border-bottom: 1px solid #2a2a3a !important;
    }
    .gr-tab {
        background: transparent !important;
        color: #8080a0 !important;
        border: none !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
    }
    .gr-tab-selected {
        background: #12121a !important;
        color: #6c63ff !important;
        border-bottom: 2px solid #6c63ff !important;
    }
    .gr-tab:hover {
        color: #a0a0ff !important;
        background: #1a1a2e !important;
    }
    .gr-accordion {
        background: #12121a !important;
        border: 1px solid #2a2a3a !important;
        border-radius: 12px !important;
    }
    .gr-accordion-header {
        background: #1a1a2e !important;
        color: #e0e0e0 !important;
        border-radius: 12px !important;
    }
    .gr-slider-container {
        background: #1a1a2e !important;
    }
    .gr-markdown {
        color: #c0c0d0 !important;
    }
    .gr-markdown h1, .gr-markdown h2, .gr-markdown h3 {
        color: #e0e0ff !important;
    }
    /* 标题样式 */
    .main-title {
        text-align: center;
        padding: 20px 0 10px;
    }
    .main-title h1 {
        font-size: 28px !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #6c63ff, #00d2ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 !important;
    }
    .main-title p {
        color: #6060a0;
        font-size: 14px;
        margin: 5px 0 0;
    }
    /* 状态指示器 */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .status-dot.online { background: #00ff88; box-shadow: 0 0 6px #00ff88; }
    .status-dot.offline { background: #ff4444; box-shadow: 0 0 6px #ff4444; }
    /* 进度条 */
    .gr-progress {
        background: #1a1a2e !important;
        border-radius: 8px !important;
    }
    .gr-progress-bar {
        background: linear-gradient(90deg, #6c63ff, #00d2ff) !important;
        border-radius: 8px !important;
    }
    /* 文件列表 */
    .file-list {
        background: #1a1a2e;
        border: 1px solid #333355;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        font-size: 13px;
    }
    .file-list .file-item {
        padding: 6px 10px;
        border-bottom: 1px solid #2a2a3a;
        display: flex;
        justify-content: space-between;
    }
    .file-list .file-item:last-child {
        border-bottom: none;
    }
    """

    # ─── 语音合成 Tab ───
    def synthesize_speech(text, voice, rate, pitch, engine_name):
        if not text.strip():
            return None, "❌ 请输入要转换的文字"
        if len(text) > 5000:
            return None, "⚠️ 文字过长（超过5000字），请分段处理"

        engine = engines.get(engine_name, engines["edge-tts"])
        if not engine.is_available():
            return None, f"❌ {engine.name} 不可用，请检查安装"

        output_dir = Path(config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f"{timestamp}.mp3"

        try:
            engine.generate(text, voice, str(output_path), rate=rate, pitch=pitch)
            duration = get_audio_duration(str(output_path))
            return str(output_path), f"✅ 生成成功！\n📁 {output_path.name}\n⏱️ 时长: {duration:.1f}秒\n📊 字数: {len(text)}"
        except Exception as e:
            return None, f"❌ 生成失败: {str(e)}"

    def get_audio_duration(file_path):
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", file_path],
                capture_output=True, text=True, timeout=10
            )
            return float(result.stdout.strip())
        except:
            return 0.0

    def refresh_voices(engine_name):
        engine = engines.get(engine_name, engines["edge-tts"])
        voices = engine.get_voices()
        return gr.update(choices=voices, value=voices[0] if voices else None)

    def check_engine_status():
        status = {}
        for name, engine in engines.items():
            available = engine.is_available()
            status[name] = "🟢 在线" if available else "🔴 离线"
        return "\n".join([f"**{engines[k].name}**: {v}" for k, v in status.items()])

    # ─── 剧本配音 Tab ───
    def parse_and_preview(script_text, max_chars):
        if not script_text.strip():
            return "", "❌ 请输入剧本内容"
        segments = parse_script(script_text, max_chars)
        preview = "\n".join([f"【第{i+1}段】({len(s)}字)\n{s}\n" for i, s in enumerate(segments)])
        warning = ""
        if len(segments) > 10:
            warning = f"\n⚠️ 共 {len(segments)} 段，配音可能需要较长时间，建议分批处理"
        return preview, f"📋 剧本解析完成\n共 {len(segments)} 段，{sum(len(s) for s in segments)} 字{warning}"

    def batch_synthesize(script_text, voice, rate, pitch, engine_name, max_chars, progress=gr.Progress()):
        if not script_text.strip():
            return None, "❌ 请输入剧本内容"

        segments = parse_script(script_text, max_chars)
        if not segments:
            return None, "❌ 无法解析剧本"

        engine = engines.get(engine_name, engines["edge-tts"])
        if not engine.is_available():
            return None, f"❌ {engine.name} 不可用"

        output_dir = Path(config["output_dir"]) / f"剧本配音_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        failed = []
        for i, seg in enumerate(progress.tqdm(segments, desc="配音进度")):
            try:
                output_path = output_dir / f"第{i+1:03d}段.mp3"
                engine.generate(seg, voice, str(output_path), rate=rate, pitch=pitch)
                results.append(str(output_path))
                time.sleep(0.3)  # 避免频率限制
            except Exception as e:
                failed.append(f"第{i+1}段: {str(e)}")

        # 生成文件列表
        file_list = "\n".join([f"✅ {Path(r).name}" for r in results])
        if failed:
            file_list += "\n\n❌ 失败:\n" + "\n".join(failed)

        summary = f"📋 配音完成\n✅ 成功: {len(results)} 段\n❌ 失败: {len(failed)} 段\n📁 输出: {output_dir}"
        return file_list, summary

    # ─── 视频配音 Tab ───
    def process_video(video_path, voice, rate, pitch, engine_name, progress=gr.Progress()):
        if not video_path:
            return None, "❌ 请上传视频文件"

        engine = engines.get(engine_name, engines["edge-tts"])
        if not engine.is_available():
            return None, f"❌ {engine.name} 不可用"

        try:
            # 1. 提取音频
            progress(0, desc="提取音频中...")
            output_dir = Path(config["output_dir"]) / f"视频配音_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_dir.mkdir(parents=True, exist_ok=True)
            audio_path = extract_audio_from_video(str(video_path), output_dir)

            # 2. 返回提取的音频
            progress(1, desc="完成")
            return audio_path, f"✅ 音频提取成功\n📁 {audio_path}\n\n💡 提示：视频配音需要语音识别(ASR)功能，正在开发中。\n当前可手动输入台词进行配音。"
        except Exception as e:
            return None, f"❌ 处理失败: {str(e)}"

    # ─── 设置 Tab ───
    def save_settings(proxy, output_dir, default_engine, default_voice):
        config["proxy"] = proxy
        config["output_dir"] = output_dir
        config["default_engine"] = default_engine
        config["default_voice"] = default_voice
        save_config(config)
        # 更新引擎代理
        for engine in engines.values():
            engine.proxy = proxy
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return "✅ 设置已保存"

    # ─── 构建 UI ───
    with gr.Blocks(
        title="🎙️ AI-TTS Studio",
        theme=gr.themes.Soft(),
        css=DARK_CSS,
    ) as app:

        # 标题
        gr.HTML("""
        <div class="main-title">
            <h1>🎙️ AI-TTS Studio</h1>
            <p>全球TTS一体化工作台 · 暗色科技风 · 模块化插件系统</p>
        </div>
        """)

        with gr.Tabs():
            # ═══ Tab 1: 语音合成 ═══
            with gr.Tab("🎙️ 语音合成"):
                with gr.Row():
                    with gr.Column(scale=2):
                        engine_dd = gr.Dropdown(
                            choices=["edge-tts", "gpt-sovits", "qwen3-tts", "indextts2"],
                            value=config["default_engine"],
                            label="🤖 TTS 引擎",
                            interactive=True,
                        )
                        voice_dd = gr.Dropdown(
                            choices=engines["edge-tts"].get_voices(),
                            value=config["default_voice"],
                            label="🗣️ 声音",
                            interactive=True,
                            filterable=True,
                        )
                        with gr.Row():
                            rate_slider = gr.Textbox(
                                value=config["default_rate"],
                                label="⚡ 语速",
                                placeholder="+20% / -10%",
                            )
                            pitch_slider = gr.Textbox(
                                value=config["default_pitch"],
                                label="🎵 音调",
                                placeholder="+5Hz / -10Hz",
                            )
                        text_input = gr.Textbox(
                            label="📝 输入文字",
                            placeholder="在这里输入要转换的文字...",
                            lines=6,
                            max_lines=20,
                        )
                        with gr.Row():
                            gen_btn = gr.Button("🔊 生成语音", variant="primary", size="lg")
                            refresh_btn = gr.Button("🔄 刷新声音列表")

                    with gr.Column(scale=1):
                        audio_output = gr.Audio(label="🎧 生成的语音", type="filepath")
                        status_output = gr.Textbox(label="📊 状态", lines=6, interactive=False)

                # 声音推荐
                gr.Markdown("""
                ### 🎭 推荐中文声音
                | 声音 | 特点 | 适用场景 |
                |------|------|----------|
                | XiaoyiNeural | 年轻女声 | 日常/短视频 |
                | YunyangNeural | 成熟男声 | 影视解说/纪录片 |
                | XiaoxuanNeural | 甜美女声 | 广告/有声书 |
                | YunjianNeural | 浑厚男声 | 游戏/预告片 |
                | XiaomengNeural | 萌系女声 | 动画/儿童 |
                | YunxiNeural | 阳光男声 | 对话/综艺 |
                | liaoning-XiaobeiNeural | 东北话男声 | 搞笑/段子 |
                """)

                # 事件绑定
                engine_dd.change(fn=refresh_voices, inputs=[engine_dd], outputs=[voice_dd])
                refresh_btn.click(fn=refresh_voices, inputs=[engine_dd], outputs=[voice_dd])
                gen_btn.click(
                    fn=synthesize_speech,
                    inputs=[text_input, voice_dd, rate_slider, pitch_slider, engine_dd],
                    outputs=[audio_output, status_output],
                )

            # ═══ Tab 2: 剧本配音 ═══
            with gr.Tab("📜 剧本配音"):
                gr.Markdown("""
                ### 📜 批量剧本配音
                粘贴或上传剧本，自动分段配音。支持长文本自动分段处理。
                """)

                with gr.Row():
                    with gr.Column(scale=2):
                        script_input = gr.Textbox(
                            label="📝 剧本内容",
                            placeholder="在这里粘贴剧本...\n\n支持自动分段（按句号、换行等）",
                            lines=12,
                        )
                        with gr.Row():
                            max_chars_input = gr.Number(
                                value=200,
                                label="📏 每段最大字数",
                                minimum=50,
                                maximum=1000,
                            )
                            parse_btn = gr.Button("📋 解析预览", variant="secondary")
                        preview_output = gr.Textbox(
                            label="👁️ 分段预览",
                            lines=8,
                            interactive=False,
                        )
                        batch_btn = gr.Button("🚀 开始批量配音", variant="primary", size="lg")

                    with gr.Column(scale=1):
                        batch_status = gr.Textbox(
                            label="📊 配音进度",
                            lines=10,
                            interactive=False,
                        )

                parse_btn.click(
                    fn=parse_and_preview,
                    inputs=[script_input, max_chars_input],
                    outputs=[preview_output, batch_status],
                )
                batch_btn.click(
                    fn=batch_synthesize,
                    inputs=[script_input, voice_dd, rate_slider, pitch_slider, engine_dd, max_chars_input],
                    outputs=[preview_output, batch_status],
                )

            # ═══ Tab 3: 视频配音 ═══
            with gr.Tab("🎬 视频配音"):
                gr.Markdown("""
                ### 🎬 视频音频提取 & 配音
                上传视频文件，提取音频，为后续配音做准备。
                """)

                with gr.Row():
                    with gr.Column():
                        video_input = gr.Video(label="📹 上传视频")
                        extract_btn = gr.Button("🎵 提取音频", variant="primary")
                    with gr.Column():
                        extracted_audio = gr.Audio(label="🎧 提取的音频", type="filepath")
                        video_status = gr.Textbox(
                            label="📊 状态",
                            lines=6,
                            interactive=False,
                        )

                extract_btn.click(
                    fn=process_video,
                    inputs=[video_input, voice_dd, rate_slider, pitch_slider, engine_dd],
                    outputs=[extracted_audio, video_status],
                )

            # ═══ Tab 4: 模型管理 ═══
            with gr.Tab("🔌 模型管理"):
                gr.Markdown("### 🔌 已安装的 TTS 引擎")
                status_md = gr.Markdown(check_engine_status())
                refresh_status_btn = gr.Button("🔄 刷新状态")
                refresh_status_btn.click(fn=lambda: gr.update(value=check_engine_status()), outputs=[status_md])

                gr.Markdown("""
                ### 📦 引擎路径配置
                """)
                engine_paths = []
                for name, info in config["engines"].items():
                    with gr.Row():
                        gr.Markdown(f"**{info['name']}** ({info['type']})")
                    path_input = gr.Textbox(
                        value=info["path"],
                        label=f"路径",
                        interactive=True,
                    )
                    engine_paths.append((name, path_input))

                gr.Markdown("""
                ---
                ### 🔮 未来可扩展的引擎
                - CosyVoice（阿里通义语音，18种方言）
                - Fish-Speech（50种语言，情感标签）
                - Bark（Suno出品，音乐生成）
                - ChatTTS（口语化天花板）
                - VALL-E（Meta，环境音效）
                - So-VITS-SVC（歌声转换）
                """)

            # ═══ Tab 5: 设置 ═══
            with gr.Tab("⚙️ 设置"):
                with gr.Column():
                    proxy_input = gr.Textbox(
                        label="🌐 代理地址",
                        value=config["proxy"],
                        placeholder="http://127.0.0.1:7890",
                    )
                    output_dir_input = gr.Textbox(
                        label="📁 默认输出目录",
                        value=config["output_dir"],
                    )
                    default_engine_input = gr.Dropdown(
                        label="🤖 默认引擎",
                        choices=["edge-tts", "gpt-sovits", "qwen3-tts", "indextts2"],
                        value=config["default_engine"],
                    )
                    default_voice_input = gr.Textbox(
                        label="🗣️ 默认声音",
                        value=config["default_voice"],
                    )
                    save_btn = gr.Button("💾 保存设置", variant="primary")
                    settings_status = gr.Textbox(label="状态", interactive=False)

                save_btn.click(
                    fn=save_settings,
                    inputs=[proxy_input, output_dir_input, default_engine_input, default_voice_input],
                    outputs=[settings_status],
                )

    return app


# ═══════════════════════════════════════════════════════════════
#  启动
# ═══════════════════════════════════════════════════════════════

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║        🎙️  AI-TTS Studio  全球TTS一体化工作台  🎙️          ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # 检查 gradio 是否安装
    try:
        import gradio as gr
    except ImportError:
        print("⚠️  Gradio 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "gradio"],
                       capture_output=True)
        import gradio as gr

    # 检查 ffmpeg
    if not shutil.which("ffmpeg"):
        print("⚠️  FFmpeg 未安装（视频功能需要），建议: brew install ffmpeg")

    app = create_ui()
    print("🚀 启动 WebUI...")
    print("📍 访问地址: http://localhost:7860")
    print("   按 Ctrl+C 停止\n")

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True,
        favicon_path=None,
    )


if __name__ == "__main__":
    main()
