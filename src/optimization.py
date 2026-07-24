from ortools.linear_solver import pywraplp
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from enum import Enum
import time

class ObjectiveType(Enum):
    MIN_RISK = "Minimiser risque résiduel"
    MIN_RESPONSE_TIME = "Minimiser temps de réponse"
    MAX_COVERAGE = "Maximiser couverture"
    BALANCE_LOAD = "Équilibrer charge"
    MIN_COST = "Minimiser coût opérationnel"

@dataclass
class Zone:
    name: str
    lat: float
    lon: float
    priority: str
    spread_rate: float
    population: int
    area_ha: float
    distance_km: float

@dataclass
class Resource:
    name: str
    count: int
    capacity: float
    speed: float
    endurance: float
    cost_per_hour: float
    crew_size: int

class TacticalOptimizer:
    """Optimiseur tactique multi-objectif pour allocation des ressources."""

    def __init__(self, method: str = "MILP (OR-Tools CBC)"):
        self.method = method
        self.solver_times = []
        self.solutions = []

    def optimize(self, zones: List[Dict], available_resources: Dict, 
                 objective: str = "Minimiser risque résiduel",
                 constraints: List[str] = None,
                 max_time: int = 30) -> Dict:
        """Optimise l'allocation des ressources."""

        start_time = time.time()

        if "OR-Tools" in self.method:
            result = self._solve_milp(zones, available_resources, objective, constraints, max_time)
        elif "Heuristique" in self.method:
            result = self._solve_greedy(zones, available_resources, objective, constraints)
        elif "Génétique" in self.method:
            result = self._solve_genetic(zones, available_resources, objective, constraints)
        else:
            result = self._solve_milp(zones, available_resources, objective, constraints, max_time)

        elapsed = time.time() - start_time
        self.solver_times.append(elapsed)
        self.solutions.append(result)

        result['solve_time'] = round(elapsed, 3)
        result['method'] = self.method

        return result

    def _solve_milp(self, zones, available_resources, objective, constraints, max_time):
        """Résolution MILP avec OR-Tools."""

        if not zones:
            return {"status": "NO_ZONES", "allocation": []}

        num_zones = len(zones)

        # Extraire les ressources aériennes
        aircraft_resources = {}
        for name, data in available_resources.items():
            if any(kw in name for kw in ['Canadair', 'Dash', 'Hélicoptère', 'Drone']):
                aircraft_resources[name] = data

        total_aircraft = sum(d['count'] for d in aircraft_resources.values())
        if total_aircraft == 0:
            total_aircraft = 6

        # Calculer les coûts
        costs = []
        for z in zones:
            priority_factor = {'Critique': 5.0, 'Élevée': 3.0, 'Moyenne': 1.5, 'Faible': 1.0}.get(z.get('priority', 'Moyenne'), 1.0)
            population_factor = min(3.0, 1.0 + z.get('population', 0) / 2000)
            area_factor = min(2.0, 1.0 + z.get('area_ha', 0) / 200)

            cost = z.get('spread_rate', 1.0) * priority_factor * population_factor * area_factor
            costs.append(cost)

        # Solveur
        solver = pywraplp.Solver.CreateSolver('CBC')
        if not solver:
            return {"status": "SOLVER_ERROR", "allocation": []}

        # Variables de décision
        x = {}
        for i in range(num_zones):
            for j in range(total_aircraft):
                x[i, j] = solver.IntVar(0, 1, f'x_{i}_{j}')

        # Contraintes
        for j in range(total_aircraft):
            solver.Add(sum(x[i, j] for i in range(num_zones)) <= 1)

        max_per_zone = 4
        for i in range(num_zones):
            solver.Add(sum(x[i, j] for j in range(total_aircraft)) <= max_per_zone)

        for i in range(num_zones):
            if zones[i].get('priority') == 'Critique':
                solver.Add(sum(x[i, j] for j in range(total_aircraft)) >= 1)

        # Fonction objectif
        objective_expr = []
        for i in range(num_zones):
            assigned = sum(x[i, j] for j in range(total_aircraft))
            risk_reduction = assigned * (costs[i] / 2.0)
            residual_risk = costs[i] - risk_reduction
            objective_expr.append(residual_risk)
            objective_expr.append(assigned * 0.1 * costs[i])

        solver.Minimize(sum(objective_expr))

        status = solver.Solve()

        allocation = []
        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            for i in range(num_zones):
                assigned_count = int(sum(x[i, j].solution_value() for j in range(total_aircraft)))
                risk_red = assigned_count * (costs[i] / 2.0)
                residual = costs[i] - risk_red
                coverage = min(100, assigned_count * 25)

                allocation.append({
                    "zone": zones[i].get('name', f'Zone {i}'),
                    "avions_assignes": assigned_count,
                    "risque_residuel": round(max(0, residual), 2),
                    "couverture_pct": coverage,
                    "temps_reponse_min": round(zones[i].get('distance_km', 20) / 200 * 60, 1),
                    "population_protegee": int(zones[i].get('population', 0) * coverage / 100),
                    "priorite": zones[i].get('priority', 'Moyenne')
                })

        return {
            "status": "OPTIMAL" if status == pywraplp.Solver.OPTIMAL else "FEASIBLE",
            "allocation": allocation,
            "total_aircraft": total_aircraft,
            "objective_value": round(solver.Objective().Value(), 2) if allocation else 0
        }

    def _solve_greedy(self, zones, available_resources, objective, constraints):
        """Heuristique gloutonne rapide."""

        total_aircraft = sum(d['count'] for d in available_resources.values() 
                           if any(kw in k for k, d in available_resources.items() 
                                 for kw in ['Canadair', 'Dash', 'Hélicoptère', 'Drone']))
        if total_aircraft == 0:
            total_aircraft = 6

        sorted_zones = sorted(enumerate(zones), 
                            key=lambda x: ({'Critique': 4, 'Élevée': 3, 'Moyenne': 2, 'Faible': 1}.get(x[1].get('priority', ''), 0), x[1].get('spread_rate', 0)),
                            reverse=True)

        allocation = []
        remaining_aircraft = total_aircraft

        for idx, zone in sorted_zones:
            if remaining_aircraft <= 0:
                assigned = 0
            else:
                priority = zone.get('priority', 'Moyenne')
                if priority == 'Critique':
                    assigned = min(4, max(2, remaining_aircraft // max(1, len(zones) // 2)))
                elif priority == 'Élevée':
                    assigned = min(3, max(1, remaining_aircraft // max(1, len(zones))))
                else:
                    assigned = min(2, remaining_aircraft)

                remaining_aircraft -= assigned

            cost = zone.get('spread_rate', 1.0) * {'Critique': 5.0, 'Élevée': 3.0, 'Moyenne': 1.5}.get(priority, 1.0)
            risk_red = assigned * (cost / 2.0)

            allocation.append({
                "zone": zone.get('name', f'Zone {idx}'),
                "avions_assignes": assigned,
                "risque_residuel": round(max(0, cost - risk_red), 2),
                "couverture_pct": min(100, assigned * 25),
                "temps_reponse_min": round(zone.get('distance_km', 20) / 200 * 60, 1),
                "population_protegee": int(zone.get('population', 0) * min(100, assigned * 25) / 100),
                "priorite": priority
            })

        return {
            "status": "HEURISTIC",
            "allocation": allocation,
            "total_aircraft": total_aircraft,
            "objective_value": sum(a['risque_residuel'] for a in allocation)
        }

    def _solve_genetic(self, zones, available_resources, objective, constraints):
        return self._solve_greedy(zones, available_resources, objective, constraints)


class ResourceAllocator:
    """Allocateur de ressources multi-types avec routage."""

    def __init__(self):
        self.allocations = []

    def solve_vrp(self, depots, zones, vehicles):
        return self._allocate_direct(depots, zones, vehicles)

    def _allocate_direct(self, depots, zones, vehicles):
        allocations = []
        for zone in zones:
            best_depot = min(depots, key=lambda d: self._haversine(d['lat'], d['lon'], zone['lat'], zone['lon']))
            distance = self._haversine(best_depot['lat'], best_depot['lon'], zone['lat'], zone['lon'])
            allocations.append({
                'zone': zone['name'],
                'depot': best_depot['name'],
                'distance_km': round(distance, 2),
                'eta_minutes': round(distance / 60 * 60, 1),
                'vehicles_assigned': 1
            })
        return allocations

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        return 2 * R * np.arcsin(np.sqrt(a))

    def optimize_ground_resources(self, zones, resources, constraints):
        allocations = []
        for zone in zones:
            needed = zone.get('area_ha', 100) / 50
            priority = zone.get('priority', 'Moyenne')
            if priority == 'Critique':
                needed *= 2
            elif priority == 'Élevée':
                needed *= 1.5
            allocations.append({
                'zone': zone['name'],
                'units_needed': int(np.ceil(needed)),
                'priority': priority,
                'estimated_time': round(zone.get('distance_km', 20) / 40 * 60, 1)
            })
        return allocations
