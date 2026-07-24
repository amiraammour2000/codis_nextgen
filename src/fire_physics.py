import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum
import random

class FuelModel(Enum):
    ROTHERMEL = "Rothermel"
    CANADIAN_FBP = "Canadian FBP"
    AUSTRALIAN = "Australian"
    CUSTOM = "Custom"

@dataclass
class FireCell:
    state: int  # 0: intact, 1: brûlé, 2: feu actif, 3: refroidi
    temperature: float
    fuel_moisture: float
    fuel_load: float
    elevation: float
    slope: float
    aspect: float
    wind_speed: float
    wind_dir: float
    spotting_probability: float = 0.0
    crown_fire_risk: float = 0.0

class PhysicalFireSimulator:
    """Simulateur physique de propagation du feu avec modélisation avancée."""

    def __init__(self, base_lat, base_lon, cell_size_m=100, rows=50, cols=50):
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size_m
        self.base_lat = base_lat
        self.base_lon = base_lon
        self.lat_step = (cell_size_m / 111000.0)
        self.lon_step = (cell_size_m / (111000.0 * np.cos(np.radians(base_lat))))

    def step_propagation(self, grid, elevation_grid, wind_speed, wind_dir_deg, moisture):
        """Étape de propagation avec physique avancée."""
        new_grid = grid.copy()
        rad = np.radians(wind_dir_deg)
        wx = np.cos(rad)
        wy = np.sin(rad)

        effective_moisture = max(5, moisture - (wind_speed * 0.2))

        for r in range(1, self.rows - 1):
            for c in range(1, self.cols - 1):
                if grid[r, c] == 2:
                    new_grid[r, c] = 1
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols and grid[nr, nc] == 0:
                                delta_h = elevation_grid[nr, nc] - elevation_grid[r, c]
                                slope_factor = delta_h / 10.0

                                dist = np.sqrt(dr**2 + dc**2)
                                alignment = (dr * wx + dc * wy) / (dist + 1e-5)

                                prob = (wind_speed / 80.0) * 0.5
                                prob += max(0, slope_factor) * 0.3
                                prob += max(0, alignment) * 0.4
                                prob *= (1.0 - (effective_moisture / 100.0))

                                if np.random.rand() < max(0.01, prob):
                                    new_grid[nr, nc] = 2
        return new_grid

    def get_fire_geojson(self, grid):
        """Convertit la grille en coordonnées GPS."""
        fire_coords = []
        for r in range(self.rows):
            for c in range(self.cols):
                if grid[r, c] == 2:
                    lat = self.base_lat - (r * self.lat_step)
                    lon = self.base_lon + (c * self.lon_step)
                    fire_coords.append([lat, lon])
        return fire_coords

    def get_burned_perimeter(self, grid):
        """Calcule le périmètre de la zone brûlée."""
        perimeter = []
        for r in range(self.rows):
            for c in range(self.cols):
                if grid[r, c] == 1:
                    neighbors = [(r+dr, c+dc) for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]]
                    if any(0 <= nr < self.rows and 0 <= nc < self.cols and grid[nr, nc] == 0 
                           for nr, nc in neighbors):
                        lat = self.base_lat - (r * self.lat_step)
                        lon = self.base_lon + (c * self.lon_step)
                        perimeter.append([lat, lon])
        return perimeter

    def calculate_ros(self, wind_speed, slope, fuel_moisture, fuel_type="standard"):
        """Rate of Spread selon Rothermel simplifié."""
        base_ros = 0.5
        wind_factor = 0.15 * wind_speed
        slope_factor = 0.1 * slope
        moisture_factor = max(0, 1.0 - (fuel_moisture / 30.0))

        fuel_multipliers = {
            "standard": 1.0,
            "forest": 1.3,
            "shrub": 1.5,
            "grass": 0.8,
            "urban": 0.3
        }

        ros = base_ros + wind_factor + slope_factor
        ros *= moisture_factor
        ros *= fuel_multipliers.get(fuel_type, 1.0)
        return max(0.1, ros)


