import requests
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import numpy as np

class WeatherService:
    """Service météorologique pour données temps réel et prévisions."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "demo_key"
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    def get_current_weather(self, lat: float, lon: float) -> Dict:
        """Récupère les conditions météo actuelles."""
        cache_key = f"{lat:.4f},{lon:.4f}"

        if cache_key in self.cache:
            cached_time, data = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self.cache_ttl):
                return data

        # Données simulées pour démonstration
        weather_data = {
            'temperature': np.random.uniform(25, 40),
            'humidity': np.random.uniform(15, 45),
            'wind_speed': np.random.uniform(20, 80),
            'wind_direction': np.random.uniform(0, 360),
            'pressure': np.random.uniform(1000, 1025),
            'visibility': np.random.uniform(5, 20),
            'cloud_cover': np.random.uniform(0, 100),
            'precipitation': np.random.uniform(0, 5),
            'uv_index': np.random.uniform(5, 11),
            'timestamp': datetime.now().isoformat(),
            'source': 'simulation'
        }

        self.cache[cache_key] = (datetime.now(), weather_data)
        return weather_data

    def get_forecast(self, lat: float, lon: float, hours: int = 24) -> List[Dict]:
        """Récupère les prévisions météo."""
        forecasts = []
        base_weather = self.get_current_weather(lat, lon)

        for i in range(hours):
            forecast_time = datetime.now() + timedelta(hours=i)

            # Variations réalistes
            temp_var = np.sin(i * np.pi / 12) * 5  # Variation journalière
            wind_var = np.random.uniform(-10, 10)

            forecasts.append({
                'timestamp': forecast_time.isoformat(),
                'temperature': base_weather['temperature'] + temp_var + np.random.uniform(-2, 2),
                'humidity': max(10, min(100, base_weather['humidity'] + np.random.uniform(-10, 10))),
                'wind_speed': max(0, base_weather['wind_speed'] + wind_var),
                'wind_direction': (base_weather['wind_direction'] + np.random.uniform(-30, 30)) % 360,
                'precipitation_probability': np.random.uniform(0, 30) if i < 6 else np.random.uniform(0, 60),
                'fire_risk_index': self._calculate_fire_risk(base_weather, i)
            })

        return forecasts

    def _calculate_fire_risk(self, weather: Dict, hour_offset: int) -> str:
        """Calcule l'indice de risque d'incendie."""
        score = 0

        # Température
        if weather['temperature'] > 35:
            score += 3
        elif weather['temperature'] > 30:
            score += 2
        elif weather['temperature'] > 25:
            score += 1

        # Humidité
        if weather['humidity'] < 20:
            score += 3
        elif weather['humidity'] < 30:
            score += 2
        elif weather['humidity'] < 40:
            score += 1

        # Vent
        if weather['wind_speed'] > 60:
            score += 3
        elif weather['wind_speed'] > 40:
            score += 2
        elif weather['wind_speed'] > 20:
            score += 1

        if score >= 7:
            return "EXTRÊME"
        elif score >= 5:
            return "TRÈS ÉLEVÉ"
        elif score >= 3:
            return "ÉLEVÉ"
        elif score >= 1:
            return "MODÉRÉ"
        return "FAIBLE"

    def get_fire_weather_index(self, lat: float, lon: float) -> Dict:
        """Calcule l'indice météo des incendies (FWI)."""
        weather = self.get_current_weather(lat, lon)

        # Composants FWI simplifiés
        ffmc = 85 + np.random.uniform(-5, 5)  # Fine Fuel Moisture Code
        dmc = 60 + np.random.uniform(-10, 10)  # Duff Moisture Code
        dc = 400 + np.random.uniform(-50, 50)  # Drought Code
        isi = 10 + np.random.uniform(-3, 5)  # Initial Spread Index
        bui = 80 + np.random.uniform(-20, 20)  # Buildup Index
        fwi = 30 + np.random.uniform(-10, 15)  # Fire Weather Index

        return {
            'ffmc': round(ffmc, 1),
            'dmc': round(dmc, 1),
            'dc': round(dc, 1),
            'isi': round(isi, 1),
            'bui': round(bui, 1),
            'fwi': round(fwi, 1),
            'risk_level': self._fwi_to_risk(fwi),
            'timestamp': datetime.now().isoformat()
        }

    def _fwi_to_risk(self, fwi: float) -> str:
        """Convertit FWI en niveau de risque."""
        if fwi >= 50:
            return "EXTRÊME"
        elif fwi >= 30:
            return "TRÈS ÉLEVÉ"
        elif fwi >= 15:
            return "ÉLEVÉ"
        elif fwi >= 5:
            return "MODÉRÉ"
        return "FAIBLE"
