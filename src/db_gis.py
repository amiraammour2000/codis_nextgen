import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional, Any
import json
from datetime import datetime

class GISDatabaseManager:
    """Gestionnaire de base de données géospatiale PostGIS."""

    def __init__(self):
        self.conn_str = os.getenv(
            "DATABASE_URL", 
            "dbname=codis_geo_db user=codis_admin password=secure_password host=localhost port=5432"
        )
        self._mock_data = self._init_mock_data()

    def _init_mock_data(self):
        """Données de démonstration si pas de DB."""
        return [
            {
                'id': 1,
                'name': 'Zone Alpha - Forêt de la Massane',
                'lat': 43.61,
                'lon': 7.06,
                'priority': 'Critique',
                'spread_rate': 4.5,
                'area_ha': 150,
                'population': 2500,
                'terrain_type': 'Forêt méditerranéenne',
                'last_update': datetime.now().isoformat()
            },
            {
                'id': 2,
                'name': 'Zone Beta - Colline Saint-Roch',
                'lat': 43.59,
                'lon': 7.03,
                'priority': 'Élevée',
                'spread_rate': 3.2,
                'area_ha': 80,
                'population': 800,
                'terrain_type': 'Maquis',
                'last_update': datetime.now().isoformat()
            },
            {
                'id': 3,
                'name': 'Zone Gamma - Vallée du Var',
                'lat': 43.62,
                'lon': 7.08,
                'priority': 'Moyenne',
                'spread_rate': 2.1,
                'area_ha': 45,
                'population': 200,
                'terrain_type': 'Prairie',
                'last_update': datetime.now().isoformat()
            },
            {
                'id': 4,
                'name': 'Zone Delta - Zone Urbaine Est',
                'lat': 43.58,
                'lon': 7.05,
                'priority': 'Critique',
                'spread_rate': 5.8,
                'area_ha': 220,
                'population': 4200,
                'terrain_type': 'Zone urbaine',
                'last_update': datetime.now().isoformat()
            },
            {
                'id': 5,
                'name': 'Zone Epsilon - Zone Industrielle Nord',
                'lat': 43.605,
                'lon': 7.065,
                'priority': 'Élevée',
                'spread_rate': 3.8,
                'area_ha': 120,
                'population': 150,
                'terrain_type': 'Zone industrielle',
                'last_update': datetime.now().isoformat()
            }
        ]

    def get_connection(self):
        """Obtient une connexion à la base de données."""
        try:
            conn = psycopg2.connect(self.conn_str)
            self._init_db(conn)
            return conn
        except Exception as e:
            print(f"⚠️ Connexion PostGIS indisponible: {e}")
            return None

    def _init_db(self, conn):
        """Initialise les tables spatiales."""
        cursor = conn.cursor()
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fire_perimeters (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    incident_id VARCHAR(50),
                    geom GEOMETRY(POLYGON, 4326),
                    area_ha DOUBLE PRECISION,
                    status VARCHAR(20)
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_sectors (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200),
                    lat DOUBLE PRECISION,
                    lon DOUBLE PRECISION,
                    priority VARCHAR(20),
                    spread_rate DOUBLE PRECISION,
                    area_ha DOUBLE PRECISION,
                    population INTEGER,
                    terrain_type VARCHAR(100),
                    geom GEOMETRY(POINT, 4326),
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS iot_tracks (
                    id SERIAL PRIMARY KEY,
                    device_id VARCHAR(50),
                    device_type VARCHAR(50),
                    lat DOUBLE PRECISION,
                    lon DOUBLE PRECISION,
                    altitude DOUBLE PRECISION,
                    speed DOUBLE PRECISION,
                    heading DOUBLE PRECISION,
                    status VARCHAR(50),
                    battery INTEGER,
                    geom GEOMETRY(POINT, 4326),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id SERIAL PRIMARY KEY,
                    incident_id VARCHAR(50) UNIQUE,
                    name VARCHAR(200),
                    lat DOUBLE PRECISION,
                    lon DOUBLE PRECISION,
                    status VARCHAR(20),
                    priority VARCHAR(20),
                    type VARCHAR(100),
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    affected_area_ha DOUBLE PRECISION,
                    resources_deployed INTEGER,
                    geom GEOMETRY(POINT, 4326)
                );
            """)

            conn.commit()
        except Exception as e:
            print(f"Erreur init DB: {e}")
        finally:
            cursor.close()

    def save_fire_perimeter(self, coordinates_list, incident_id="default"):
        """Sauvegarde un périmètre de feu."""
        conn = self.get_connection()
        if not conn or not coordinates_list:
            return False

        try:
            if len(coordinates_list) < 3:
                return False

            coords_str = ", ".join([f"{lon} {lat}" for lat, lon in coordinates_list])
            poly_str = f"POLYGON(({coords_str}, {coordinates_list[0][1]} {coordinates_list[0][0]}))"

            cursor = conn.cursor()
            query = sql.SQL("""
                INSERT INTO fire_perimeters (incident_id, geom, area_ha, status)
                VALUES (%s, ST_GeomFromText(%s, 4326), %s, %s)
            """)

            # Calcul approximatif de l'aire
            area_ha = len(coordinates_list) * 1.0

            cursor.execute(query, (incident_id, poly_str, area_ha, 'active'))
            conn.commit()
            return True
        except Exception as e:
            print(f"Erreur PostGIS: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def fetch_active_sectors(self):
        """Récupère les secteurs actifs."""
        conn = self.get_connection()
        if not conn:
            return self._mock_data

        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT id, name, lat, lon, priority, spread_rate, area_ha, population, terrain_type, last_update
                FROM active_sectors
                WHERE last_update > NOW() - INTERVAL '24 hours'
                ORDER BY 
                    CASE priority 
                        WHEN 'Critique' THEN 1 
                        WHEN 'Élevée' THEN 2 
                        WHEN 'Moyenne' THEN 3 
                        ELSE 4 
                    END
            """)
            results = cursor.fetchall()
            return [dict(r) for r in results] if results else self._mock_data
        except Exception as e:
            print(f"Erreur fetch: {e}")
            return self._mock_data
        finally:
            if conn:
                conn.close()

    def save_sector(self, sector_data):
        """Sauvegarde un secteur."""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            query = sql.SQL("""
                INSERT INTO active_sectors (name, lat, lon, priority, spread_rate, area_ha, population, terrain_type, geom)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                ON CONFLICT (id) DO UPDATE SET
                    priority = EXCLUDED.priority,
                    spread_rate = EXCLUDED.spread_rate,
                    last_update = NOW()
            """)
            cursor.execute(query, (
                sector_data['name'], sector_data['lat'], sector_data['lon'],
                sector_data['priority'], sector_data.get('spread_rate', 0),
                sector_data.get('area_ha', 0), sector_data.get('population', 0),
                sector_data.get('terrain_type', ''),
                sector_data['lon'], sector_data['lat']
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Erreur save sector: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def save_iot_track(self, track_data):
        """Sauvegarde une trace IoT."""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            query = sql.SQL("""
                INSERT INTO iot_tracks (device_id, device_type, lat, lon, altitude, speed, heading, status, battery, geom)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            """)
            cursor.execute(query, (
                track_data['id'], track_data.get('type', 'unknown'),
                track_data['lat'], track_data['lon'],
                track_data.get('altitude', 0), track_data.get('speed', 0),
                track_data.get('heading', 0), track_data.get('status', 'active'),
                track_data.get('battery', 100),
                track_data['lon'], track_data['lat']
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Erreur save IoT: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_iot_history(self, device_id, hours=24):
        """Récupère l'historique d'un appareil."""
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT lat, lon, altitude, speed, heading, status, battery, timestamp
                FROM iot_tracks
                WHERE device_id = %s AND timestamp > NOW() - INTERVAL '%s hours'
                ORDER BY timestamp DESC
            """, (device_id, hours))
            return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"Erreur get history: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_fire_perimeters_history(self, incident_id=None, hours=24):
        """Récupère l'historique des périmètres."""
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            if incident_id:
                cursor.execute("""
                    SELECT id, timestamp, incident_id, area_ha, status,
                           ST_AsGeoJSON(geom) as geojson
                    FROM fire_perimeters
                    WHERE incident_id = %s AND timestamp > NOW() - INTERVAL '%s hours'
                    ORDER BY timestamp DESC
                """, (incident_id, hours))
            else:
                cursor.execute("""
                    SELECT id, timestamp, incident_id, area_ha, status,
                           ST_AsGeoJSON(geom) as geojson
                    FROM fire_perimeters
                    WHERE timestamp > NOW() - INTERVAL '%s hours'
                    ORDER BY timestamp DESC
                """, (hours,))
            return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"Erreur get perimeters: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def save_incident(self, incident_data):
        """Sauvegarde un incident."""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            query = sql.SQL("""
                INSERT INTO incidents (incident_id, name, lat, lon, status, priority, type, 
                                     start_time, affected_area_ha, resources_deployed, geom)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                ON CONFLICT (incident_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    affected_area_ha = EXCLUDED.affected_area_ha,
                    resources_deployed = EXCLUDED.resources_deployed
            """)
            cursor.execute(query, (
                incident_data['id'], incident_data['name'],
                incident_data['lat'], incident_data['lon'],
                incident_data.get('status', 'active'),
                incident_data.get('priority', 'Moyenne'),
                incident_data.get('type', 'Feu'),
                incident_data.get('start_time', datetime.now()),
                incident_data.get('affected_area_ha', 0),
                incident_data.get('resources_deployed', 0),
                incident_data['lon'], incident_data['lat']
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Erreur save incident: {e}")
            return False
        finally:
            if conn:
                conn.close()
