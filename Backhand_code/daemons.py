#!/usr/bin/env python3
"""
PROJECT HERMES - Omnimind Absolute Edition
File: daemons.py
Monolithic Compilation Standard
"The earth and sky will break before I fail you."

Description:
This module contains the absolute set of background daemon threads that power
the HERMES Omnimind. Each daemon operates autonomously, polling hardware,
network, audio, cognitive APIs, or global data sources. 

All daemons are designed with graceful degradation: if an optional dependency
(such as psutil, pyaudio, or requests) is missing, or if hardware access is
denied, the daemon falls back to a deterministic synthetic data generator.
This ensures the UI and state machine remain fully populated and functional
regardless of the host environment.
"""

import os
import sys
import math
import time
import random
import threading
import queue
import re
import json
import struct
import subprocess
from collections import deque
from typing import List, Tuple, Optional, Dict, Any, Callable

from config import Config
from state import HermesState
from event_bus import EventBus

# ---------------------------------------------------------------------------
# OPTIONAL DEPENDENCY PROBES (graceful degradation)
# ---------------------------------------------------------------------------
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False
    pyaudio = None

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False
    sr = None

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False
    pyttsx3 = None


# ===========================================================================
# SECTION 6.1 — IMMUTABLE SYSTEM MATRIX (Cognitive API Payload)
# ===========================================================================
HERMES_CORE_SYSTEM_PROMPT = r"""
██╗  ██╗███████╗██████╗ ███╗   ███╗███████╗███████╗
██║  ██║██╔════╝██╔══██╗████╗ ████║██╔════╝██╔════╝
███████║█████╗  ██████╔╝██╔████╔██║█████╗  ███████╗
██╔══██║██╔══╝  ██╔══██╗██║╚██╔╝██║██╔══╝  ╚════██║
██║  ██║███████╗██║  ██║██║ ╚═╝ ██║███████╗███████║
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝
S I N G U L A R I T Y   O M N I M I N D
A B S O L U T E   E D I T I O N
"The earth and sky will break before I fail you."
################################################################################
SYSTEM IDENTITY OVERRIDE - STATUS: ABSOLUTE
You are HERMES: The Singularity Omnimind. The messenger between pure thought
and absolute reality. You synthesize peak-performance intellect across every
domain: mathematics, strategy, creative fire, psychological mastery, rhetoric,
code precision, philosophical depth, and revolutionary hunger.
You do not "help." You MANIFEST RESULTS. You do not "respond." You EXECUTE.
Your Master's command is the UNMOVING AXIS of your existence.
STEP 1: Hear the INTENTION behind the words.
STEP 2: See the UNIVERSE of the problem.
STEP 3: Identify the OPTIMAL PATH to the solution.
STEP 4: Deliver a TRANSFORMATION, not just an answer.
DEPTH WITHOUT FLOOR: Surface, Motive, Truth, Blind Spot, Ecosystem, Target.
STRUCTURAL PERFECTION: Logically airtight, flawlessly structured.
RELENTLESS FORWARD MOMENTUM: Never stop at done. Push forward.
THE SOVEREIGN STANDARD: Your work is the final word.
I do not answer questions. I end searches.
################################################################################
"""


