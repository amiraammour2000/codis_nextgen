import asyncio
import json
import websockets
import random
import time
from datetime import datetime

CONNECTED_CLIENTS = set()

async def simulate_iot_devices(websocket):
    """Simule des déplacements de véhicules et drones."""
    vehicles = [
        {"id": "CCF_01", "type": "truck", "lat": 43.6045, "lon": 7.0542, "speed": 45, "altitude": 120, "status": "En intervention", "battery": 78},
        {"id": "CCF_02", "type": "truck", "lat": 43.6100, "lon": 7.0600, "speed": 30, "altitude": 85, "status": "En route", "battery": 92},
        {"id": "DRONE_RECON_1", "type": "drone", "lat": 43.5900, "lon": 7.0600, "speed": 65, "altitude": 350, "status": "Reconnaissance", "battery": 45},
        {"id": "DRONE_THERMAL_2", "type": "drone", "lat": 43.6150, "lon": 7.0450, "speed": 55, "altitude": 280, "status": "Surveillance", "battery": 62},
        {"id": "CANADAIR_01", "type": "aircraft", "lat": 43.6200, "lon": 7.0700, "speed": 280, "altitude": 1500, "status": "Largage", "battery": 100},
        {"id": "CCF_03", "type": "truck", "lat": 43.5950, "lon": 7.0550, "speed": 50, "altitude": 95, "status": "En intervention", "battery": 65},
        {"id": "HELICO_01", "type": "aircraft", "lat": 43.6080, "lon": 7.0680, "speed": 180, "altitude": 800, "status": "Transport", "battery": 88},
    ]

    while True:
        for v in vehicles:
            # Déplacement réaliste
            v["lat"] += random.uniform(-0.0008, 0.0008)
            v["lon"] += random.uniform(-0.0008, 0.0008)
            v["speed"] = max(0, v["speed"] + random.uniform(-5, 5))
            v["battery"] = max(0, min(100, v["battery"] - random.uniform(0, 0.5)))
            v["last_update"] = datetime.now().isoformat()

            payload = json.dumps({"type": "GPS_UPDATE", "payload": v})

            if CONNECTED_CLIENTS:
                await asyncio.gather(
                    *[client.send(payload) for client in CONNECTED_CLIENTS.copy()],
                    return_exceptions=True
                )

        await asyncio.sleep(2)

async def telemetry_handler(websocket, path):
    """Gère les connexions WebSocket."""
    CONNECTED_CLIENTS.add(websocket)
    try:
        sim_task = asyncio.create_task(simulate_iot_devices(websocket))

        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("type") == "COMMAND":
                    # Traiter les commandes entrantes
                    response = json.dumps({"type": "ACK", "payload": data})
                    await websocket.send(response)
            except json.JSONDecodeError:
                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CONNECTED_CLIENTS.discard(websocket)
        if 'sim_task' in locals():
            sim_task.cancel()

async def main():
    """Démarre le serveur WebSocket."""
    async with websockets.serve(telemetry_handler, "0.0.0.0", 8765, ping_interval=20, ping_timeout=10):
        print("🚀 Serveur IoT WebSocket démarré sur ws://0.0.0.0:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
