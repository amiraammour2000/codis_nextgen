import math
from typing import Tuple

def format_coordinates(lat: float, lon: float) -> str:
    """Formate les coordonnées GPS."""
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    return f"{abs(lat):.4f}°{lat_dir}, {abs(lon):.4f}°{lon_dir}"

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcule la distance en km entre deux points GPS."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))

def get_priority_color(priority: str) -> str:
    """Retourne la couleur associée à une priorité."""
    colors = {
        'Critique': '#EF4444',
        'Élevée': '#F59E0B',
        'Moyenne': '#3B82F6',
        'Faible': '#10B981',
        'Standard': '#64748B'
    }
    return colors.get(priority, '#64748B')

def format_duration(seconds: int) -> str:
    """Formate une durée en secondes."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 and hours == 0:
        parts.append(f"{secs}s")

    return " ".join(parts) if parts else "0s"

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Alias pour calculate_distance."""
    return calculate_distance(lat1, lon1, lat2, lon2)

def interpolate_color(value: float, min_val: float, max_val: float, 
                      color_min: str = "#10B981", color_max: str = "#EF4444") -> str:
    """Interpole une couleur entre deux valeurs."""
    ratio = (value - min_val) / (max_val - min_val)
    ratio = max(0, min(1, ratio))

    # Simple interpolation (could be improved with proper RGB interpolation)
    if ratio < 0.5:
        return color_min
    return color_max

def estimate_containment_time(area_ha: float, resources_count: int, 
                               wind_speed: float, moisture: float) -> int:
    """Estime le temps de containment en minutes."""
    base_time = area_ha * 10  # 10 min par ha
    resource_factor = max(0.5, 1.0 - (resources_count * 0.1))
    wind_factor = 1.0 + (wind_speed / 100)
    moisture_factor = max(0.5, 1.0 - (moisture / 100))

    return int(base_time * resource_factor * wind_factor * moisture_factor)