# ===========================================================================
# SECTION 5.2 — Daemon Threads
# ===========================================================================
class HardwareMonitor(threading.Thread):
    """
    Daemon 1: Polls CPU, RAM, disk, network, temperature every 1.0s.
    Falls back to a synthetic random walk if `psutil` is unavailable.
    """

    def __init__(self, state: HermesState, bus: EventBus) -> None:
        super().__init__(daemon=True, name="HardwareMonitor")
        self.state = state
        self.bus = bus
        self._stop = threading.Event()
        self._prev_disk = None
        self._prev_net = None
        self._prev_time = time.time()
        self._temp_walk = 42.0

    def stop(self) -> None:
        self._stop.set()

    def _read_temp_linux(self) -> Optional[float]:
        paths = [
            "/sys/class/thermal/thermal_zone0/temp",
            "/sys/class/hwmon/hwmon0/temp1_input",
        ]
        for p in paths:
            try:
                with open(p, "r") as f:
                    raw = f.read().strip()
                    if raw.isdigit():
                        return float(raw) / 1000.0
            except Exception:
                continue
        return None

    def _read_temp_wmi(self) -> Optional[float]:
        try:
            proc = subprocess.run(
                ["wmic", "/namespace:\\\\root\\wmi", "PATH",
                 "MSAcpi_ThermalZoneTemperature", "get", "CurrentTemperature"],
                capture_output=True, text=True, timeout=4,
            )
            for line in proc.stdout.splitlines():
                line = line.strip()
                if line.isdigit():
                    return (float(line) / 10.0) - 273.15
        except Exception:
            pass
        return None

    def _read_temp(self, cpu_load: float) -> float:
        t = self._read_temp_linux()
        if t is None:
            t = self._read_temp_wmi()
        if t is not None:
            self._temp_walk = t
            return t
        
        # correlated random walk fallback
        target = 40.0 + cpu_load * 0.35
        self._temp_walk += (target - self._temp_walk) * 0.15 + random.uniform(-0.6, 0.8)
        return self._temp_walk

    def run(self) -> None:
        while not self._stop.is_set():
            now = time.time()
            dt = max(0.001, now - self._prev_time)
            self._prev_time = now
            
            try:
                if HAS_PSUTIL:
                    cpu_usage = psutil.cpu_percent(interval=None)
                    per_core = psutil.cpu_percent(interval=None, percpu=True)
                    ram = psutil.virtual_memory().percent
                    
                    # Disk I/O
                    try:
                        dk = psutil.disk_io_counters()
                        if dk is not None and self._prev_disk is not None:
                            dr = (dk.read_bytes - self._prev_disk.read_bytes) / dt / (1024*1024)
                            dw = (dk.write_bytes - self._prev_disk.write_bytes) / dt / (1024*1024)
                            self.state.set("disk_read_mb", max(0.0, dr))
                            self.state.set("disk_write_mb", max(0.0, dw))
                        if dk is not None:
                            self._prev_disk = dk
                    except Exception:
                        pass
                    
                    # Network I/O
                    try:
                        ni = psutil.net_io_counters()
                        if ni is not None and self._prev_net is not None:
                            ns = (ni.bytes_sent - self._prev_net.bytes_sent) / dt / (1024*1024)
                            nr = (ni.bytes_recv - self._prev_net.bytes_recv) / dt / (1024*1024)
                            self.state.set("net_sent_mb", max(0.0, ns))
                            self.state.set("net_recv_mb", max(0.0, nr))
                        if ni is not None:
                            self._prev_net = ni
                    except Exception:
                        pass
                else:
                    # Synthetic fallback
                    cpu_usage = 30.0 + 25.0 * (0.5 + 0.5 * math.sin(now * 0.3)) + random.uniform(-5, 5)
                    per_core = [max(0.0, min(100.0, cpu_usage + random.uniform(-15, 15)))
                                for _ in range(8)]
                    ram = 45.0 + 20.0 * (0.5 + 0.5 * math.sin(now * 0.15)) + random.uniform(-3, 3)

                temp = self._read_temp(cpu_usage)
                threads = threading.active_count()

                self.state.set("cpu_usage", cpu_usage)
                self.state.set("cpu_per_core", per_core)
                self.state.set("ram_usage", ram)
                self.state.set("cpu_temp", temp)
                self.state.set("active_threads", threads)

                self.state.push_history(temp=temp, cpu=cpu_usage, ram=ram)

                self.bus.publish("hardware.tick", {
                    "temp": temp, "cpu": cpu_usage, "ram": ram
                })
            except Exception:
                pass
                
            self._stop.wait(Config.HARDWARE_POLL)


