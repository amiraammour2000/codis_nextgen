from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import base64
from io import BytesIO

class ReportGenerator:
    """Générateur de rapports multi-format."""

    def __init__(self):
        self.templates = {}
        self._load_templates()

    def _load_templates(self):
        """Charge les templates de rapports."""
        self.templates = {
            'full': self._template_full(),
            'tactical': self._template_tactical(),
            'simulation': self._template_simulation(),
            'resources': self._template_resources()
        }

    def generate_full_report(self, incidents, resources, simulation_data, 
                            format='pdf', sections=None, date_range=None) -> bytes:
        """Génère un rapport complet."""

        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'version': '3.0',
                'system': 'CODIS NEXT-GEN PRO',
                'classification': 'CONFIDENTIEL'
            },
            'summary': self._generate_summary(incidents, resources),
            'incidents': incidents,
            'resources': resources,
            'simulation': simulation_data,
            'recommendations': self._generate_recommendations(incidents, resources)
        }

        if format == 'json':
            return json.dumps(report_data, default=str, indent=2).encode('utf-8')
        elif format == 'pdf':
            return self._generate_pdf(report_data, sections)
        elif format == 'excel':
            return self._generate_excel(report_data)
        elif format == 'html':
            return self._generate_html(report_data)
        else:
            return json.dumps(report_data, default=str, indent=2).encode('utf-8')

    def _generate_summary(self, incidents, resources):
        """Génère le résumé exécutif."""
        total_incidents = len(incidents)
        critical = len([i for i in incidents if i.get('priority') == 'Critique'])
        total_resources = sum(v.get('count', 0) for v in resources.values())

        return {
            'total_incidents': total_incidents,
            'critical_incidents': critical,
            'total_resources': total_resources,
            'status': 'ACTIF' if total_incidents > 0 else 'VEILLE',
            'last_update': datetime.now().isoformat()
        }

    def _generate_recommendations(self, incidents, resources):
        """Génère des recommandations."""
        recommendations = []

        critical_incidents = [i for i in incidents if i.get('priority') == 'Critique']
        if len(critical_incidents) > 2:
            recommendations.append({
                'priority': 'HAUTE',
                'category': 'Ressources',
                'message': 'Demande de renforts : plus de 2 incidents critiques simultanés'
            })

        if any(i.get('wind_speed', 0) > 60 for i in incidents):
            recommendations.append({
                'priority': 'HAUTE',
                'category': 'Météo',
                'message': 'Conditions venteuses extrêmes - Suspension des opérations aériennes recommandée'
            })

        return recommendations

    def _generate_pdf(self, data, sections):
        """Génère un PDF (simulation)."""
        # Retourne des données JSON encodées comme placeholder
        return json.dumps(data, default=str).encode('utf-8')

    def _generate_excel(self, data):
        """Génère un Excel (simulation)."""
        return json.dumps(data, default=str).encode('utf-8')

    def _generate_html(self, data):
        """Génère un HTML."""
        html = f"""
        <html>
        <head><title>Codis Report</title></head>
        <body>
            <h1>Rapport CODIS - {data['metadata']['generated_at']}</h1>
            <p>Classification: {data['metadata']['classification']}</p>
            <h2>Résumé</h2>
            <p>Incidents: {data['summary']['total_incidents']}</p>
            <p>Ressources: {data['summary']['total_resources']}</p>
        </body>
        </html>
        """
        return html.encode('utf-8')

    def _template_full(self):
        return "template_full"

    def _template_tactical(self):
        return "template_tactical"

    def _template_simulation(self):
        return "template_simulation"

    def _template_resources(self):
        return "template_resources"
