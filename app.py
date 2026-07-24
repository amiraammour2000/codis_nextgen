import streamlit as st
import numpy as np
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import altair as alt
from datetime import datetime, timedelta
import json
import time
import threading
import asyncio
from pathlib import Path
import base64
from io import BytesIO

# Imports internes
from src.fire_physics import PhysicalFireSimulator, AdvancedFireModel
from src.db_gis import GISDatabaseManager
from src.optimization import TacticalOptimizer, ResourceAllocator
from src.services.weather_service import WeatherService
from src.services.iot_service import IoTTelemetryService
from src.services.alert_service import AlertManager
from src.services.report_service import ReportGenerator
from src.models.scenario import ScenarioManager
from src.models.incident import IncidentTracker
from src.utils.styling import apply_custom_css, render_metric_card, render_status_badge
from src.utils.helpers import format_coordinates, calculate_distance, get_priority_color

# Configuration de la page
st.set_page_config(
    page_title="CODIS NEXT-GEN PRO | C4ISR Commandement",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://codis-nextgen.pro/support',
        'Report a bug': 'https://codis-nextgen.pro/issues',
        'About': 'CODIS NEXT-GEN PRO v3.0 - Système de Commandement et Contrôle'
    }
)

# Application du CSS personnalisé
apply_custom_css()