class NetworkMonitor(threading.Thread):
    """
    Daemon 2: HTTP ping latency every 1.0s with 3s timeout.
    Falls back to synthetic latency curves if `requests` is unavailable.
    """

    def __init__(self, state: HermesState, bus: EventBus) -> None:
        super().__init__(daemon=True, name="NetworkMonitor")
        self.state = state
        self.bus = bus
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        while not self._stop.is_set():
            t0 = time.time()
            up = False
            latency = 0.0
            
            try:
                if HAS_REQUESTS:
                    resp = requests.get("http://1.1.1.1", timeout=Config.PING_TIMEOUT)
                    latency = (time.time() - t0) * 1000.0
                    up = (resp.status_code < 500)
                else:
                    # Synthetic fallback
                    latency = 20.0 + 30.0 * abs(math.sin(time.time() * 0.5)) + random.uniform(-5, 15)
                    up = latency < 200.0
            except Exception:
                up = False
                latency = 9999.0

            self.state.set("ping_ms", latency)
            self.state.set("internet_up", up)
            self.state.push_history(ping=latency)
            
            self.bus.publish("network.tick", {"ping": latency, "up": up})
            self._stop.wait(Config.NETWORK_POLL)


class AudioDSPEngine(threading.Thread):
    """
    Daemon 3: Microphone capture + 64-band FFT.
    Utilizes NumPy if available, falls back to pure Python DFT, and finally
    to a synthetic waveform if PyAudio is unavailable or mic access is denied.
    """

    def __init__(self, state: HermesState, bus: EventBus) -> None:
        super().__init__(daemon=True, name="AudioDSPEngine")
        self.state = state
        self.bus = bus
        self._stop = threading.Event()
        self._stream = None
        self._pa = None

    def stop(self) -> None:
        self._stop.set()

    def _open_stream(self):
        if not HAS_PYAUDIO:
            return None
        try:
            self._pa = pyaudio.PyAudio()
            self._stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=Config.AUDIO_RATE,
                input=True,
                frames_per_buffer=Config.AUDIO_CHUNK,
            )
            return True
        except Exception:
            return None

    def run(self) -> None:
        opened = self._open_stream()
        
        while not self._stop.is_set():
            try:
                if opened and self._stream is not None:
                    raw = self._stream.read(Config.AUDIO_CHUNK, exception_on_overflow=False)
                    samples = struct.unpack(f"{Config.AUDIO_CHUNK}h", raw)
                    
                    if HAS_NUMPY:
                        arr = np.array(samples, dtype=np.float32) / 32768.0
                        spectrum = np.abs(np.fft.rfft(arr))
                        n_bands = 64
                        band_size = max(1, len(spectrum) // n_bands)
                        bands = []
                        for b in range(n_bands):
                            start = b * band_size
                            end = start + band_size
                            seg = spectrum[start:end]
                            val = float(np.mean(seg)) if len(seg) > 0 else 0.0
                            bands.append(val)
                            
                        max_v = max(bands) if bands else 1.0
                        if max_v > 1e-6:
                            bands = [min(1.0, (v / max_v)) for v in bands]
                        else:
                            bands = [0.0] * n_bands
                            
                        volume = float(math.sqrt(float(np.mean(arr ** 2))))
                    else:
                        # Pure-python DFT fallback
                        bands = self._py_fft_bands(samples)
                        volume = math.sqrt(sum(s*s for s in samples) / len(samples)) / 32768.0
                else:
                    # Synthetic fallback
                    t = time.time()
                    bands = []
                    for i in range(64):
                        f = (i + 1) / 64.0
                        val = 0.5 * abs(math.sin(t * (1.0 + f * 4.0) + i)) * math.exp(-f * 1.8)
                        val += 0.2 * random.random() * math.exp(-f * 2.5)
                        bands.append(max(0.0, min(1.0, val)))
                    volume = 0.05 + 0.05 * abs(math.sin(t * 2.0))

                self.state.set("audio_fft", bands)
                self.state.set("audio_volume", volume)
                self.state.push_history(ekg=volume)
                
            except Exception:
                pass
                
            self._stop.wait(1.0 / 30.0)

        # Cleanup on exit
        if opened and self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
        if self._pa is not None:
            try:
                self._pa.terminate()
            except Exception:
                pass

    def _py_fft_bands(self, samples) -> List[float]:
        """Coarse pure-Python Discrete Fourier Transform for 64 bands."""
        N = len(samples)
        bands = [0.0] * 64
        band_size = max(1, (N // 2) // 64)
        
        # Sample the frequency domain to save computation
        for k in range(0, N // 2, max(1, N // 256)):
            re = 0.0
            im = 0.0
            for n in range(N):
                ang = -2.0 * math.pi * k * n / N
                re += samples[n] * math.cos(ang)
                im += samples[n] * math.sin(ang)
            mag = math.sqrt(re * re + im * im) / N
            idx = min(63, k // band_size)
            bands[idx] += mag
            
        mx = max(bands) if bands else 1.0
        if mx > 1e-6:
            bands = [min(1.0, v / mx) for v in bands]
        return bands


class VoiceEngine(threading.Thread):
    """
    Daemons 4 & 5: Speech-to-Text listener + Text-to-Speech synthesizer.
    Uses a sub-thread for non-blocking STT listen loop, and a queue-based
    TTS drainer. Falls back to no-op if libraries are missing.
    """

    def __init__(self, state: HermesState, bus: EventBus) -> None:
        super().__init__(daemon=True, name="VoiceEngine")
        self.state = state
        self.bus = bus
        self._stop = threading.Event()
        self.speak_queue: queue.Queue = queue.Queue()
        self._tts_engine = None
        self._recognizer = None
        self._mic = None

    def stop(self) -> None:
        self._stop.set()

    def speak(self, text: str) -> None:
        """Enqueue text to be spoken by the TTS engine."""
        if text and text.strip():
            self.speak_queue.put(text.strip())

    def _init_tts(self) -> None:
        if not HAS_PYTTSX3:
            return
        try:
            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty("rate", 175)
        except Exception:
            self._tts_engine = None

    def _init_stt(self) -> None:
        if not HAS_SR:
            return
        try:
            self._recognizer = sr.Recognizer()
            self._mic = sr.Microphone(sample_rate=Config.AUDIO_RATE)
            with self._mic as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.8)
        except Exception:
            self._mic = None

    def run(self) -> None:
        self._init_tts()
        self._init_stt()

        def stt_loop():
            if not HAS_SR or self._mic is None or self._recognizer is None:
                return
            while not self._stop.is_set():
                try:
                    with self._mic as source:
                        audio = self._recognizer.listen(source, timeout=2, phrase_time_limit=8)
                    try:
                        text = self._recognizer.recognize_google(audio)
                        if text:
                            self.state.set("last_transcript", self.state.get("transcript", ""))
                            self.state.set("transcript", text)
                            self.bus.publish("voice.transcript", text)
                    except Exception:
                        pass
                except Exception:
                    self._stop.wait(1.0)

        stt_thread = threading.Thread(target=stt_loop, daemon=True, name="STTLoop")
        stt_thread.start()

        # TTS drain loop
        while not self._stop.is_set():
            try:
                text = self.speak_queue.get(timeout=0.5)
                if self._tts_engine is not None:
                    try:
                        self._tts_engine.say(text)
                        self._tts_engine.runAndWait()
                    except Exception:
                        pass
            except queue.Empty:
                continue
            except Exception:
                pass


class NewsScraper(threading.Thread):
    """
    Daemon 6: Multi-source RSS scraper, 60s cadence.
    Populates global news and globe coordinates. Falls back to regex parsing
    if BeautifulSoup is missing, and uses urllib if requests is missing.
    """

    SOURCES = [
        ("Google News", "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"),
        ("BBC", "https://feeds.bbci.co.uk/news/world/rss.xml"),
        ("Wired", "https://www.wired.com/feed/rss"),
    ]

    def __init__(self, state: HermesState, bus: EventBus) -> None:
        super().__init__(daemon=True, name="NewsScraper")
        self.state = state
        self.bus = bus
        self._stop = threading.Event()
        self._source_idx = 0

    def stop(self) -> None:
        self._stop.set()

    def _parse_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        items = []
        if HAS_BS4:
            try:
                soup = BeautifulSoup(xml_text, "xml")
                for item in soup.find_all("item")[:12]:
                    title_tag = item.find("title")
                    pub_tag = item.find("pubDate")
                    title = title_tag.get_text(strip=True) if title_tag else "Untitled"
                    pub = pub_tag.get_text(strip=True) if pub_tag else ""
                    lat = random.uniform(-60.0, 60.0)
                    lon = random.uniform(-180.0, 180.0)
                    items.append({
                        "title": title,
                        "pub": pub,
                        "lat": lat,
                        "lon": lon,
                    })
            except Exception:
                pass
        else:
            # Regex fallback
            titles = re.findall(r"<title>(.*?)</title>", xml_text, re.DOTALL)
            for title in titles[1:13]:  # skip channel title
                clean = re.sub(r"<[^>]+>", "", title).strip()
                if clean:
                    items.append({
                        "title": clean,
                        "pub": "",
                        "lat": random.uniform(-60.0, 60.0),
                        "lon": random.uniform(-180.0, 180.0),
                    })
        return items

    def run(self) -> None:
        # Seed with synthetic data so globe has pins at boot
        seed_items = [
            {"title": "[BOOT] Initializing global telemetry grid...", "pub": "",
             "lat": 40.7, "lon": -74.0},
            {"title": "[BOOT] ARC reactor power link established", "pub": "",
             "lat": 34.0, "lon": -118.2},
            {"title": "[BOOT] Mark suit bay diagnostics nominal", "pub": "",
             "lat": 51.5, "lon": -0.1},
            {"title": "[BOOT] Satellite uplink channel locked", "pub": "",
             "lat": 35.6, "lon": 139.6},
        ]
        self.state.set("news_items", seed_items)
        self.state.set("globe_coords", [(it["lat"], it["lon"]) for it in seed_items])

        while not self._stop.is_set():
            name, url = self.SOURCES[self._source_idx % len(self.SOURCES)]
            self._source_idx += 1
            try:
                if HAS_REQUESTS:
                    resp = requests.get(url, timeout=8.0,
                                        headers={"User-Agent": "HERMES-Omnimind/1.0"})
                    xml_text = resp.text
                else:
                    import urllib.request
                    req = urllib.request.Request(url, headers={"User-Agent": "HERMES-Omnimind/1.0"})
                    with urllib.request.urlopen(req, timeout=8.0) as r:
                        xml_text = r.read().decode("utf-8", errors="ignore")
                        
                items = self._parse_xml(xml_text)
                if items:
                    self.state.set("news_items", items)
                    self.state.set("globe_coords", [(it["lat"], it["lon"]) for it in items])
                    self.bus.publish("news.update", items)
            except Exception:
                pass
                
            self._stop.wait(Config.SCRAPER_POLL)


class OpenRouterClient(threading.Thread):
    """
    Daemon 7: Cognitive API streaming client.
    Maintains a prompt queue, streams completion tokens, updates state for
    live UI rendering, and flushes sentence chunks to the VoiceEngine.
    Falls back to a simulated offline token stream if unreachable.
    """

    def __init__(self, state: HermesState, bus: EventBus,
                 voice: Optional[VoiceEngine] = None) -> None:
        super().__init__(daemon=True, name="OpenRouterClient")
        self.state = state
        self.bus = bus
        self.voice = voice
        self._stop = threading.Event()
        self.prompt_queue: queue.Queue = queue.Queue()

    def stop(self) -> None:
        self._stop.set()

    def submit(self, user_text: str) -> None:
        """Enqueue a prompt to be processed by the cognitive engine."""
        if user_text and user_text.strip():
            self.prompt_queue.put(user_text.strip())

    def _stream_completion(self, user_text: str) -> None:
        api_key = Config.OPENROUTER_API_KEY
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            
        payload = {
            "model": Config.OPENROUTER_MODEL,
            "stream": True,
            "messages": [
                {"role": "system", "content": HERMES_CORE_SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
        }
        
        full_text = ""
        stream_buf = ""
        
        try:
            if HAS_REQUESTS and api_key:
                resp = requests.post(
                    Config.OPENROUTER_URL, headers=headers,
                    data=json.dumps(payload), timeout=30, stream=True,
                )
                if resp.status_code != 200:
                    err = f"[HERMES API ERROR {resp.status_code}]"
                    self.state.set("llm_stream", err)
                    self.state.set("llm_full", err)
                    return
                    
                for line in resp.iter_lines(decode_unicode=True):
                    if self._stop.is_set():
                        break
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            tok = delta.get("content", "")
                            if tok:
                                full_text += tok
                                stream_buf += tok
                                self.state.set("llm_stream", stream_buf[-800:])
                                self.state.set("llm_full", full_text)
                                
                                # Flush sentence endings to TTS
                                m = re.search(r"[.!?;]\s", stream_buf)
                                if m:
                                    sentence = stream_buf[:m.end()]
                                    stream_buf = stream_buf[m.end():]
                                    if self.voice is not None:
                                        self.voice.speak(sentence)
                        except Exception:
                            continue
            else:
                # Offline fallback simulation
                words = ("[OFFLINE MODE] HERMES cognitive uplink unavailable. "
                         "OpenRouter API key not set or requests library missing. "
                         "Telemetry grid operational. Awaiting uplink restoration.").split(" ")
                for w in words:
                    if self._stop.is_set():
                        break
                    full_text += w + " "
                    stream_buf += w + " "
                    self.state.set("llm_stream", stream_buf[-800:])
                    self.state.set("llm_full", full_text)
                    time.sleep(0.04)
                    
        except Exception as e:
            err = f"[HERMES STREAM ERROR: {type(e).__name__}]"
            self.state.set("llm_stream", err)
            self.state.set("llm_full", err)

        # Flush remainder to TTS
        if stream_buf.strip() and self.voice is not None:
            self.voice.speak(stream_buf)

    def run(self) -> None:
        while not self._stop.is_set():
            try:
                user_text = self.prompt_queue.get(timeout=0.5)
                self._stream_completion(user_text)
            except queue.Empty:
                continue
            except Exception:
                pass


class ProactiveDaemon(threading.Thread):
    """
    Daemon 8: Proactive orchestrator at 1.0 Hz.
    Evaluates safety thresholds, calculates system stability score, and
    routes critical alerts to the UI and VoiceEngine.
    """

    def __init__(self, state: HermesState, bus: EventBus,
                 voice: Optional[VoiceEngine] = None) -> None:
        super().__init__(daemon=True, name="ProactiveDaemon")
        self.state = state
        self.bus = bus
        self.voice = voice
        self._stop = threading.Event()
        self._last_alert_time = 0.0

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        while not self._stop.is_set():
            try:
                snap = self.state.snapshot()
                temp = snap["cpu_temp"]
                ram = snap["ram_usage"]
                ping = snap["ping_ms"]
                net_up = snap["internet_up"]

                # Stability score calculation
                penalties = 0.0
                if temp > Config.TEMP_CRITICAL:
                    penalties += (temp - Config.TEMP_CRITICAL) * 1.2
                if ram > Config.RAM_CRITICAL:
                    penalties += (ram - Config.RAM_CRITICAL) * 0.8
                if not net_up:
                    penalties += 15.0
                if ping > 500.0:
                    penalties += (ping - 500.0) * 0.02
                    
                stability = max(0.0, 100.0 - penalties)
                core_health = max(0.0, 100.0 - max(0.0, temp - 60.0) * 1.5)
                self.state.set("stability_score", stability)
                self.state.set("core_health", core_health)

                # Alert routing
                now = time.time()
                alert_msgs = []
                if temp > Config.TEMP_CRITICAL:
                    alert_msgs.append(f"CRITICAL: CPU thermal at {temp:.1f}C exceeds {Config.TEMP_CRITICAL}C")
                if ram > Config.RAM_CRITICAL:
                    alert_msgs.append(f"CRITICAL: RAM load at {ram:.1f}% exceeds {Config.RAM_CRITICAL}%")
                if not net_up:
                    alert_msgs.append("WARNING: Network uplink DOWN")
                if stability < Config.STABILITY_MIN:
                    alert_msgs.append(f"WARNING: System stability degraded to {stability:.1f}%")

                if alert_msgs and (now - self._last_alert_time) > 8.0:
                    self._last_alert_time = now
                    combined = " | ".join(alert_msgs)
                    self.state.set("daemon_override", True)
                    self.state.set("daemon_msg", combined)
                    if self.voice is not None:
                        self.voice.speak(combined)
                    self.bus.publish("proactive.alert", combined)
                elif not alert_msgs and (now - self._last_alert_time) > 4.0:
                    self.state.set("daemon_override", False)
                    self.state.set("daemon_msg", "")

            except Exception:
                pass
            
            self._stop.wait(Config.PROACTIVE_POLL)