# 🌐 Geoscope CLI

**Geoscope** is a powerful Multi-INT (Multi-Intelligence) fusion tool designed for open-source intelligence gathering, analysis, and visualization. It aggregates data from OSINT, SOCMINT, GEOINT, SIGNALS, and CYBINT sources, analyzes it using local LLMs (Ollama), and presents actionable intelligence via interactive maps and military-style reports.

![Geoscope Map](https://placeholder-image-url.com/map_preview.png)

## 🚀 Features

- **Multi-INT Collection**:
  - **OSINT**: News aggregation via DuckDuckGo.
  - **SOCMINT**: Social media scraping (Twitter/X, Reddit, Telegram).
  - **GEOINT**: Satellite imagery metadata (Sentinel-2, Landsat).
  - **SIGNALS**: SDR log ingestion and EAM (Emergency Action Message) detection.
  - **CYBINT**: Cyber threat intelligence from CISA KEV and 7+ security feeds.
- **AI Analysis**: Uses local LLMs (Llama 3, Mistral) via Ollama for threat scoring and summarization.
- **Visualization**: Interactive Folium maps and threat heatmaps.
- **Reporting**: Generates professional military-style intelligence assessments (SITREPs).

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

What it does (5 phases):
📊 Topic Assessment - LLM analyzes target, suggests keywords
📥 Collection Sweep - Fetches from all relevant INT sources
🗃️ Data Aggregation - Queries and categorizes intel
🤖 LLM Synthesis - Generates military-style assessment with:
Executive Summary
Threat Matrix
Key Intelligence by domain
IOCs & TTPs (the llm might rarely include OSINT x.com accounts as IOCs)
Confidence assessment
🗺️ Map Generation - Creates interactive Folium map
Flags:
        Flag	                                Effect
--sweep / --no-sweep	                Enable/disable fresh data collection
--html	                                Export report to HTML file
--hours 24,48,72	                    Lookback window for existing data
--no-map	                            Skip map generation

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

#### **SIGNALS (Signals Intelligence)** (COMING SOON)
Analyze radio intercepts.
```bash
# Ingest SDR logs
geoscope signals ingest --file logs/sdr_capture.txt

# Analyze text for EAM patterns
geoscope signals analyze "SKYKING SKYKING DO NOT ANSWER"
```

### 5. 📤 Data Management
Export your intelligence database.
```bash
# Export to JSON
geoscope export --format json --output intel_dump.json

# Export to CSV
geoscope export --format csv
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

## ⚠️ Disclaimer

This tool is for **educational and research purposes only**. The authors are not responsible for misuse. Always adhere to local laws and terms of service when scraping data.
