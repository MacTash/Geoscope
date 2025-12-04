"""
Geoscope ADSINT - ADS-B Aircraft Intelligence
Tracks military and interesting aircraft via OpenSky Network API.
"""

import requests
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from synscope.database import SessionLocal, IntelItem
from synscope.core.utils import logger

console = Console()

# OpenSky Network API (Free, no auth required for basic queries)
OPENSKY_API = "https://opensky-network.org/api"

# Military callsign prefixes to watch
MILITARY_CALLSIGNS = [
    "RCH",    # REACH - USAF airlift
    "DUKE",   # Special operations
    "EVIL",   # Fighter callsign
    "KNIFE",  # Special ops
    "VIKING", # Navy
    "DOOM",   # B-52 callsign
    "DEATH",  # B-1 callsign
    "BONE",   # B-1 Lancer
    "GHOST",  # Stealth
    "SNAKE",  # Attack helo
    "ARROW",  # Fighter
    "NATO",   # NATO aircraft
    "RRR",    # RAF tanker
    "MMF",    # French AF
    "IAM",    # Italian AF
    "GAF",    # German AF
    "FORTE",  # RQ-4 Global Hawk
    "LAGR",   # KC-135 tanker
]

# Aircraft of interest (ICAO hex codes for known recon/military)
INTERESTING_AIRCRAFT = {
    "AE01D5": "USAF E-4B Nightwatch (Doomsday Plane)",
    "AE041B": "USAF RC-135V Rivet Joint",
    "AE0425": "USAF RC-135W Rivet Joint",
    "AE5420": "USAF E-6B Mercury (TACAMO)",
    "43C6C4": "RAF RC-135W Rivet Joint",
}


class ADSINTManager:
    """Tracks aircraft via ADS-B data from OpenSky Network."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def scan_region(self, lat_min: float, lat_max: float, lon_min: float, lon_max: float):
        """
        Scan a geographic bounding box for aircraft.
        
        Example regions:
        - Ukraine: 44.0, 52.5, 22.0, 40.5
        - Taiwan Strait: 22.0, 27.0, 116.0, 122.0
        - Baltic Sea: 53.0, 60.0, 10.0, 30.0
        """
        console.print(f"[cyan]Scanning region: {lat_min},{lon_min} to {lat_max},{lon_max}[/cyan]")
        
        try:
            response = requests.get(
                f"{OPENSKY_API}/states/all",
                params={
                    "lamin": lat_min,
                    "lamax": lat_max,
                    "lomin": lon_min,
                    "lomax": lon_max
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            console.print(f"[red]OpenSky API error: {e}[/red]")
            return []
        
        states = data.get("states", [])
        if not states:
            console.print("[yellow]No aircraft in region.[/yellow]")
            return []
        
        console.print(f"[green]Found {len(states)} aircraft. Filtering for military...[/green]")
        
        military_count = 0
        results = []
        
        for state in states:
            icao24 = state[0]
            callsign = (state[1] or "").strip()
            origin_country = state[2]
            longitude = state[5]
            latitude = state[6]
            altitude = state[7]  # meters
            velocity = state[9]  # m/s
            
            # Check if military callsign
            is_military = any(callsign.upper().startswith(prefix) for prefix in MILITARY_CALLSIGNS)
            is_known = icao24.upper() in INTERESTING_AIRCRAFT
            
            if is_military or is_known:
                military_count += 1
                
                aircraft_name = INTERESTING_AIRCRAFT.get(icao24.upper(), f"Military ({callsign})")
                
                # Check for duplicates
                source_id = f"ADSINT-{icao24}-{datetime.now().strftime('%Y%m%d%H')}"
                if self.db.query(IntelItem).filter_by(source_url=source_id).first():
                    continue
                
                threat_level = "HIGH" if is_known else "ELEVATED"
                threat_score = 75 if is_known else 50
                
                summary = (
                    f"🛩️ {aircraft_name} | Callsign: {callsign} | "
                    f"Alt: {altitude:.0f}m | Speed: {velocity:.0f}m/s | Origin: {origin_country}"
                )
                
                item = IntelItem(
                    timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                    int_category="ADSINT",
                    source_url=source_id,
                    keyword=callsign or icao24,
                    raw_text=f"ICAO: {icao24}, Callsign: {callsign}, Country: {origin_country}",
                    summary=summary,
                    country=origin_country,
                    latitude=latitude,
                    longitude=longitude,
                    threat_level=threat_level,
                    threat_score=threat_score,
                    confidence=1.0
                )
                
                self.db.add(item)
                results.append({
                    "callsign": callsign,
                    "icao24": icao24,
                    "type": aircraft_name,
                    "country": origin_country,
                    "lat": latitude,
                    "lon": longitude,
                    "alt": altitude
                })
        
        self.db.commit()
        console.print(f"[bold green]Tracked {military_count} military aircraft.[/bold green]")
        return results
    
    def scan_preset(self, region: str):
        """Scan predefined regions of interest."""
        presets = {
            "ukraine": (44.0, 52.5, 22.0, 40.5),
            "taiwan": (21.0, 26.0, 116.0, 123.0),
            "baltic": (53.0, 60.0, 10.0, 30.0),
            "korea": (33.0, 43.0, 124.0, 132.0),
            "gulf": (23.0, 32.0, 47.0, 60.0),
            "mediterranean": (30.0, 42.0, -6.0, 36.0),
            "global": (-60.0, 70.0, -180.0, 180.0),  # Very slow, use sparingly
        }
        
        if region.lower() not in presets:
            console.print(f"[yellow]Unknown region. Available: {', '.join(presets.keys())}[/yellow]")
            return []
        
        coords = presets[region.lower()]
        return self.scan_region(*coords)
    
    def track_callsign(self, callsign: str):
        """Track a specific aircraft by callsign."""
        console.print(f"[cyan]Searching for callsign: {callsign}[/cyan]")
        
        try:
            response = requests.get(f"{OPENSKY_API}/states/all", timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            console.print(f"[red]API error: {e}[/red]")
            return None
        
        for state in data.get("states", []):
            if state[1] and callsign.upper() in state[1].upper():
                icao24 = state[0]
                cs = state[1].strip()
                country = state[2]
                lat, lon = state[6], state[5]
                alt = state[7]
                
                console.print(f"[green]✓ Found: {cs} | {country} | {lat:.2f}, {lon:.2f} | Alt: {alt}m[/green]")
                return {
                    "callsign": cs,
                    "icao24": icao24,
                    "country": country,
                    "lat": lat,
                    "lon": lon,
                    "altitude": alt
                }
        
        console.print(f"[yellow]Callsign not found in current airspace.[/yellow]")
        return None
    
    def list_recent(self, limit: int = 10):
        """List recently tracked aircraft from database."""
        items = self.db.query(IntelItem).filter(
            IntelItem.int_category == "ADSINT"
        ).order_by(IntelItem.timestamp.desc()).limit(limit).all()
        
        if not items:
            console.print("[yellow]No ADSINT data in database.[/yellow]")
            return
        
        table = Table(title="✈️ Recent Aircraft Tracks")
        table.add_column("Time", style="dim")
        table.add_column("Callsign", style="cyan")
        table.add_column("Country", style="green")
        table.add_column("Summary")
        table.add_column("Threat")
        
        for item in items:
            table.add_row(
                str(item.timestamp)[:16],
                item.keyword or "-",
                item.country or "-",
                (item.summary or "")[:40] + "...",
                item.threat_level or "-"
            )
        
        console.print(table)
