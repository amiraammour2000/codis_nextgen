import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class ScenarioManager:
    """Gestionnaire de scénarios d'incendie."""

    def __init__(self, storage_path: str = "data/scenarios"):
        self.storage_path = storage_path
        self.scenarios = []
        self._load_scenarios()

    def _load_scenarios(self):
        """Charge les scénarios existants."""
        os.makedirs(self.storage_path, exist_ok=True)
        # Scénarios par défaut
        self.scenarios = [
            {
                'id': 'SCN-001',
                'name': 'Scénario Standard - Forêt méditerranéenne',
                'description': 'Propagation classique en forêt méditerranéenne avec vent modéré',
                'ignition_points': 1,
                'ignition_intensity': 3,
                'env_params': {
                    'wind_speed': 45,
                    'wind_dir': 180,
                    'moisture': 25,
                    'temperature': 30
                },
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 'SCN-002',
                'name': 'Scénario Critique - Vent fort',
                'description': 'Conditions extrêmes avec vent fort et humidité faible',
                'ignition_points': 2,
                'ignition_intensity': 5,
                'env_params': {
                    'wind_speed': 85,
                    'wind_dir': 270,
                    'moisture': 12,
                    'temperature': 38
                },
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 'SCN-003',
                'name': 'Scénario Urbain - Interface',
                'description': 'Feu de forêt menaçant zone urbaine',
                'ignition_points': 1,
                'ignition_intensity': 4,
                'env_params': {
                    'wind_speed': 35,
                    'wind_dir': 90,
                    'moisture': 30,
                    'temperature': 28
                },
                'created_at': datetime.now().isoformat()
            }
        ]

    def create_scenario(self, name: str, description: str = "", 
                       ignition_points: int = 1, ignition_intensity: int = 3,
                       env_params: Dict = None) -> Dict:
        """Crée un nouveau scénario."""
        scenario = {
            'id': f"SCN-{len(self.scenarios) + 1:03d}",
            'name': name,
            'description': description,
            'ignition_points': ignition_points,
            'ignition_intensity': ignition_intensity,
            'env_params': env_params or {},
            'created_at': datetime.now().isoformat()
        }
        self.scenarios.append(scenario)
        return scenario

    def list_scenarios(self) -> List[Dict]:
        """Liste tous les scénarios."""
        return self.scenarios

    def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """Récupère un scénario par ID."""
        for s in self.scenarios:
            if s['id'] == scenario_id:
                return s
        return None

    def load_scenario(self, name: str) -> Optional[Dict]:
        """Charge un scénario par nom."""
        for s in self.scenarios:
            if s['name'] == name:
                return s
        return None

    def delete_scenario(self, scenario_id: str) -> bool:
        """Supprime un scénario."""
        for i, s in enumerate(self.scenarios):
            if s['id'] == scenario_id:
                self.scenarios.pop(i)
                return True
        return False
