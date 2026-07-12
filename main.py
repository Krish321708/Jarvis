#!/usr/bin/env python3
"""
PROJECT HERMES - Omnimind Absolute Edition
File: main.py
Monolithic Compilation Standard
"The earth and sky will break before I fail you."
"""

import os
import sys
import time
import traceback

# ---------------------------------------------------------------------------
# PATH OVERRIDE FOR "Backhand_code" DIRECTORY
# ---------------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(CURRENT_DIR, "Backhand_code")
if os.path.isdir(BACKEND_DIR):
    sys.path.insert(0, BACKEND_DIR)
else:
    print(f"[HERMES] FATAL: Directory '{BACKEND_DIR}' not found.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# HERMES SECTOR IMPORTS (Pulled from Backhand_code)
# ---------------------------------------------------------------------------
from config import Config
from palette import BLACK
from state import HermesState
from event_bus import EventBus
from daemons import (HardwareMonitor, NetworkMonitor, AudioDSPEngine, VoiceEngine,
                     NewsScraper, OpenRouterClient, ProactiveDaemon)
from ui_panels import (HeaderBarRenderer, TerrainRenderer, GlobeRenderer, NewsFeedRenderer,
                       PersonalMonitorRenderer, StatusMatrixRenderer, DaemonOverlayRenderer)
from self_test import execute_pre_flight

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False
    pygame = None


class HermesOmnimind:
    """
    Main Application Controller. 
    Orchestrates daemons, state, event routing, and the render pipeline.
    """

    def __init__(self) -> None:
        if not HAS_PYGAME:
            print("[HERMES] FATAL: Pygame is required for Omnimind GUI. Aborting.")
            sys.exit(1)

        # 1. Core Infrastructure Initialization
        # State and Bus are injected into all daemons and controllers,
        # acting as the central nervous system of the application.
        self.state = HermesState()
        self.bus = EventBus()

        # 2. Daemon Initialization
        # Each daemon runs in an autonomous background thread, polling hardware,
        # network, or APIs, and writing results into the shared HermesState.
        self.hw_monitor = HardwareMonitor(self.state, self.bus)
        self.net_monitor = NetworkMonitor(self.state, self.bus)
        self.audio_dsp = AudioDSPEngine(self.state, self.bus)
        self.voice_engine = VoiceEngine(self.state, self.bus)
        self.news_scraper = NewsScraper(self.state, self.bus)
        
        # The Cognitive LLM Client requires the Voice Engine to route spoken responses
        self.llm_client = OpenRouterClient(self.state, self.bus, voice=self.voice_engine)
        
        # The Proactive Daemon evaluates system thresholds and uses Voice to alert
        self.proactive = ProactiveDaemon(self.state, self.bus, voice=self.voice_engine)

        # 3. UI Renderer Initialization
        # Renderers are stateless; they read a snapshot from HermesState every frame.
        self.header = HeaderBarRenderer()
        self.terrain = TerrainRenderer()
        self.globe = GlobeRenderer()
        self.news = NewsFeedRenderer()
        self.personal = PersonalMonitorRenderer()
        self.status = StatusMatrixRenderer()
        self.daemon_overlay = DaemonOverlayRenderer()

        # 4. Display & Loop Setup
        pygame.init()
        # SCALED flag handles HiDPI displays gracefully, vsync=1 locks to monitor refresh
        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT), pygame.SCALED, vsync=1)
        pygame.display.set_caption("PROJECT HERMES - Omnimind Absolute Edition")
        self.clock = pygame.time.Clock()
        self.running = False

        # 5. Event Bus Wiring
        # Decoupled communication: Voice transcript captures are routed directly
        # to the LLM client for cognitive processing without either knowing of the other.
        self.bus.subscribe("voice.transcript", self.llm_client.submit)

    def start_daemons(self) -> None:
        """Spawns all background threads."""
        self.hw_monitor.start()
        self.net_monitor.start()
        self.audio_dsp.start()
        self.voice_engine.start()
        self.news_scraper.start()
        self.llm_client.start()
        self.proactive.start()

    def stop_daemons(self) -> None:
        """Signals all background threads to stop via their threading.Event flags."""
        print("[HERMES] Signaling daemon shutdown...")
        self.hw_monitor.stop()
        self.net_monitor.stop()
        self.audio_dsp.stop()
        self.voice_engine.stop()
        self.news_scraper.stop()
        self.llm_client.stop()
        self.proactive.stop()

    def _initial_boot_prompt(self) -> None:
        """Sends the first system prompt to the LLM to verify uplink on launch."""
        boot_msg = (
            "SYSTEM BOOT COMPLETE. HERMES OMMININD ABSOLUTE EDITION IS ONLINE. "
            "All telemetry streams initialized. ARC reactor stable. "
            "Acknowledge uplink and report cognitive status."
        )
        self.llm_client.submit(boot_msg)

    def run(self) -> None:
        """The main 60fps application loop."""
        self.running = True
        self.start_daemons()
        self._initial_boot_prompt()

        print("[HERMES] Entering main render loop. UI is live.")

        while self.running:
            # dt ensures smooth animations even if frame rate dips
            dt = self.clock.tick(Config.FPS) / 1000.0
            
            self.handle_events()
            self.render(dt)
            pygame.display.flip()

        # Loop exited, begin teardown
        self.stop_daemons()
        pygame.quit()

    def handle_events(self) -> None:
        """Processes Pygame OS events and keyboard inputs."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    
                elif event.key == pygame.K_RETURN:
                    # Manual cognitive diagnostic trigger
                    self.llm_client.submit("Run a deep system diagnostic on all subnets and report anomalies.")
                    
                elif event.key == pygame.K_SPACE:
                    # Manual TTS bypass test
                    self.voice_engine.speak("All systems nominal. Standing by for orders.")
                    
                elif event.key == pygame.K_BACKSPACE:
                    # Clear the voice transcript UI bar manually
                    self.state.set("transcript", "")

    def render(self, dt: float) -> None:
        """
        The render pipeline. 
        Takes a non-blocking snapshot of the state and feeds it to all panels.
        """
        # Capture once per frame to ensure visual consistency across all panels
        snap = self.state.snapshot()
        
        # Base clear
        self.screen.fill(BLACK)
        
        # Layer 1: Base Viewports
        self.header.render(self.screen, snap)
        self.terrain.render(self.screen, snap, dt)
        self.globe.render(self.screen, snap, dt)
        self.news.render(self.screen, snap, dt)
        self.personal.render(self.screen, snap, dt)
        self.status.render(self.screen, snap, dt)
        
        # Layer 2: HUD Overlays & Global Alerts
        # Drawn last so they sit above all base geometry
        self.daemon_overlay.render(self.screen, snap, dt)


# ===========================================================================
# BOOT SEQUENCE
# ===========================================================================
def print_boot_art() -> None:
    art = r"""
