from datetime import datetime
from typing import List, Dict, Optional
import json

class IncidentTracker:
    """Suivi des incidents et historique."""

    def __init__(self):
        self.incidents = []
        self.timeline = []
        self.statistics = {}

    def add_incident(self, incident: Dict):
        """Ajoute un incident."""
        self.incidents.append(incident)
        self._add_timeline_event('INCIDENT_CREATED', incident)

    def update_incident(self, incident_id: str, updates: Dict):
        """Met à jour un incident."""
        for inc in self.incidents:
            if inc['id'] == incident_id:
                inc.update(updates)
                self._add_timeline_event('INCIDENT_UPDATED', {'id': incident_id, 'updates': updates})
                return True
        return False

    def close_incident(self, incident_id: str, reason: str = ""):
        """Clôture un incident."""
        for inc in self.incidents:
            if inc['id'] == incident_id:
                inc['status'] = 'resolved'
                inc['end_time'] = datetime.now()
                inc['closure_reason'] = reason
                self._add_timeline_event('INCIDENT_CLOSED', {'id': incident_id, 'reason': reason})
                return True
        return False

    def get_incident(self, incident_id: str) -> Optional[Dict]:
        """Récupère un incident."""
        for inc in self.incidents:
            if inc['id'] == incident_id:
                return inc
        return None

    def get_active(self) -> List[Dict]:
        """Retourne les incidents actifs."""
        return [i for i in self.incidents if i.get('status') == 'actif']

    def get_statistics(self) -> Dict:
        """Calcule les statistiques."""
        total = len(self.incidents)
        active = len(self.get_active())
        critical = len([i for i in self.incidents if i.get('priority') == 'Critique'])

        return {
            'total_incidents': total,
            'active_incidents': active,
            'critical_incidents': critical,
            'resolved_incidents': total - active,
            'average_duration': self._calculate_average_duration()
        }

    def _calculate_average_duration(self) -> float:
        """Calcule la durée moyenne des incidents résolus."""
        durations = []
        for inc in self.incidents:
            if inc.get('status') == 'resolved' and 'end_time' in inc and 'start_time' in inc:
                if isinstance(inc['end_time'], datetime) and isinstance(inc['start_time'], datetime):
                    durations.append((inc['end_time'] - inc['start_time']).total_seconds() / 3600)
        return sum(durations) / len(durations) if durations else 0.0

    def _add_timeline_event(self, event_type: str, data: Dict):
        """Ajoute un événement à la timeline."""
        self.timeline.append({
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        })

    def get_timeline(self, hours: int = 24) -> List[Dict]:
        """Récupère la timeline récente."""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=hours)
        return [t for t in self.timeline if datetime.fromisoformat(t['timestamp']) > cutoff]
