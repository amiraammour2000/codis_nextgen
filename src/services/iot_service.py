import asyncio
import json
import websockets
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
import threading

class IoTTelemetryService:
    """Service de télémétrie IoT temps réel."""

    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.connected = False
        self.tracks = []
        self.callbacks = []
        self._running = False
        self._thread = None

    def start(self):
        """Démarre le service de télémétrie."""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        """Arrête le service."""
        self._running = False

    def _run(self):
        """Boucle principale du service."""
        try:
            asyncio.run(self._connect())
        except Exception:
            pass

    async def _connect(self):
        """Connexion WebSocket."""
        try:
            async with websockets.connect(self.uri) as websocket:
                self.connected = True
                async for message in websocket:
                    data = json.loads(message)
                    self._process_message(data)
        except Exception:
            self.connected = False

    def _process_message(self, data: Dict):
        """Traite un message reçu."""
        if data.get("type") == "GPS_UPDATE":
            payload = data['payload']
            self._update_track(payload)
            for callback in self.callbacks:
                callback(payload)

    def _update_track(self, track: Dict):
        """Met à jour ou ajoute une trace."""
        for i, t in enumerate(self.tracks):
            if t['id'] == track['id']:
                self.tracks[i] = track
                return
        self.tracks.append(track)

    def get_tracks(self) -> List[Dict]:
        """Retourne toutes les traces."""
        return self.tracks

    def get_track_by_id(self, track_id: str) -> Optional[Dict]:
        """Retourne une trace par ID."""
        for t in self.tracks:
            if t['id'] == track_id:
                return t
        return None

    def register_callback(self, callback: Callable):
        """Enregistre un callback."""
        self.callbacks.append(callback)

    def simulate_tracks(self):
        """Génère des traces simulées pour démonstration."""
        vehicles = [
            {"id": "CCF_01", "type": "truck", "lat": 43.6045, "lon": 7.0542, "speed": 45, "altitude": 120, "status": "En intervention", "battery": 78},
            {"id": "CCF_02", "type": "truck", "lat": 43.6100, "lon": 7.0600, "speed": 30, "altitude": 85, "status": "En route", "battery": 92},
            {"id": "DRONE_RECON_1", "type": "drone", "lat": 43.5900, "lon": 7.0600, "speed": 65, "altitude": 350, "status": "Reconnaissance", "battery": 45},
            {"id": "DRONE_THERMAL_2", "type": "drone", "lat": 43.6150, "lon": 7.0450, "speed": 55, "altitude": 280, "status": "Surveillance", "battery": 62},
            {"id": "CANADAIR_01", "type": "aircraft", "lat": 43.6200, "lon": 7.0700, "speed": 280, "altitude": 1500, "status": "Largage", "battery": 100},
        ]

        for v in vehicles:
            v['lat'] += random.uniform(-0.001, 0.001)
            v['lon'] += random.uniform(-0.001, 0.001)
            v['last_update'] = datetime.now().isoformat()
            self._update_track(v)

        return vehicles
