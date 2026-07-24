from datetime import datetime
from typing import List, Dict, Optional, Callable
import json

class AlertManager:
    """Gestionnaire d'alertes et notifications."""

    def __init__(self):
        self.alerts = []
        self.escalation_rules = []
        self.callbacks = []
        self.next_id = 1

    def create_alert(self, level: str, title: str, message: str, 
                     source: str = "Système", auto_escalate: bool = True) -> Dict:
        """Crée une nouvelle alerte."""
        alert = {
            'id': f"ALT-{self.next_id:03d}",
            'level': level,
            'title': title,
            'message': message,
            'source': source,
            'timestamp': datetime.now(),
            'acknowledged': False,
            'assigned_to': None,
            'escalation_level': 1,
            'auto_escalate': auto_escalate
        }
        self.next_id += 1
        self.alerts.append(alert)

        # Notifier les callbacks
        for callback in self.callbacks:
            callback(alert)

        return alert

    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Acquitte une alerte."""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['assigned_to'] = user
                return True
        return False

    def get_active_alerts(self) -> List[Dict]:
        """Retourne les alertes non acquittées."""
        return [a for a in self.alerts if not a['acknowledged']]

    def get_alerts_by_level(self, level: str) -> List[Dict]:
        """Filtre les alertes par niveau."""
        return [a for a in self.alerts if a['level'] == level]

    def register_callback(self, callback: Callable):
        """Enregistre un callback pour les nouvelles alertes."""
        self.callbacks.append(callback)

    def check_escalation(self):
        """Vérifie et escalade les alertes non acquittées."""
        for alert in self.alerts:
            if not alert['acknowledged'] and alert['auto_escalate']:
                elapsed = (datetime.now() - alert['timestamp']).total_seconds() / 60

                if elapsed > 15 and alert['escalation_level'] == 1:
                    alert['escalation_level'] = 2
                    self.create_alert(
                        'ALERTE',
                        f"Escalade: {alert['title']}",
                        f"Alerte {alert['id']} non acquittée après 15 minutes",
                        'Escalade'
                    )
                elif elapsed > 30 and alert['escalation_level'] == 2:
                    alert['escalation_level'] = 3
                    self.create_alert(
                        'CRITIQUE',
                        f"Escalade CRITIQUE: {alert['title']}",
                        f"Alerte {alert['id']} non acquittée après 30 minutes - Intervention requise",
                        'Escalade'
                    )

    def export_alerts(self, format: str = 'json') -> str:
        """Exporte les alertes."""
        if format == 'json':
            return json.dumps(self.alerts, default=str, indent=2)
        return ""