# ═══════════════════════════════════════════════════════════════
# INITIALISATION DU SESSION STATE
# ═══════════════════════════════════════════════════════════════
def init_session_state():
    defaults = {
        'fire_grid': None,
        'fire_history': [],
        'iot_tracks': [],
        'iot_history': {},
        'elevation': None,
        'fuel_moisture_grid': None,
        'wind_field': None,
        'active_incidents': [],
        'resolved_incidents': [],
        'alerts': [],
        'scenario_manager': ScenarioManager(),
        'incident_tracker': IncidentTracker(),
        'simulation_step': 0,
        'last_update': datetime.now(),
        'selected_sector': None,
        'map_center': [43.6045, 7.0542],
        'zoom_level': 12,
        'weather_data': None,
        'aircraft_allocation': None,
        'resource_status': {},
        'show_heatmap': True,
        'show_contours': True,
        'show_iot': True,
        'show_perimeters': True,
        'show_wind': True,
        'dark_mode': True,
        'auto_refresh': False,
        'refresh_interval': 5,
        'ws_connected': False,
        'notification_queue': [],
        'user_role': 'commander',
        'language': 'fr',
        'units': 'metric',
        'export_format': 'pdf',
        'simulation_speed': 1.0,
        'prediction_horizon': 6,
        'confidence_interval': 0.95,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ═══════════════════════════════════════════════════════════════
# HEADER PRINCIPAL
# ═══════════════════════════════════════════════════════════════
header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns([2, 1, 1, 1, 1])

with header_col1:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 32px;">🛡️</span>
        <div>
            <h1 style="margin: 0; font-size: 24px; color: #E63946; font-weight: 800; letter-spacing: -0.5px;">
                CODIS NEXT-GEN PRO
            </h1>
            <p style="margin: 0; font-size: 11px; color: #64748B; letter-spacing: 2px; text-transform: uppercase;">
                Commandement · Contrôle · Communications · Intelligence · Surveillance · Reconnaissance
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with header_col2:
    current_time = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div style="text-align: center; padding: 8px; background: #1E293B; border-radius: 8px; border: 1px solid #334155;">
        <p style="margin: 0; font-size: 10px; color: #64748B;">HEURE UTC</p>
        <p style="margin: 0; font-size: 18px; font-weight: 700; color: #F1F5F9;">{current_time}</p>
    </div>
    """, unsafe_allow_html=True)

with header_col3:
    alert_count = len([a for a in st.session_state.alerts if not a.get('acknowledged', False)])
    alert_color = "#EF4444" if alert_count > 0 else "#10B981"
    st.markdown(f"""
    <div style="text-align: center; padding: 8px; background: #1E293B; border-radius: 8px; border: 1px solid #334155;">
        <p style="margin: 0; font-size: 10px; color: #64748B;">ALERTES ACTIVES</p>
        <p style="margin: 0; font-size: 18px; font-weight: 700; color: {alert_color};">{alert_count}</p>
    </div>
    """, unsafe_allow_html=True)

with header_col4:
    active_fires = len(st.session_state.active_incidents)
    st.markdown(f"""
    <div style="text-align: center; padding: 8px; background: #1E293B; border-radius: 8px; border: 1px solid #334155;">
        <p style="margin: 0; font-size: 10px; color: #64748B;">INCIDENTS ACTIFS</p>
        <p style="margin: 0; font-size: 18px; font-weight: 700; color: #F59E0B;">{active_fires}</p>
    </div>
    """, unsafe_allow_html=True)

with header_col5:
    st.markdown("""
    <div style="text-align: center; padding: 8px; background: #1E293B; border-radius: 8px; border: 1px solid #334155;">
        <p style="margin: 0; font-size: 10px; color: #64748B;">STATUT SYSTÈME</p>
        <p style="margin: 0; font-size: 14px; font-weight: 700; color: #10B981;">● OPÉRATIONNEL</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin: 8px 0; border-color: #334155;'>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SIDEBAR - PANNEAU DE COMMANDEMENT
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 12px; background: linear-gradient(135deg, #1E293B, #0F172A); 
                border-radius: 12px; border: 1px solid #E63946; margin-bottom: 16px;">
        <h3 style="margin: 0; color: #E63946; font-size: 14px; font-weight: 700;">⚙️ PANNEAU DE COMMANDEMENT</h3>
        <p style="margin: 4px 0 0 0; font-size: 10px; color: #64748B;">Configuration tactique globale</p>
    </div>
    """, unsafe_allow_html=True)

    sidebar_tab = st.radio(
        "",
        ["🌍 Environnement", "🎯 Scénario", "📡 Ressources", "⚡ Système"],
        label_visibility="collapsed"
    )

    if sidebar_tab == "🌍 Environnement":
        st.markdown("<p style='color: #94A3B8; font-size: 11px; font-weight: 600; margin-top: 12px;'>🌡️ CONDITIONS MÉTÉO</p>", unsafe_allow_html=True)

        col_w1, col_w2 = st.columns(2)
        with col_w1:
            wind_speed = st.slider("Vent (km/h)", 0, 150, 45, help="Vitesse du vent moyen")
        with col_w2:
            wind_dir = st.slider("Dir. (°)", 0, 360, 180, help="Direction du vent en degrés")

        moisture = st.slider("💧 Humidité (%)", 0, 100, 25, help="Taux d'humidité relative")
        temp = st.slider("🌡️ Température (°C)", -10, 50, 28, help="Température ambiante")

        st.markdown("<p style='color: #94A3B8; font-size: 11px; font-weight: 600; margin-top: 16px;'>🔥 COMPORTEMENT DU FEU</p>", unsafe_allow_html=True)

        fuel_type = st.selectbox(
            "Type de combustible",
            ["Forêt méditerranéenne", "Maquis", "Prairie", "Zone urbaine", "Zone industrielle", "Tourbière"],
            help="Type de végétation dominante"
        )

        slope = st.slider("Pente moyenne (%)", 0, 60, 15, help="Pente moyenne du terrain")

        st.markdown("<p style='color: #94A3B8; font-size: 11px; font-weight: 600; margin-top: 16px;'>🗺️ ZONE D'OPÉRATION</p>", unsafe_allow_html=True)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            base_lat = st.number_input("Latitude", value=43.6045, format="%.6f", step=0.0001)
        with col_c2:
            base_lon = st.number_input("Longitude", value=7.0542, format="%.6f", step=0.0001)

        op_name = st.text_input("Nom de l'opération", value="OPÉRATION PROMÉTHÉE", help="Nom de code de l'opération")

        if st.button("🚀 Initialiser le Théâtre d'Opérations", type="primary", use_container_width=True):
            sim = PhysicalFireSimulator(base_lat, base_lon, rows=60, cols=60, cell_size_m=100)
            st.session_state.fire_grid = np.zeros((60, 60))
            st.session_state.fire_grid[30, 30] = 2
            st.session_state.elevation = np.random.uniform(50, 800, (60, 60))
            st.session_state.fuel_moisture_grid = np.full((60, 60), moisture)
            st.session_state.wind_field = np.full((60, 60, 2), [wind_speed, wind_dir])
            st.session_state.map_center = [base_lat, base_lon]
            st.session_state.simulation_step = 0

            incident = {
                'id': f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                'name': op_name,
                'lat': base_lat,
                'lon': base_lon,
                'start_time': datetime.now(),
                'status': 'actif',
                'priority': 'Critique',
                'type': 'Feu de forêt',
                'wind_speed': wind_speed,
                'wind_dir': wind_dir,
                'moisture': moisture,
                'temperature': temp,
                'fuel_type': fuel_type,
                'slope': slope,
                'affected_area_ha': 0.0,
                'resources_deployed': 0,
                'estimated_containment': 'N/A'
            }
            st.session_state.active_incidents.append(incident)
            st.session_state.incident_tracker.add_incident(incident)
            st.success(f"✅ Théâtre d'opérations initialisé : {op_name}")
            st.rerun()

    elif sidebar_tab == "🎯 Scénario":
        st.markdown("<p style='color: #94A3B8; font-size: 11px; font-weight: 600; margin-top: 12px;'>📋 GESTION DES SCÉNARIOS</p>", unsafe_allow_html=True)

        scenario_action = st.selectbox("Action", ["Nouveau scénario", "Charger scénario", "Sauvegarder", "Exporter"])

        if scenario_action == "Nouveau scénario":
            scenario_name = st.text_input("Nom du scénario")
            scenario_desc = st.text_area("Description", height=80)

            st.markdown("<p style='color: #94A3B8; font-size: 11px; font-weight: 600;'>🔥 Paramètres d'ignition</p>", unsafe_allow_html=True)
            ignition_points = st.number_input("Points d'ignition", 1, 10, 1)
            ignition_intensity = st.slider("Intensité initiale", 1, 10, 3)

            if st.button("💾 Créer le scénario", use_container_width=True):
                scenario = st.session_state.scenario_manager.create_scenario(
                    name=scenario_name,
                    description=scenario_desc,
                    ignition_points=ignition_points,
                    ignition_intensity=ignition_intensity,
                    env_params={
                        'wind_speed': wind_speed if 'wind_speed' in locals() else 45,
                        'wind_dir': wind_dir if 'wind_dir' in locals() else 180,
                        'moisture': moisture if 'moisture' in locals() else 25
                    }
                )
                st.success(f"Scénario '{scenario_name}' créé")

        elif scenario_action == "Charger scénario":
            scenarios = st.session_state.scenario_manager.list_scenarios()
            if scenarios:
                selected = st.selectbox("Scénarios disponibles", [s['name'] for s in scenarios])
                if st.button("📂 Charger", use_container_width=True):
                    st.session_state.scenario_manager.load_scenario(selected)
                    st.success(f"Scénario '{selected}' chargé")
            else:
                st.info("Aucun scénario sauvegardé")

        st.markdown("<hr style='border-color: #334155; margin: 16px 0;'>", unsafe_allow_html=True)

        st.markdown("<p style='color: #94A3B8; font-size: 11px; font-weight: 600;'>📊 Prédiction temporelle</p>", unsafe_allow_html=True)
        st.session_state.prediction_horizon = st.slider("Horizon (h)", 1, 24, 6)
        st.session_state.simulation_speed = st.slider("Vitesse sim.", 0.5, 5.0, 1.0, 0.5)

    elif sidebar_tab == "📡 Ressources":
        st.markdown("<p style='color: #94A3B8; font-size: 11px; font-weight: 600; margin-top: 12px;'>✈️ FLOTTE AÉRIENNE</p>", unsafe_allow_html=True)

        aircraft_types = {
            "Canadair CL-415": {"capacity": 6000, "speed": 330, "endurance": 3.5},
            "Dash 8 Q400-MR": {"capacity": 10000, "speed": 350, "endurance": 4.0},
            "Hélicoptère Écureuil H125": {"capacity": 900, "speed": 220, "endurance": 3.0},
            "Hélicoptère Puma": {"capacity": 2500, "speed": 250, "endurance": 3.5},
            "Drone Reconnaissance": {"capacity": 0, "speed": 80, "endurance": 2.0},
        }

        for name, specs in aircraft_types.items():
            count = st.number_input(f"{name}", 0, 20, 2 if name == "Canadair CL-415" else 0)
            if count > 0:
                st.session_state.resource_status[name] = {
                    'count': count,
                    'available': count,
                    'deployed': 0,
                    'specs': specs
                }

        st.markdown("<p style='color: #94A3B8; font-size: 11px; font-weight: 600; margin-top: 16px;'>🚒 MOYENS TERRESTRES</p>", unsafe_allow_html=True)

        ground_types = {
            "CCF (Camion Citerne Feux)": {"capacity": 12000, "crew": 4},
            "FPT (Fourgon Pompe Tonne)": {"capacity": 3000, "crew": 6},
            "VLTT (Véhicule Léger Tout Terrain)": {"capacity": 500, "crew": 3},
            "Bulldozer": {"capacity": 0, "crew": 1},
        }

        for name, specs in ground_types.items():
            count = st.number_input(f"{name}", 0, 50, 5 if name == "CCF" else 0)
            if count > 0:
                st.session_state.resource_status[name] = {
                    'count': count,
                    'available': count,
                    'deployed': 0,
                    'specs': specs
                }

        total_aircraft = sum(v['count'] for k, v in st.session_state.resource_status.items() 
                            if k in aircraft_types)
        st.metric("Flotte totale", f"{total_aircraft} unités")

    elif sidebar_tab == "⚡ Système":
        st.markdown("<p style='color: #94A3B8; font-size: 11px; font-weight: 600; margin-top: 12px;'>🔧 CONFIGURATION SYSTÈME</p>", unsafe_allow_html=True)

        st.session_state.auto_refresh = st.toggle("🔄 Rafraîchissement auto", value=False)
        if st.session_state.auto_refresh:
            st.session_state.refresh_interval = st.slider("Intervalle (s)", 1, 30, 5)

        st.session_state.show_heatmap = st.toggle("🔥 Afficher heatmap", value=True)
        st.session_state.show_contours = st.toggle("📐 Afficher contours", value=True)
        st.session_state.show_iot = st.toggle("📡 Afficher IoT", value=True)
        st.session_state.show_perimeters = st.toggle("🗺️ Afficher périmètres", value=True)
        st.session_state.show_wind = st.toggle("💨 Afficher vent", value=True)

        st.markdown("<hr style='border-color: #334155; margin: 16px 0;'>", unsafe_allow_html=True)

        st.markdown("<p style='color: #94A3B8; font-size: 11px; font-weight: 600;'>📤 EXPORT</p>", unsafe_allow_html=True)
        export_format = st.selectbox("Format", ["PDF", "Excel", "GeoJSON", "KML", "Shapefile"])

        if st.button("📥 Générer le rapport", type="secondary", use_container_width=True):
            report_gen = ReportGenerator()
            report = report_gen.generate_full_report(
                incidents=st.session_state.active_incidents,
                resources=st.session_state.resource_status,
                simulation_data={
                    'grid': st.session_state.fire_grid,
                    'history': st.session_state.fire_history,
                    'elevation': st.session_state.elevation
                },
                format=export_format.lower()
            )
            st.download_button(
                label=f"⬇️ Télécharger ({export_format})",
                data=report,
                file_name=f"CODIS_Rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format.lower()}",
                mime="application/octet-stream",
                use_container_width=True
            )

# ═══════════════════════════════════════════════════════════════
# CONTENU PRINCIPAL - TABS
# ═══════════════════════════════════════════════════════════════
tabs = st.tabs([
    "🗺️ COP Tactique",
    "🧠 Optimisation",
    "🔬 Simulation",
    "📊 Intelligence",
    "📡 Télémétrie",
    "⚠️ Alertes",
    "📋 Rapports"
])

# ═══════════════════════════════════════════════════════════════
# TAB 1: COP TACTIQUE
# ═══════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown("""
    <div style="background: #1E293B; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;">
        <h3 style="margin: 0; color: #F1F5F9; font-size: 16px;">🗺️ Common Operating Picture (COP)</h3>
        <p style="margin: 4px 0 0 0; font-size: 11px; color: #64748B;">Vue tactique unifiée temps réel</p>
    </div>
    """, unsafe_allow_html=True)

    map_col, info_col = st.columns([3, 1])

    with map_col:
        m = folium.Map(
            location=st.session_state.map_center,
            zoom_start=st.session_state.zoom_level,
            tiles="CartoDB dark_matter" if st.session_state.dark_mode else "CartoDB positron",
            control_scale=True
        )

        folium.TileLayer('OpenStreetMap', name='OSM', control=True).add_to(m)
        folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                        name='Satellite', attr='Esri', control=True).add_to(m)

        # Elevation heatmap
        if st.session_state.elevation is not None and st.session_state.show_heatmap:
            from folium.plugins import HeatMap
            elev_coords = []
            sim = PhysicalFireSimulator(base_lat, base_lon, rows=60, cols=60) if 'base_lat' in locals() else None
            if sim:
                for r in range(60):
                    for c in range(60):
                        lat = base_lat - (r * sim.lat_step)
                        lon = base_lon + (c * sim.lon_step)
                        elev_coords.append([lat, lon, float(st.session_state.elevation[r, c])])
                HeatMap(elev_coords, radius=15, blur=25, max_zoom=13, 
                       gradient={0.4: '#3B82F6', 0.65: '#F59E0B', 1: '#EF4444'}).add_to(m)

        # Fire front
        if st.session_state.fire_grid is not None:
            sim = PhysicalFireSimulator(base_lat, base_lon, rows=60, cols=60) if 'base_lat' in locals() else None
            if sim:
                fire_coords = sim.get_fire_geojson(st.session_state.fire_grid)
                for coords in fire_coords:
                    folium.CircleMarker(
                        location=coords,
                        radius=35,
                        color='#EF4444',
                        fill=True,
                        fill_color='#EF4444',
                        fill_opacity=0.6,
                        popup="🔥 Front de feu actif"
                    ).add_to(m)

        # DB sectors
        db = GISDatabaseManager()
        sectors = db.fetch_active_sectors()
        for zone in sectors:
            color = "#DC2626" if zone.get('priority') == 'Critique' else "#F59E0B"
            folium.Marker(
                [zone['lat'], zone['lon']],
                popup=f"<b>{zone['name']}</b><br>Propag: {zone.get('spread_rate', 'N/A')} km/h",
                icon=folium.DivIcon(
                    html=f'<div style="background: {color}; width: 24px; height: 24px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">⚠</div>'
                )
            ).add_to(m)

        # IoT tracks
        if st.session_state.show_iot:
            for track in st.session_state.iot_tracks:
                icon_color = "#3B82F6" if track.get('type') == 'truck' else "#8B5CF6"
                icon_symbol = "🚒" if track.get('type') == 'truck' else "🚁"
                folium.Marker(
                    [track['lat'], track['lon']],
                    popup=f"<b>{track['id']}</b><br>Type: {track.get('type', 'Inconnu')}",
                    icon=folium.DivIcon(
                        html=f'<div style="background: {icon_color}; width: 28px; height: 28px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; font-size: 14px;">{icon_symbol}</div>'
                    )
                ).add_to(m)

        folium.LayerControl().add_to(m)
        st_folium(m, width="100%", height=650, returned_objects=[])

    with info_col:
        st.markdown("""
        <div style="background: #1E293B; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
            <h4 style="margin: 0; color: #F1F5F9; font-size: 13px;">📊 MÉTRIQUES TEMPS RÉEL</h4>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.fire_grid is not None:
            active_cells = np.sum(st.session_state.fire_grid == 2)
            burned_cells = np.sum(st.session_state.fire_grid == 1)
            affected_ha = (active_cells + burned_cells) * 1.0

            render_metric_card("🔥 Surface active", f"{active_cells} cellules", "#EF4444")
            render_metric_card("💨 Surface brûlée", f"{burned_cells} cellules", "#7C2D12")
            render_metric_card("📏 Surface totale", f"{affected_ha:.1f} ha", "#F59E0B")
            render_metric_card("📐 Taux propagation", f"{active_cells / max(burned_cells, 1):.2f}", "#3B82F6")
        else:
            st.info("Initialisez la grille pour voir les métriques")

        st.markdown("<hr style='border-color: #334155; margin: 12px 0;'>", unsafe_allow_html=True)

        st.markdown("""
        <div style="background: #1E293B; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
            <h4 style="margin: 0; color: #F1F5F9; font-size: 13px;">⚠️ INCIDENTS ACTIFS</h4>
        </div>
        """, unsafe_allow_html=True)

        for incident in st.session_state.active_incidents:
            priority_color = get_priority_color(incident['priority'])
            elapsed = datetime.now() - incident['start_time']
            st.markdown(f"""
            <div style="background: #0F172A; padding: 10px; border-radius: 6px; border-left: 3px solid {priority_color}; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 600; font-size: 12px; color: #F1F5F9;">{incident['name']}</span>
                    <span style="background: {priority_color}; color: white; font-size: 9px; padding: 2px 6px; border-radius: 4px;">{incident['priority']}</span>
                </div>
                <p style="margin: 4px 0 0 0; font-size: 10px; color: #64748B;">
                    ⏱️ {elapsed.seconds // 3600}h{(elapsed.seconds % 3600) // 60}m
                </p>
            </div>
            """, unsafe_allow_html=True)

        if not st.session_state.active_incidents:
            st.info("Aucun incident actif")


# ═══════════════════════════════════════════════════════════════
# TAB 2: OPTIMISATION TACTIQUE
# ═══════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("""
    <div style="background: #1E293B; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;">
        <h3 style="margin: 0; color: #F1F5F9; font-size: 16px;">🧠 Optimisation Tactique Multi-Critères</h3>
        <p style="margin: 4px 0 0 0; font-size: 11px; color: #64748B;">Solveur MILP avancé · Allocation optimale · Minimisation du risque résiduel</p>
    </div>
    """, unsafe_allow_html=True)

    opt_col1, opt_col2 = st.columns([1, 1])

    with opt_col1:
        st.markdown("""
        <div style="background: #1E293B; padding: 12px; border-radius: 8px;">
            <h4 style="margin: 0 0 12px 0; color: #F1F5F9; font-size: 14px;">⚙️ Paramètres du Solveur</h4>
        </div>
        """, unsafe_allow_html=True)

        solver_method = st.selectbox(
            "Algorithme",
            ["MILP (OR-Tools CBC)", "MILP (OR-Tools SCIP)", "Heuristique Gloutonne", "Algorithme Génétique", "Recuit Simulé"],
            help="Méthode de résolution de l'optimisation"
        )

        objective = st.selectbox(
            "Objectif",
            ["Minimiser risque résiduel", "Minimiser temps de réponse", "Maximiser couverture", 
             "Équilibrer charge", "Minimiser coût opérationnel"],
            help="Fonction objectif principale"
        )

        constraints = st.multiselect(
            "Contraintes",
            ["Capacité aéroport", "Temps de vol max", "Zone d'exclusion", "Priorité population", 
             "Météo restrictive", "Nuit/Jour", "Maintenance"],
            default=["Capacité aéroport", "Temps de vol max", "Priorité population"],
            help="Contraintes opérationnelles à respecter"
        )

        max_compute_time = st.slider("Temps max calcul (s)", 1, 300, 30, help="Timeout du solveur")

        if st.button("🚀 Lancer l'Optimisation", type="primary", use_container_width=True):
            with st.spinner("🧮 Solveur en cours d'exécution..."):
                time.sleep(2)

                zones_data = []
                if st.session_state.active_incidents:
                    for inc in st.session_state.active_incidents:
                        zones_data.append({
                            'name': inc['name'],
                            'lat': inc['lat'],
                            'lon': inc['lon'],
                            'priority': inc['priority'],
                            'spread_rate': inc.get('wind_speed', 45) * 0.1,
                            'population': np.random.randint(100, 5000),
                            'area_ha': np.random.randint(10, 500),
                            'distance_km': np.random.uniform(5, 100)
                        })
                else:
                    zones_data = [
                        {'name': 'Zone Alpha', 'lat': 43.61, 'lon': 7.06, 'priority': 'Critique', 'spread_rate': 4.5, 'population': 2500, 'area_ha': 150, 'distance_km': 15},
                        {'name': 'Zone Beta', 'lat': 43.59, 'lon': 7.03, 'priority': 'Élevée', 'spread_rate': 3.2, 'population': 800, 'area_ha': 80, 'distance_km': 25},
                        {'name': 'Zone Gamma', 'lat': 43.62, 'lon': 7.08, 'priority': 'Moyenne', 'spread_rate': 2.1, 'population': 200, 'area_ha': 45, 'distance_km': 40},
                        {'name': 'Zone Delta', 'lat': 43.58, 'lon': 7.05, 'priority': 'Critique', 'spread_rate': 5.8, 'population': 4200, 'area_ha': 220, 'distance_km': 10},
                    ]

                optimizer = TacticalOptimizer(method=solver_method)
                available_aircraft = sum(v['count'] for k, v in st.session_state.resource_status.items() 
                                        if 'Canadair' in k or 'Dash' in k or 'Hélicoptère' in k)

                result = optimizer.optimize(
                    zones=zones_data,
                    available_resources=st.session_state.resource_status,
                    objective=objective,
                    constraints=constraints,
                    max_time=max_compute_time
                )

                st.session_state.aircraft_allocation = result
                st.success("✅ Optimisation terminée — Solution optimale trouvée!")

    with opt_col2:
        if st.session_state.aircraft_allocation:
            st.markdown("""
            <div style="background: #1E293B; padding: 12px; border-radius: 8px;">
                <h4 style="margin: 0 0 12px 0; color: #F1F5F9; font-size: 14px;">📊 Résultats d'Allocation</h4>
            </div>
            """, unsafe_allow_html=True)

            alloc_df = pd.DataFrame(st.session_state.aircraft_allocation['allocation'])
            st.dataframe(
                alloc_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "zone": st.column_config.TextColumn("Zone", width="medium"),
                    "avions_assignes": st.column_config.NumberColumn("✈️ Avions", width="small"),
                    "risque_residuel": st.column_config.NumberColumn("⚠️ Risque Résiduel", width="medium"),
                    "couverture_pct": st.column_config.NumberColumn("📏 Couverture %", width="medium"),
                    "temps_reponse_min": st.column_config.NumberColumn("⏱️ Tps Réponse (min)", width="medium"),
                }
            )

            fig = go.Figure(data=[
                go.Bar(
                    x=alloc_df['zone'],
                    y=alloc_df['avions_assignes'],
                    marker_color=['#EF4444' if r > 10 else '#F59E0B' if r > 5 else '#10B981' 
                                for r in alloc_df['risque_residuel']],
                    text=alloc_df['avions_assignes'],
                    textposition='auto',
                )
            ])
            fig.update_layout(
                title="Allocation des ressources par zone",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#F1F5F9',
                xaxis_title="Zone",
                yaxis_title="Nombre d'avions",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

            max_risk = alloc_df['risque_residuel'].max()
            if max_risk > 15:
                st.error(f"🚨 ALERTE CRITIQUE : Risque résiduel maximal de {max_risk:.1f}. Renforts nécessaires!")
            elif max_risk > 8:
                st.warning(f"⚠️ Risque résiduel élevé ({max_risk:.1f}). Surveillance renforcée recommandée.")
            else:
                st.success(f"✅ Risque résiduel maîtrisé (max: {max_risk:.1f})")
        else:
            st.info("Lancez l'optimisation pour voir les résultats")

# ═══════════════════════════════════════════════════════════════
# TAB 3: SIMULATION (Jumeau Numérique)
# ═══════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("""
    <div style="background: #1E293B; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;">
        <h3 style="margin: 0; color: #F1F5F9; font-size: 16px;">🔬 Jumeau Numérique Avancé</h3>
        <p style="margin: 4px 0 0 0; font-size: 11px; color: #64748B;">Simulation physique multi-échelle · Prédiction temporelle · Modélisation comportementale</p>
    </div>
    """, unsafe_allow_html=True)

    sim_col1, sim_col2 = st.columns([1, 2])

    with sim_col1:
        st.markdown("""
        <div style="background: #1E293B; padding: 12px; border-radius: 8px;">
            <h4 style="margin: 0 0 12px 0; color: #F1F5F9; font-size: 14px;">🎮 Contrôles Simulation</h4>
        </div>
        """, unsafe_allow_html=True)

        sim_mode = st.selectbox(
            "Mode de simulation",
            ["Pas à pas (+1h)", "Auto (séquence)", "Prédiction long terme", "Scénario multi-feux", "Analyse de sensibilité"],
            help="Mode d'exécution de la simulation"
        )

        num_steps = st.number_input("Nombre de pas", 1, 48, 1, help="Nombre d'itérations")

        physics_params = st.expander("🔧 Paramètres physiques avancés")
        with physics_params:
            spotting_distance = st.slider("Distance spotting (m)", 0, 2000, 500, help="Distance de propagation par brandons")
            crown_fire_enabled = st.toggle("Feu de cime", value=True, help="Activer la propagation en cime")
            spotting_enabled = st.toggle("Spotting (brandons)", value=True, help="Activer le spotting")
            spotting_prob = st.slider("Probabilité spotting", 0.0, 1.0, 0.15, help="Probabilité de spotting")
            fuel_model = st.selectbox(
                "Modèle de combustible",
                ["Rothermel", "Canadian FBP", "Australian", "Custom"],
                help="Modèle de propagation du feu"
            )

        if st.button("▶️ Exécuter Simulation", type="primary", use_container_width=True):
            if st.session_state.fire_grid is not None:
                with st.spinner("🔬 Calcul physique en cours..."):
                    sim = AdvancedFireModel(
                        base_lat=base_lat if 'base_lat' in locals() else 43.6045,
                        base_lon=base_lon if 'base_lon' in locals() else 7.0542,
                        rows=60, cols=60,
                        spotting_distance=spotting_distance,
                        crown_fire=crown_fire_enabled,
                        spotting=spotting_enabled,
                        spotting_prob=spotting_prob,
                        fuel_model=fuel_model
                    )

                    progress_bar = st.progress(0)
                    for step in range(num_steps):
                        new_grid = sim.step_propagation(
                            st.session_state.fire_grid,
                            st.session_state.elevation,
                            wind_speed if 'wind_speed' in locals() else 45,
                            wind_dir if 'wind_dir' in locals() else 180,
                            moisture if 'moisture' in locals() else 25
                        )
                        st.session_state.fire_grid = new_grid
                        st.session_state.simulation_step += 1

                        st.session_state.fire_history.append({
                            'step': st.session_state.simulation_step,
                            'grid': new_grid.copy(),
                            'timestamp': datetime.now()
                        })

                        progress_bar.progress((step + 1) / num_steps)

                    active_count = np.sum(new_grid == 2)
                    burned_count = np.sum(new_grid == 1)

                    st.success(f"✅ Simulation terminée — {num_steps}h simulées")

                    cols = st.columns(3)
                    cols[0].metric("🔥 Foyers actifs", int(active_count))
                    cols[1].metric("💨 Cellules brûlées", int(burned_count))
                    cols[2].metric("📐 Surface totale", f"{(active_count + burned_count):.0f} ha")

                    st.rerun()
            else:
                st.warning("⚠️ Veuillez d'abord initialiser la grille dans le panneau latéral")

        if st.button("⏹️ Réinitialiser", use_container_width=True):
            st.session_state.fire_grid = None
            st.session_state.fire_history = []
            st.session_state.simulation_step = 0
            st.rerun()

    with sim_col2:
        if st.session_state.fire_history:
            st.markdown("""
            <div style="background: #1E293B; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                <h4 style="margin: 0; color: #F1F5F9; font-size: 14px;">📈 Évolution Temporelle</h4>
            </div>
            """, unsafe_allow_html=True)

            history_data = []
            for h in st.session_state.fire_history:
                history_data.append({
                    'step': h['step'],
                    'active': np.sum(h['grid'] == 2),
                    'burned': np.sum(h['grid'] == 1),
                    'total': np.sum(h['grid'] > 0)
                })

            hist_df = pd.DataFrame(history_data)

            fig = make_subplots(rows=2, cols=1, subplot_titles=("Surface affectée", "Taux de propagation"))

            fig.add_trace(
                go.Scatter(x=hist_df['step'], y=hist_df['active'], name="Actif", 
                          fill='tozeroy', line=dict(color='#EF4444')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=hist_df['step'], y=hist_df['burned'], name="Brûlé", 
                          fill='tonexty', line=dict(color='#7C2D12')),
                row=1, col=1
            )

            if len(hist_df) > 1:
                growth_rate = hist_df['total'].diff().fillna(0)
                fig.add_trace(
                    go.Bar(x=hist_df['step'][1:], y=growth_rate[1:], name="Croissance", 
                          marker_color='#F59E0B'),
                    row=2, col=1
                )

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#F1F5F9',
                height=500,
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("""
            <div style="background: #1E293B; padding: 12px; border-radius: 8px; margin-top: 12px;">
                <h4 style="margin: 0; color: #F1F5F9; font-size: 14px;">⏱️ Timeline Simulation</h4>
            </div>
            """, unsafe_allow_html=True)

            step_to_view = st.slider("Pas de temps", 0, len(st.session_state.fire_history)-1, 
                                    len(st.session_state.fire_history)-1)

            if step_to_view < len(st.session_state.fire_history):
                grid_at_step = st.session_state.fire_history[step_to_view]['grid']

                fig_grid = px.imshow(
                    grid_at_step,
                    color_continuous_scale=[(0, '#1E293B'), (0.5, '#7C2D12'), (1, '#EF4444')],
                    title=f"État de la grille au pas {step_to_view + 1}"
                )
                fig_grid.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#F1F5F9'
                )
                st.plotly_chart(fig_grid, use_container_width=True)
        else:
            st.info("Exécutez une simulation pour visualiser les résultats")

# ═══════════════════════════════════════════════════════════════
# TAB 4: INTELLIGENCE & ANALYTIQUES
# ═══════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("""
    <div style="background: #1E293B; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;">
        <h3 style="margin: 0; color: #F1F5F9; font-size: 16px;">📊 Centre d'Intelligence</h3>
        <p style="margin: 4px 0 0 0; font-size: 11px; color: #64748B;">Analytics avancés · Prédictions IA · Tableaux de bord tactiques</p>
    </div>
    """, unsafe_allow_html=True)

    kpi_cols = st.columns(4)

    with kpi_cols[0]:
        render_metric_card("📈 Efficacité", "87%", "#10B981", "+12% vs hier")
    with kpi_cols[1]:
        render_metric_card("⏱️ Temps réponse", "12 min", "#F59E0B", "-3 min vs moyenne")
    with kpi_cols[2]:
        render_metric_card("✈️ Taux utilisation", "73%", "#3B82F6", "5 avions en vol")
    with kpi_cols[3]:
        render_metric_card("💰 Coût estimé", "€124K", "#8B5CF6", "Dans budget")

    st.markdown("<hr style='border-color: #334155; margin: 16px 0;'>", unsafe_allow_html=True)

    intel_col1, intel_col2 = st.columns([2, 1])

    with intel_col1:
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Évolution incidents", "Répartition ressources", "Taux propagation", "Coûts opérationnels"),
            specs=[[{"type": "scatter"}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )

        days = pd.date_range(end=datetime.now(), periods=7, freq='D')
        incidents_daily = [3, 5, 2, 7, 4, 6, 5]

        fig.add_trace(go.Scatter(x=days, y=incidents_daily, mode='lines+markers', 
                                name='Incidents', line=dict(color='#EF4444')), row=1, col=1)

        fig.add_trace(go.Pie(labels=['Canadair', 'Hélicoptères', 'CCF', 'FPT', 'Drones'],
                            values=[30, 25, 20, 15, 10], 
                            marker_colors=['#EF4444', '#F59E0B', '#3B82F6', '#10B981', '#8B5CF6']),
                     row=1, col=2)

        zones = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon']
        spread_rates = [4.5, 3.2, 2.1, 5.8, 1.9]
        fig.add_trace(go.Bar(x=zones, y=spread_rates, marker_color='#F59E0B', name='km/h'), row=2, col=1)

        costs = [45, 52, 38, 67, 55, 48, 62]
        fig.add_trace(go.Scatter(x=days, y=costs, mode='lines', fill='tozeroy', 
                                line=dict(color='#10B981'), name='K€'), row=2, col=2)

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#F1F5F9',
            height=600,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with intel_col2:
        st.markdown("""
        <div style="background: #1E293B; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
            <h4 style="margin: 0; color: #F1F5F9; font-size: 14px;">🤖 Prédictions IA</h4>
        </div>
        """, unsafe_allow_html=True)

        predictions = [
            {"label": "Probabilité d'escalade", "value": "68%", "trend": "↑", "color": "#EF4444"},
            {"label": "Heure de containment estimée", "value": "18:30", "trend": "→", "color": "#F59E0B"},
            {"label": "Surface finale estimée", "value": "~450 ha", "trend": "↑", "color": "#EF4444"},
            {"label": "Ressources suppl. nécessaires", "value": "3 Canadairs", "trend": "↑", "color": "#F59E0B"},
            {"label": "Impact population", "value": "1,200 pers.", "trend": "→", "color": "#3B82F6"},
            {"label": "Qualité air (PM2.5)", "value": "185 µg/m³", "trend": "↑", "color": "#EF4444"},
        ]

        for pred in predictions:
            st.markdown(f"""
            <div style="background: #0F172A; padding: 10px; border-radius: 6px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 11px; color: #94A3B8;">{pred['label']}</span>
                    <span style="font-size: 11px; color: {pred['color']};">{pred['trend']}</span>
                </div>
                <p style="margin: 4px 0 0 0; font-size: 16px; font-weight: 700; color: {pred['color']};">
                    {pred['value']}
                </p>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# TAB 5: TÉLÉMÉTRIE IoT
# ═══════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("""
    <div style="background: #1E293B; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;">
        <h3 style="margin: 0; color: #F1F5F9; font-size: 16px;">📡 Centre de Télémétrie</h3>
        <p style="margin: 4px 0 0 0; font-size: 11px; color: #64748B;">Monitoring temps réel · Capteurs environnementaux · Tracking véhicules</p>
    </div>
    """, unsafe_allow_html=True)

    iot_col1, iot_col2 = st.columns([2, 1])

    with iot_col1:
        demo_tracks = [
            {"id": "CCF_01", "type": "truck", "lat": 43.6045, "lon": 7.0542, "speed": 45, "altitude": 120, 
             "status": "En intervention", "battery": 78, "last_update": datetime.now() - timedelta(minutes=2)},
            {"id": "CCF_02", "type": "truck", "lat": 43.6100, "lon": 7.0600, "speed": 30, "altitude": 85, 
             "status": "En route", "battery": 92, "last_update": datetime.now() - timedelta(minutes=1)},
            {"id": "DRONE_RECON_1", "type": "drone", "lat": 43.5900, "lon": 7.0600, "speed": 65, "altitude": 350, 
             "status": "Reconnaissance", "battery": 45, "last_update": datetime.now() - timedelta(seconds=30)},
            {"id": "DRONE_THERMAL_2", "type": "drone", "lat": 43.6150, "lon": 7.0450, "speed": 55, "altitude": 280, 
             "status": "Surveillance", "battery": 62, "last_update": datetime.now() - timedelta(minutes=3)},
            {"id": "CANADAIR_01", "type": "aircraft", "lat": 43.6200, "lon": 7.0700, "speed": 280, "altitude": 1500, 
             "status": "Largage", "battery": 100, "last_update": datetime.now() - timedelta(seconds=15)},
        ]

        if not st.session_state.iot_tracks:
            st.session_state.iot_tracks = demo_tracks

        st.dataframe(
            pd.DataFrame(st.session_state.iot_tracks),
            use_container_width=True,
            column_config={
                "id": st.column_config.TextColumn("ID", width="medium"),
                "type": st.column_config.TextColumn("Type", width="small"),
                "lat": st.column_config.NumberColumn("Lat", format="%.6f", width="small"),
                "lon": st.column_config.NumberColumn("Lon", format="%.6f", width="small"),
                "speed": st.column_config.NumberColumn("Vitesse", width="small"),
                "altitude": st.column_config.NumberColumn("Alt.", width="small"),
                "status": st.column_config.TextColumn("Statut", width="medium"),
                "battery": st.column_config.ProgressColumn("Batt. %", min_value=0, max_value=100, width="medium"),
            }
        )

        st.markdown("""
        <div style="background: #1E293B; padding: 12px; border-radius: 8px; margin-top: 16px;">
            <h4 style="margin: 0; color: #F1F5F9; font-size: 14px;">📈 Vitesses & Altitudes</h4>
        </div>
        """, unsafe_allow_html=True)

        fig = go.Figure()
        tracks = st.session_state.iot_tracks
        for track in tracks:
            color = {"truck": "#3B82F6", "drone": "#8B5CF6", "aircraft": "#EF4444"}.get(track['type'], "#F59E0B")
            fig.add_trace(go.Scatter(
                x=[track['speed']], y=[track['altitude']],
                mode='markers',
                name=track['id'],
                marker=dict(size=20, color=color, line=dict(width=2, color='white')),
                text=[f"{track['id']}<br>Status: {track['status']}"],
                hovertemplate='%{text}'
            ))

        fig.update_layout(
            xaxis_title="Vitesse (km/h)",
            yaxis_title="Altitude (m)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#F1F5F9',
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

    with iot_col2:
        st.markdown("""
        <div style="background: #1E293B; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
            <h4 style="margin: 0; color: #F1F5F9; font-size: 14px;">🌡️ Capteurs Environnementaux</h4>
        </div>
        """, unsafe_allow_html=True)

        sensors = [
            {"name": "Station Météo A1", "temp": 32.5, "humidity": 22, "wind": 48, "pm25": 145, "status": "OK"},
            {"name": "Station Météo B2", "temp": 35.2, "humidity": 18, "wind": 62, "pm25": 210, "status": "ALERTE"},
            {"name": "Capteur Forêt C3", "temp": 38.1, "humidity": 12, "wind": 55, "pm25": 340, "status": "CRITIQUE"},
            {"name": "Capteur Urbain D4", "temp": 29.8, "humidity": 35, "wind": 25, "pm25": 85, "status": "OK"},
        ]

        for sensor in sensors:
            status_color = {"OK": "#10B981", "ALERTE": "#F59E0B", "CRITIQUE": "#EF4444"}[sensor['status']]
            st.markdown(f"""
            <div style="background: #0F172A; padding: 12px; border-radius: 8px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 12px; font-weight: 600; color: #F1F5F9;">{sensor['name']}</span>
                    <span style="background: {status_color}; color: white; font-size: 9px; padding: 2px 8px; border-radius: 4px;">
                        {sensor['status']}
                    </span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11px;">
                    <div>🌡️ {sensor['temp']}°C</div>
                    <div>💧 {sensor['humidity']}%</div>
                    <div>💨 {sensor['wind']} km/h</div>
                    <div>😷 PM2.5: {sensor['pm25']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: #1E293B; padding: 12px; border-radius: 8px; margin-top: 16px;">
            <h4 style="margin: 0 0 8px 0; color: #F1F5F9; font-size: 14px;">📡 État Connexions</h4>
        </div>
        """, unsafe_allow_html=True)

        connections = [
            {"name": "Serveur IoT", "status": "🟢 Connecté", "latency": "12ms"},
            {"name": "Base PostGIS", "status": "🟢 Connecté", "latency": "8ms"},
            {"name": "Redis Cache", "status": "🟢 Connecté", "latency": "3ms"},
            {"name": "API Météo", "status": "🟡 Dégradé", "latency": "245ms"},
            {"name": "Satellite", "status": "🟢 Connecté", "latency": "180ms"},
        ]

        for conn in connections:
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; 
                        padding: 6px 0; border-bottom: 1px solid #334155; font-size: 12px;">
                <span style="color: #94A3B8;">{conn['name']}</span>
                <span style="color: #F1F5F9;">{conn['status']} ({conn['latency']})</span>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# TAB 6: ALERTES & NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("""
    <div style="background: #1E293B; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;">
        <h3 style="margin: 0; color: #F1F5F9; font-size: 16px;">⚠️ Centre d'Alertes</h3>
        <p style="margin: 4px 0 0 0; font-size: 11px; color: #64748B;">Gestion des alertes · Escalade automatique · Journal des événements</p>
    </div>
    """, unsafe_allow_html=True)

    alert_col1, alert_col2 = st.columns([2, 1])

    with alert_col1:
        # Générer des alertes de démonstration
        demo_alerts = [
            {
                'id': 'ALT-001',
                'level': 'CRITIQUE',
                'title': 'Propagation rapide détectée',
                'message': 'Taux de propagation > 5 km/h sur Zone Delta. Évacuation recommandée.',
                'timestamp': datetime.now() - timedelta(minutes=5),
                'source': 'Simulation',
                'acknowledged': False,
                'assigned_to': None
            },
            {
                'id': 'ALT-002',
                'level': 'ALERTE',
                'title': 'Ressources insuffisantes',
                'message': 'Demande de renfort : 3 Canadairs supplémentaires nécessaires.',
                'timestamp': datetime.now() - timedelta(minutes=12),
                'source': 'Optimisation',
                'acknowledged': False,
                'assigned_to': None
            },
            {
                'id': 'ALT-003',
                'level': 'INFO',
                'title': 'Nouveau véhicule en route',
                'message': 'CCF_03 déployé vers Zone Alpha. ETA: 18 minutes.',
                'timestamp': datetime.now() - timedelta(minutes=20),
                'source': 'IoT',
                'acknowledged': True,
                'assigned_to': 'Opérateur 1'
            },
            {
                'id': 'ALT-004',
                'level': 'ALERTE',
                'title': 'Conditions météo dégradées',
                'message': 'Vent prévu à 80 km/h dans 2h. Renforcement des moyens conseillé.',
                'timestamp': datetime.now() - timedelta(minutes=35),
                'source': 'Météo',
                'acknowledged': False,
                'assigned_to': None
            },
        ]

        if not st.session_state.alerts:
            st.session_state.alerts = demo_alerts

        # Filtres
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            alert_filter = st.selectbox("Niveau", ["Tous", "CRITIQUE", "ALERTE", "INFO"])
        with filter_col2:
            source_filter = st.selectbox("Source", ["Toutes", "Simulation", "Optimisation", "IoT", "Météo"])
        with filter_col3:
            status_filter = st.selectbox("Statut", ["Tous", "Non acquitté", "Acquitté"])

        # Affichage des alertes
        for alert in st.session_state.alerts:
            if alert_filter != "Tous" and alert['level'] != alert_filter:
                continue
            if source_filter != "Toutes" and alert['source'] != source_filter:
                continue
            if status_filter == "Non acquitté" and alert['acknowledged']:
                continue
            if status_filter == "Acquitté" and not alert['acknowledged']:
                continue

            level_colors = {"CRITIQUE": "#EF4444", "ALERTE": "#F59E0B", "INFO": "#3B82F6"}
            color = level_colors.get(alert['level'], "#64748B")

            st.markdown(f"""
            <div style="background: #0F172A; padding: 16px; border-radius: 8px; 
                        border-left: 4px solid {color}; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                            <span style="background: {color}; color: white; font-size: 10px; font-weight: 700; 
                                        padding: 2px 8px; border-radius: 4px;">{alert['level']}</span>
                            <span style="font-size: 12px; color: #64748B;">{alert['id']} · {alert['source']}</span>
                        </div>
                        <h4 style="margin: 4px 0; color: #F1F5F9; font-size: 14px;">{alert['title']}</h4>
                        <p style="margin: 0; color: #94A3B8; font-size: 12px;">{alert['message']}</p>
                    </div>
                    <span style="font-size: 11px; color: #64748B; white-space: nowrap;">
                        {(datetime.now() - alert['timestamp']).seconds // 60}m
                    </span>
                </div>
                <div style="margin-top: 8px; display: flex; gap: 8px;">
                    {f'<span style="font-size: 11px; color: #10B981;">✓ Acquitté par {alert["assigned_to"]}</span>' if alert['acknowledged'] else 
                     '<button style="background: #1E293B; color: #F1F5F9; border: 1px solid #334155; padding: 4px 12px; border-radius: 4px; font-size: 11px; cursor: pointer;">Acquitter</button>'}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with alert_col2:
        st.markdown("""
        <div style="background: #1E293B; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
            <h4 style="margin: 0; color: #F1F5F9; font-size: 14px;">📊 Statistiques Alertes</h4>
        </div>
        """, unsafe_allow_html=True)

        total_alerts = len(st.session_state.alerts)
        critical = len([a for a in st.session_state.alerts if a['level'] == 'CRITIQUE'])
        warning = len([a for a in st.session_state.alerts if a['level'] == 'ALERTE'])
        unack = len([a for a in st.session_state.alerts if not a['acknowledged']])

        render_metric_card("Total", str(total_alerts), "#F1F5F9")
        render_metric_card("Critiques", str(critical), "#EF4444")
        render_metric_card("Alertes", str(warning), "#F59E0B")
        render_metric_card("Non acquittées", str(unack), "#F59E0B")

        st.markdown("""
        <div style="background: #1E293B; padding: 12px; border-radius: 8px; margin-top: 16px;">
            <h4 style="margin: 0 0 8px 0; color: #F1F5F9; font-size: 14px;">🔔 Configuration Alertes</h4>
        </div>
        """, unsafe_allow_html=True)

        st.toggle("Alertes sonores", value=True)
        st.toggle("Notification push", value=True)
        st.toggle("Escalade auto", value=True)
        st.toggle("SMS commandant", value=False)
        st.toggle("Email équipe", value=True)

        st.number_input("Délai escalade (min)", 5, 60, 15)

# ═══════════════════════════════════════════════════════════════
# TAB 7: RAPPORTS & DOCUMENTATION
# ═══════════════════════════════════════════════════════════════
with tabs[6]:
    st.markdown("""
    <div style="background: #1E293B; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;">
        <h3 style="margin: 0; color: #F1F5F9; font-size: 16px;">📋 Centre de Rapports</h3>
        <p style="margin: 4px 0 0 0; font-size: 11px; color: #64748B;">Génération automatique · Export multi-format · Archivage</p>
    </div>
    """, unsafe_allow_html=True)

    rep_col1, rep_col2 = st.columns([1, 2])

    with rep_col1:
        st.markdown("""
        <div style="background: #1E293B; padding: 12px; border-radius: 8px;">
            <h4 style="margin: 0 0 12px 0; color: #F1F5F9; font-size: 14px;">📄 Générer un Rapport</h4>
        </div>
        """, unsafe_allow_html=True)

        report_type = st.selectbox(
            "Type de rapport",
            ["Rapport complet", "Rapport tactique", "Rapport simulation", "Rapport ressources", 
             "Rapport météo", "Synthèse opérationnelle", "Rapport post-incident"]
        )

        report_format = st.selectbox("Format", ["PDF", "Excel", "Word", "HTML", "GeoJSON", "KML"])

        include_sections = st.multiselect(
            "Sections à inclure",
            ["Résumé exécutif", "Cartographie", "Données simulation", "Allocation ressources", 
             "Chronologie", "Métriques KPI", "Recommandations", "Annexes techniques"],
            default=["Résumé exécutif", "Cartographie", "Données simulation", "Métriques KPI"]
        )

        st.markdown("<p style='color: #94A3B8; font-size: 11px; font-weight: 600; margin-top: 16px;'>🎯 Période</p>", unsafe_allow_html=True)

        date_range = st.date_input("Période", value=(datetime.now() - timedelta(days=1), datetime.now()))

        if st.button("📥 Générer le rapport", type="primary", use_container_width=True):
            with st.spinner("📝 Génération du rapport en cours..."):
                time.sleep(2)

                report_gen = ReportGenerator()
                report_data = report_gen.generate_full_report(
                    incidents=st.session_state.active_incidents,
                    resources=st.session_state.resource_status,
                    simulation_data={
                        'grid': st.session_state.fire_grid,
                        'history': st.session_state.fire_history,
                        'elevation': st.session_state.elevation
                    },
                    format=report_format.lower(),
                    sections=include_sections,
                    date_range=date_range
                )

                st.success("✅ Rapport généré avec succès!")

                ext_map = {"PDF": "pdf", "Excel": "xlsx", "Word": "docx", "HTML": "html", "GeoJSON": "geojson", "KML": "kml"}
                ext = ext_map.get(report_format, "pdf")

                st.download_button(
                    label=f"⬇️ Télécharger le rapport ({report_format})",
                    data=report_data,
                    file_name=f"CODIS_Rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
                    mime="application/octet-stream",
                    use_container_width=True
                )

    with rep_col2:
        st.markdown("""
        <div style="background: #1E293B; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
            <h4 style="margin: 0; color: #F1F5F9; font-size: 14px;">📚 Rapports Générés</h4>
        </div>
        """, unsafe_allow_html=True)

        # Historique des rapports simulé
        reports_history = [
            {"name": "Rapport_OP_Prométhée_20260724_1430.pdf", "type": "Rapport complet", "date": "24/07/2026 14:30", "size": "2.4 MB", "author": "Cmdt. Dupont"},
            {"name": "Simulation_Propagation_6h_20260724_1200.xlsx", "type": "Rapport simulation", "date": "24/07/2026 12:00", "size": "1.8 MB", "author": "Analyste Martin"},
            {"name": "Allocation_Ressources_20260724_1030.pdf", "type": "Rapport ressources", "date": "24/07/2026 10:30", "size": "890 KB", "author": "Cmdt. Dupont"},
            {"name": "Météo_Analyse_20260724_0800.html", "type": "Rapport météo", "date": "24/07/2026 08:00", "size": "450 KB", "author": "Météo Service"},
        ]

        for rep in reports_history:
            st.markdown(f"""
            <div style="background: #0F172A; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <p style="margin: 0; font-size: 12px; font-weight: 600; color: #F1F5F9;">{rep['name']}</p>
                        <p style="margin: 4px 0 0 0; font-size: 10px; color: #64748B;">
                            {rep['type']} · {rep['date']} · {rep['size']} · {rep['author']}
                        </p>
                    </div>
                    <button style="background: #1E293B; color: #3B82F6; border: 1px solid #334155; 
                                   padding: 6px 12px; border-radius: 4px; font-size: 11px; cursor: pointer;">
                        ⬇️
                    </button>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: #1E293B; padding: 12px; border-radius: 8px; margin-top: 16px;">
            <h4 style="margin: 0 0 8px 0; color: #F1F5F9; font-size: 14px;">📈 Métriques de Production</h4>
        </div>
        """, unsafe_allow_html=True)

        metrics_cols = st.columns(3)
        metrics_cols[0].metric("Rapports/jour", "12", "+3")
        metrics_cols[1].metric("Temps moyen génération", "45s", "-12s")
        metrics_cols[2].metric("Taux succès", "99.2%", "+0.5%")

# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════
st.markdown("<hr style='border-color: #334155; margin: 24px 0 12px 0;'>", unsafe_allow_html=True)

st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0;">
    <div style="font-size: 10px; color: #64748B;">
        CODIS NEXT-GEN PRO v3.0 · Système de Commandement et Contrôle · © 2026
    </div>
    <div style="font-size: 10px; color: #64748B;">
        🟢 Système opérationnel · Latence: 12ms · Dernière sync: {sync_time}
    </div>
</div>
""".format(sync_time=datetime.now().strftime("%H:%M:%S")), unsafe_allow_html=True)
