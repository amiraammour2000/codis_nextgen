# 🛡️ CODIS NEXT-GEN PRO

**Système de Commandement et Contrôle (C4ISR) pour la gestion des incendies**

[![Version](https://img.shields.io/badge/version-3.0-red)](https://)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://)
[![Streamlit](https://img.shields.io/badge/streamlit-1.40+-green)](https://)
[![License](https://img.shields.io/badge/license-MIT-yellow)](https://)

## 🚀 Caractéristiques

- **🗺️ COP Tactique** — Carte interactive temps réel avec PostGIS, heatmaps, trajectoires IoT
- **🧠 Optimisation MILP** — Solveur OR-Tools pour dispatch aérien et allocation ressources
- **🔬 Jumeau Numérique** — Simulation physique avancée (Rothermel, Canadian FBP, spotting, feu de cime)
- **📡 Télémétrie IoT** — WebSocket temps réel, tracking véhicules/drones/capteurs
- **📊 Intelligence** — Dashboards analytiques, prédictions IA, KPIs temps réel
- **⚠️ Alertes** — Gestion multi-niveaux, escalade automatique, notifications
- **📋 Rapports** — Génération auto PDF/Excel/HTML/GeoJSON

## 📦 Installation

### Prérequis
- Python 3.11+
- Docker & Docker Compose (optionnel)
- PostgreSQL 15+ avec PostGIS
- Redis 7+

### Méthode 1 : Docker Compose (Recommandé)

```bash
# Cloner le projet
cd codis_nextgen_pro

# Copier la configuration
cp .env.example .env

# Lancer les services
docker-compose up -d

# Accéder à l'application
open http://localhost:8501
```

### Méthode 2 : Installation manuelle

```bash
# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer la base de données
# (voir section Configuration)

# Lancer l'application
streamlit run app.py
```

## ⚙️ Configuration

### Base de données PostGIS

```sql
CREATE DATABASE codis_geo_db;
\c codis_geo_db
CREATE EXTENSION postgis;
```

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL de connexion PostgreSQL | `dbname=codis...` |
| `REDIS_HOST` | Hôte Redis | `localhost` |
| `REDIS_PORT` | Port Redis | `6379` |
| `ENV` | Environnement | `development` |

## 🏗️ Architecture

```
codis_nextgen_pro/
├── app.py                    # Application principale Streamlit
├── celery_worker.py          # Worker Celery pour tâches asynchrones
├── iot_websocket_server.py   # Serveur WebSocket IoT
├── requirements.txt          # Dépendances Python
├── docker-compose.yml        # Orchestration Docker
├── Dockerfile                # Image Docker
├── .streamlit/
│   └── config.toml          # Configuration Streamlit
├── src/
│   ├── fire_physics.py      # Simulation physique du feu
│   ├── db_gis.py            # Gestionnaire PostGIS
│   ├── optimization.py      # Optimisation MILP
│   ├── models/              # Modèles de données
│   ├── services/            # Services métier
│   └── utils/               # Utilitaires
├── config/
│   └── nginx.conf           # Configuration Nginx
└── docs/                    # Documentation
```

## 🎯 Utilisation

### 1. Initialiser le théâtre d'opérations
1. Ouvrir le panneau latéral **⚙️ Panneau de Commandement**
2. Configurer les paramètres météo et zone
3. Cliquer sur **🚀 Initialiser le Théâtre d'Opérations**

### 2. Lancer une simulation
1. Aller dans l'onglet **🔬 Simulation**
2. Configurer les paramètres physiques
3. Cliquer sur **▶️ Exécuter Simulation**

### 3. Optimiser les ressources
1. Aller dans l'onglet **🧠 Optimisation**
2. Sélectionner l'algorithme et les contraintes
3. Cliquer sur **🚀 Lancer l'Optimisation**

## 📊 Modules

| Module | Description | Technologie |
|--------|-------------|-------------|
| COP | Carte tactique temps réel | Folium, PostGIS |
| Optimisation | Allocation ressources | OR-Tools, MILP |
| Simulation | Jumeau numérique | NumPy, modèles physiques |
| IoT | Télémétrie temps réel | WebSockets, Redis |
| Intelligence | Analytics & prédictions | Plotly, Pandas |
| Alertes | Gestion notifications | Celery, WebSockets |
| Rapports | Génération documents | ReportLab, OpenPyXL |

## 🔧 Développement

```bash
# Lancer en mode développement
streamlit run app.py --server.runOnSave=true

# Lancer le worker Celery
celery -A celery_worker.celery_app worker --loglevel=info

# Lancer le serveur IoT
python iot_websocket_server.py
```

## 📝 License

MIT License — Voir [LICENSE](LICENSE) pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez consulter [CONTRIBUTING.md](CONTRIBUTING.md).

---

**CODIS NEXT-GEN PRO v3.0** — Développé avec ❤️ pour la sécurité civile
