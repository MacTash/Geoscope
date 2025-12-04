# 🌐 Geoscope CLI

**Geoscope** is a powerful Multi-INT (Multi-Intelligence) fusion tool designed for open-source intelligence gathering, analysis, and visualization. It aggregates data from OSINT, SOCMINT, GEOINT, ADSINT, MARITINT, and CYBINT sources, analyzes it using local LLMs (Ollama), and presents actionable intelligence via interactive maps and military-style reports.

> *"GREETINGS, PROFESSOR FALKEN. SHALL WE PLAY A GAME?"*
> — Inspired by WOPR from WarGames (1983)

<p align="center">
  <img src="https://img.shields.io/github/stars/MacTash/Geoscope?style=flat-square" alt="Stars">
  <img src="https://img.shields.io/github/license/MacTash/Geoscope?style=flat-square" alt="License">
  <img src="https://img.shields.io/github/issues/MacTash/Geoscope?style=flat-square" alt="Issues">
  <img src="https://img.shields.io/github/last-commit/MacTash/Geoscope?style=flat-square" alt="Last Commit">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python Version">
  <img src="https://img.shields.io/badge/Threat%20Intelligence-MultiINT-red?style=flat-square">
  <img src="https://img.shields.io/badge/Status-Alpha-orange?style=flat-square">
  <img src="https://img.shields.io/badge/LLM-SITREP%20Mode-success?style=flat-square">
</p>


## 🚀 Features

- **Multi-INT Collection**:
  - **OSINT**: News aggregation via DuckDuckGo.
  - **SOCMINT**: Social media scraping (Twitter/X, Reddit, Telegram).
  - **GEOINT**: Satellite imagery metadata (Sentinel-2, Landsat).
  - **ADSINT**: Real-time military aircraft tracking via ADS-B (OpenSky Network).
  - **MARITINT**: Naval vessel and ship tracking with regional intelligence.
  - **CYBINT**: Cyber threat intelligence from CISA KEV and 7+ security feeds.
- **AI Analysis**: Uses local LLMs (Llama 3, Mistral) via Ollama for threat scoring and summarization.
- **Visualization**: Interactive Folium maps and threat heatmaps.
- **Reporting**: Generates professional military-style intelligence assessments (SITREPs).
- **WarGames DEFCON Theme**: Retro terminal aesthetic inspired by WOPR from WarGames (1983).

## 🛠️ Installation

