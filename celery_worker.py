import os
from celery import Celery
from celery.signals import task_postrun
from src.optimization import TacticalOptimizer, ResourceAllocator
from src.fire_physics import PhysicalFireSimulator, AdvancedFireModel
from src.db_gis import GISDatabaseManager
import numpy as np

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", "6379")

celery_app = Celery(
    'codis_tasks',
    broker=f'redis://{redis_host}:{redis_port}/0',
    backend=f'redis://{redis_host}:{redis_port}/0',
    include=['celery_worker']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)

@celery_app.task(name='tasks.run_heavy_optimization', bind=True)
def run_heavy_optimization(self, zones_data, available_resources, objective="Minimiser risque résiduel", 
                          constraints=None, max_time=30):
    """Tâche d'optimisation lourde."""
    self.update_state(state='PROGRESS', meta={'progress': 10})

    optimizer = TacticalOptimizer(method="MILP (OR-Tools CBC)")

    self.update_state(state='PROGRESS', meta={'progress': 50})

    result = optimizer.optimize(
        zones=zones_data,
        available_resources=available_resources,
        objective=objective,
        constraints=constraints or [],
        max_time=max_time
    )

    self.update_state(state='PROGRESS', meta={'progress': 90})

    return {
        "status": "SUCCESS",
        "allocation": result.get('allocation', []),
        "solve_time": result.get('solve_time', 0),
        "method": result.get('method', ''),
        "objective_value": result.get('objective_value', 0)
    }

@celery_app.task(name='tasks.run_fire_simulation', bind=True)
def run_fire_simulation(self, grid_state, elevation, wind_speed, wind_dir, moisture, 
                        base_lat, base_lon, steps=1, model_params=None):
    """Tâche de simulation de feu."""
    self.update_state(state='PROGRESS', meta={'progress': 10})

    grid_array = np.array(grid_state)
    elev_array = np.array(elevation)

    self.update_state(state='PROGRESS', meta={'progress': 30})

    model_params = model_params or {}
    sim = AdvancedFireModel(
        base_lat=base_lat,
        base_lon=base_lon,
        rows=grid_array.shape[0],
        cols=grid_array.shape[1],
        spotting_distance=model_params.get('spotting_distance', 500),
        crown_fire=model_params.get('crown_fire', True),
        spotting=model_params.get('spotting', True),
        spotting_prob=model_params.get('spotting_prob', 0.15),
        fuel_model=model_params.get('fuel_model', 'Rothermel')
    )

    self.update_state(state='PROGRESS', meta={'progress': 50})

    for i in range(steps):
        new_grid = sim.step_propagation(grid_array, elev_array, wind_speed, wind_dir, moisture)
        grid_array = new_grid
        progress = 50 + (i + 1) / steps * 40
        self.update_state(state='PROGRESS', meta={'progress': int(progress)})

    fire_coords = sim.get_fire_geojson(new_grid)
    stats = sim.get_statistics(new_grid)

    self.update_state(state='PROGRESS', meta={'progress': 95})

    return {
        "grid": new_grid.tolist(),
        "geo_coords": fire_coords,
        "statistics": stats,
        "spotting_events": sim.get_spotting_events(),
        "crown_fire_events": sim.get_crown_fire_events()
    }

@celery_app.task(name='tasks.generate_report', bind=True)
def generate_report(self, report_type, data, format='pdf'):
    """Tâche de génération de rapport."""
    from src.services.report_service import ReportGenerator

    self.update_state(state='PROGRESS', meta={'progress': 20})

    report_gen = ReportGenerator()
    result = report_gen.generate_full_report(
        incidents=data.get('incidents', []),
        resources=data.get('resources', {}),
        simulation_data=data.get('simulation', {}),
        format=format
    )

    self.update_state(state='PROGRESS', meta={'progress': 90})

    return {
        "status": "SUCCESS",
        "report_data": result.decode('utf-8') if isinstance(result, bytes) else result,
        "format": format
    }

@celery_app.task(name='tasks.update_weather_data')
def update_weather_data(lat, lon):
    """Tâche de mise à jour des données météo."""
    from src.services.weather_service import WeatherService

    service = WeatherService()
    current = service.get_current_weather(lat, lon)
    forecast = service.get_forecast(lat, lon, hours=6)
    fwi = service.get_fire_weather_index(lat, lon)

    return {
        "current": current,
        "forecast": forecast,
        "fwi": fwi,
        "timestamp": str(datetime.now())
    }

@celery_app.task(name='tasks.check_alerts')
def check_alerts():
    """Tâche de vérification des alertes."""
    from src.services.alert_service import AlertManager

    manager = AlertManager()
    manager.check_escalation()

    return {
        "active_alerts": len(manager.get_active_alerts()),
        "timestamp": str(datetime.now())
    }

@task_postrun.connect
def close_db_connections(task_id, task, args, kwargs, retval, state, **extras):
    """Ferme les connexions DB après chaque tâche."""
    pass