██╗  ██╗███████╗██████╗ ███╗   ███╗███████╗███████╗
██║  ██║██╔════╝██╔══██╗████╗ ████║██╔════╝██╔════╝
███████║█████╗  ██████╔╝██╔████╔██║█████╗  ███████╗
██╔══██║██╔══╝  ██╔══██╗██║╚██╔╝██║██╔══╝  ╚════██║
██║  ██║███████╗██║  ██║██║ ╚═╝ ██║███████╗███████║
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝
S I N G U L A R I T Y   O M N I M I N D
A B S O L U T E   E D I T I O N
"The earth and sky will break before I fail you."
    """
    print(art)


if __name__ == "__main__":
    try:
        print_boot_art()
        
        # 1. Pre-flight Validation (Must pass twice)
        if not execute_pre_flight():
            print("[HERMES] CRITICAL: Pre-flight validation failed. System abort.")
            sys.exit(1)
            
        # 2. Application Bootstrap
        print("[HERMES] Booting Apex Controller...")
        app = HermesOmnimind()
        app.run()
        
    except KeyboardInterrupt:
        # Graceful exit on Ctrl+C
        print("\n[HERMES] Manual shutdown initiated by Master. Awaiting power down sequence.")
        try:
            pygame.quit()
        except Exception:
            pass
        sys.exit(0)
        
    except Exception as e:
        # Catch-all catastrophic failure handler
        print(f"\n[HERMES CRITICAL FAILURE] {type(e).__name__}: {e}")
        print("[HERMES] STACK TRACE:")
        traceback.print_exc()
        try:
            pygame.quit()
        except Exception:
            pass
        sys.exit(1)
        
    finally:
        print("[HERMES] Power down complete. Goodbye.")