1. **Prerequisites**:
   - Python 3.10+
   - **Ollama** (Required for local AI analysis):
     - Download from [ollama.com](https://ollama.com/)
     - Install and start the service: `ollama serve`
     - **Pull the Model**: Geoscope is optimized for Llama 3.2 (3B), which is lightweight and fast.
       ```bash
       ollama pull llama3.2:3b
       ```
     - *Note: You can change the model in `.env` if you prefer another (e.g., `mistral`, `llama3`).*

2. **Install Geoscope**:
   ```bash
   git clone https://github.com/MacTash/geoscope.git
   cd geoscope
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Initialize Database**:
   ```bash
   geoscope init
   ```

## 🎯 How It Works

Geoscope operates in **5 phases**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        GEOSCOPE ENGINE                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌─────┐ │
│  │ OSINT  │ │SOCMINT │ │ GEOINT │ │ ADSINT │ │MARITINT│ │CYBER│ │
│  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └──┬──┘ │
│      └──────────┴─────┬────┴──────────┴──────────┴─────────┘    │
│                       ▼                                         │
│               ┌───────────────┐                                 │
│               │   SQLite DB   │ ◄─── All intel stored locally   │
│               └───────┬───────┘                                 │
│                       ▼                                         │
│               ┌───────────────┐                                 │
│               │  Ollama LLM   │ ◄─── Local AI (no cloud APIs)   │
│               │ (Llama 3.2)   │                                 │
│               └───────┬───────┘                                 │
│                       ▼                                         │
│           ┌───────────────────────┐                             │
│           │  Reports / Maps / UI  │                             │
│           └───────────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 1: 📊 Topic Assessment
LLM analyzes the target and suggests optimal keywords for collection.

### Phase 2: 📥 Collection Sweep
All relevant INT modules fetch fresh data from their sources:
| Module | Source | Method |
|--------|--------|--------|
| OSINT | DuckDuckGo News | Web scraping |
| SOCMINT | X/Reddit/Telegram | `site:` search operators |
| GEOINT | Sentinel Hub | STAC API |
| ADSINT | OpenSky Network | REST API |
| MARITINT | Regional patterns | Intel database |
| CYBINT | CISA + RSS feeds | API + RSS parsing |

### Phase 3: 🗃️ Data Aggregation
Intel is stored in SQLite with: `timestamp`, `category`, `summary`, `country`, `coordinates`, `threat_level`, `threat_score`, `confidence`.

### Phase 4: 🤖 LLM Synthesis
Generates military-style assessment with:
- Executive Summary
- Threat Matrix
- Key Intelligence by domain
- IOCs & TTPs
- Confidence assessment

### Phase 5: 🗺️ Display & Visualization
- **DEFCON Status**: Real-time threat level (1-5) based on intel
- **Interactive Maps**: Folium-based with clustered markers
- **Heatmaps**: Visualize threat density globally
- **WarGames Theme**: Retro green-on-black terminal aesthetic

### Report Flags
| Flag | Effect |
|------|--------|
| `--sweep` / `--no-sweep` | Enable/disable fresh data collection |
| `--html` | Export report to HTML file |
| `--hours 24,48,72` | Lookback window for existing data |
| `--no-map` | Skip map generation |

## 📖 Usage Guide

### 1. 📊 Status & Overview
Check the system status and recent intelligence items.
```bash
geoscope status
```

### 2. 🗺️ Interactive Maps
Generate visual intelligence products.
```bash
# Generate a map for a specific country
geoscope map generate --country "Ukraine" --hours 72

# REFER TO GEOINT section for more practical usages with nearly zero map generation errors.

# Generate a global threat heatmap
geoscope map heatmap
```

### 3. 🎖️ Intelligence Reports
Generate comprehensive AI-synthesized reports.
```bash
# Quick situation brief
geoscope report brief --country "Taiwan"

# Full military-style assessment (runs a fresh sweep)
geoscope report full "Iran" --sweep --html

# Report on a specific threat topic
geoscope report full "Ransomware" --sweep

# Variations
geoscope report full "country name" --nosweep --hours 24 or 48 or 72
```

### 4. 🕵️ Intelligence Collection (Modules)

#### **OSINT (Open Source Intelligence)**
Track news and global events.
```bash
# Fetch news articles
geoscope osint fetch --keyword "South China Sea" --limit 20

# Search stored OSINT
geoscope osint search "naval exercises"
```

#### **SOCMINT (Social Media Intelligence)**
Monitor social chatter.
```bash
# Scrape recent posts
geoscope socmint scrape --keyword "air defense" --limit 50

# Target specific users
geoscope socmint scrape --keyword "frontline" --user "TheStudyofWar"

# View trending topics
geoscope socmint trending
```

#### **CYBINT (Cyber Intelligence)**
Track vulnerabilities and cyber threats.
```bash
# Scan all configured threat feeds
geoscope cybint scan --all

# List active CISA exploits (KEV)
geoscope cybint cves

# Search for specific malware
geoscope cybint search "LockBit"
```

#### **GEOINT (Geospatial Intelligence)**
Find satellite imagery metadata.
```bash
# Find recent clear imagery
geoscope geoint sat --target "Gaza" --days 7 --clouds 20

# Get coordinates for a location
geoscope geoint locate "Pyongyang"
```

#### **ADSINT (Aircraft Intelligence)**
Track military and interesting aircraft in real-time via ADS-B.
```bash
# Scan a region for military aircraft
geoscope adsint scan ukraine
geoscope adsint scan taiwan
geoscope adsint scan baltic

# Track a specific callsign
geoscope adsint track FORTE   # RQ-4 Global Hawk
geoscope adsint track REACH   # USAF Airlift

# List recent tracks
geoscope adsint list
```

**Available Regions:** `ukraine`, `taiwan`, `baltic`, `korea`, `gulf`, `mediterranean`

#### **MARITINT (Maritime Intelligence)**
Track naval vessels and monitor maritime chokepoints.
```bash
# Scan a maritime region
geoscope maritint scan black_sea
geoscope maritint scan taiwan_strait
geoscope maritint scan persian_gulf

# Search for a specific vessel
geoscope maritint search "Gerald Ford"

# List recent maritime intel
geoscope maritint list
```

**Available Regions:** `black_sea`, `baltic`, `south_china_sea`, `persian_gulf`, `taiwan_strait`, `mediterranean`, `arctic`

### 5. 📤 Data Management
Export your intelligence database.
```bash
# Export to JSON
geoscope export --format json --output intel_dump.json

# Export to CSV
geoscope export --format csv
```

### 6. 🧹 Maintenance
Clean up cache and old reports.
```bash
# Remove __pycache__ directories
geoscope clean

# Also remove old HTML reports/maps
geoscope clean --reports

# Clean everything
geoscope clean --all

# Reset database (wipe all intel)
geoscope reset --force
```

## ⚙️ Configuration

Create a `.env` file in the root directory to customize settings:

```env
OLLAMA_HOST=http://localhost:11434
MODEL_NAME=llama3.2:3b
LOG_LEVEL=INFO
DB_NAME=geoscope.db
```

## 🤝 Contributing

Contributions are welcome! Please submit a Pull Request.

## 🎮 Easter Eggs

Run `geoscope init` and look for the WOPR greeting.

## ⚠️ Disclaimer

This tool is for **educational and research purposes only**. The authors are not responsible for misuse. Always adhere to local laws and terms of service when scraping data.

---

*"The only winning move is not to play."* — WOPR