class AdvancedFireModel(PhysicalFireSimulator):
    """Modèle de feu avancé avec spotting, feu de cime et modèles de combustible."""

    def __init__(self, base_lat, base_lon, rows=60, cols=60, cell_size_m=100,
                 spotting_distance=500, crown_fire=True, spotting=True, 
                 spotting_prob=0.15, fuel_model=FuelModel.ROTHERMEL):
        super().__init__(base_lat, base_lon, cell_size_m, rows, cols)
        self.spotting_distance = spotting_distance
        self.crown_fire_enabled = crown_fire
        self.spotting_enabled = spotting
        self.spotting_prob = spotting_prob
        self.fuel_model = fuel_model
        self.spotting_events = []
        self.crown_fire_events = []

    def step_propagation(self, grid, elevation_grid, wind_speed, wind_dir_deg, moisture):
        """Propagation avancée avec spotting et feu de cime."""
        new_grid = grid.copy()
        rad = np.radians(wind_dir_deg)
        wx = np.cos(rad)
        wy = np.sin(rad)

        effective_moisture = max(5, moisture - (wind_speed * 0.2))

        # Phase 1: Propagation de base
        for r in range(1, self.rows - 1):
            for c in range(1, self.cols - 1):
                if grid[r, c] == 2:
                    new_grid[r, c] = 1

                    # Propagation locale
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols and grid[nr, nc] == 0:
                                delta_h = elevation_grid[nr, nc] - elevation_grid[r, c]
                                slope_factor = delta_h / 10.0

                                dist = np.sqrt(dr**2 + dc**2)
                                alignment = (dr * wx + dc * wy) / (dist + 1e-5)

                                # Modèle de combustible
                                if self.fuel_model == FuelModel.ROTHERMEL:
                                    prob = self._rothermel_prob(wind_speed, slope_factor, alignment, effective_moisture)
                                elif self.fuel_model == FuelModel.CANADIAN_FBP:
                                    prob = self._canadian_fbp_prob(wind_speed, slope_factor, alignment, effective_moisture)
                                else:
                                    prob = self._default_prob(wind_speed, slope_factor, alignment, effective_moisture)

                                if np.random.rand() < prob:
                                    new_grid[nr, nc] = 2

                    # Feu de cime
                    if self.crown_fire_enabled:
                        crown_prob = self._crown_fire_probability(wind_speed, moisture, elevation_grid[r, c])
                        if np.random.rand() < crown_prob:
                            self.crown_fire_events.append({
                                'lat': self.base_lat - (r * self.lat_step),
                                'lon': self.base_lon + (c * self.lon_step),
                                'timestamp': 'now'
                            })
                            # Propagation accélérée en cime
                            for dr in [-2, -1, 0, 1, 2]:
                                for dc in [-2, -1, 0, 1, 2]:
                                    nr, nc = r + dr, c + dc
                                    if 0 <= nr < self.rows and 0 <= nc < self.cols and grid[nr, nc] == 0:
                                        if np.random.rand() < 0.3:
                                            new_grid[nr, nc] = 2

                    # Spotting
                    if self.spotting_enabled and np.random.rand() < self.spotting_prob:
                        spot_dist = int(self.spotting_distance / self.cell_size)
                        spot_r = r + int(np.random.uniform(-spot_dist, spot_dist))
                        spot_c = c + int(np.random.uniform(-spot_dist, spot_dist))

                        if 0 <= spot_r < self.rows and 0 <= spot_c < self.cols and grid[spot_r, spot_c] == 0:
                            new_grid[spot_r, spot_c] = 2
                            self.spotting_events.append({
                                'from': (r, c),
                                'to': (spot_r, spot_c),
                                'distance': np.sqrt((spot_r-r)**2 + (spot_c-c)**2) * self.cell_size
                            })

        return new_grid

    def _default_prob(self, wind_speed, slope_factor, alignment, moisture):
        """Probabilité de propagation par défaut."""
        prob = (wind_speed / 80.0) * 0.5
        prob += max(0, slope_factor) * 0.3
        prob += max(0, alignment) * 0.4
        prob *= (1.0 - (moisture / 100.0))
        return max(0.01, min(0.95, prob))

    def _rothermel_prob(self, wind_speed, slope_factor, alignment, moisture):
        """Probabilité basée sur Rothermel."""
        # ROS (Rate of Spread) simplifié
        ros = 0.5 + 0.15 * wind_speed + 0.1 * max(0, slope_factor)
        ros *= max(0, 1.0 - (moisture / 30.0))

        # Convertir en probabilité
        prob = min(0.8, ros / 10.0)
        prob += max(0, alignment) * 0.2
        return max(0.01, min(0.95, prob))

    def _canadian_fbp_prob(self, wind_speed, slope_factor, alignment, moisture):
        """Probabilité basée sur Canadian FBP."""
        isi = 0.208 * wind_speed  # Initial Spread Index
        bui = max(0, 100 - moisture * 2)  # Buildup Index

        prob = (isi / 50.0) * 0.4
        prob += (bui / 200.0) * 0.3
        prob += max(0, slope_factor) * 0.2
        prob += max(0, alignment) * 0.1
        return max(0.01, min(0.95, prob))

    def _crown_fire_probability(self, wind_speed, moisture, elevation):
        """Probabilité de transition vers feu de cime."""
        if wind_speed < 30:
            return 0.0

        base_prob = (wind_speed - 30) / 100.0
        moisture_factor = max(0, 1.0 - (moisture / 20.0))
        elevation_factor = min(1.0, elevation / 1000.0)

        return base_prob * moisture_factor * elevation_factor * 0.3

    def get_spotting_events(self):
        """Retourne les événements de spotting."""
        return self.spotting_events

    def get_crown_fire_events(self):
        """Retourne les événements de feu de cime."""
        return self.crown_fire_events

    def get_statistics(self, grid):
        """Statistiques détaillées de la simulation."""
        active = np.sum(grid == 2)
        burned = np.sum(grid == 1)
        total = grid.size

        return {
            'active_cells': int(active),
            'burned_cells': int(burned),
            'total_cells': int(total),
            'affected_percentage': float((active + burned) / total * 100),
            'active_percentage': float(active / total * 100),
            'burned_percentage': float(burned / total * 100),
            'spotting_events': len(self.spotting_events),
            'crown_fire_events': len(self.crown_fire_events),
            'estimated_area_ha': float((active + burned) * (self.cell_size / 100) ** 2),
        }
