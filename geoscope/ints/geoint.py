# ... imports remain the same ...
import pystac_client
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
from rich.console import Console
from geoscope.database import SessionLocal, IntelItem
from geoscope.core.utils import logger

console = Console()

class GEOINTManager:
    def __init__(self):
        self.db = SessionLocal()
        self.geocoder = Nominatim(user_agent="geoscope_toolkit_v2")
        self.stac_api_url = "https://earth-search.aws.element84.com/v1"

    def get_coordinates(self, location_name: str):
        try:
            location = self.geocoder.geocode(location_name)
            if location:
                return location.latitude, location.longitude
            return None, None
        except Exception as e:
            logger.error(f"Geocoding failed: {e}")
            return None, None

    # UPDATED METHOD: Added cloud_max parameter
    def search_satellite_metadata(self, location_name: str, days_back: int = 7, cloud_max: int = 50):
        lat, lon = self.get_coordinates(location_name)
        if not lat:
            console.print(f"[red]Could not locate '{location_name}'.[/red]")
            return

        console.print(f"[cyan]Searching Sentinel-2 imagery for {location_name} ({lat}, {lon})...[/cyan]")
        console.print(f"[dim]Criteria: Last {days_back} days, <{cloud_max}% cloud cover[/dim]")

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        date_range = f"{start_date.isoformat()}Z/{end_date.isoformat()}Z" # Added Z for UTC strictness

        try:
            client = pystac_client.Client.open(self.stac_api_url)
            search = client.search(
                collections=["sentinel-2-l2a"],
                bbox=[lon - 0.1, lat - 0.1, lon + 0.1, lat + 0.1],
                datetime=date_range,
                query={"eo:cloud_cover": {"lt": cloud_max}}, # Uses the dynamic cloud_max
                max_items=10
            )
            
            items = list(search.items())
            
            if not items:
                console.print(f"[yellow]No imagery found. Try increasing cloud cover tolerance.[/yellow]")
                return

            for item in items:
                props = item.properties
                acquisition_date = props.get("datetime")
                cloud_cover = props.get("eo:cloud_cover")
                
                summary = (
                    f"Satellite Pass: Sentinel-2. "
                    f"Cloud Cover: {cloud_cover}%. "
                    f"Date: {acquisition_date}."
                )

                # Check dupes
                if self.db.query(IntelItem).filter_by(source_url=f"STAC:{item.id}").first():
                    continue

                intel = IntelItem(
                    timestamp=datetime.fromisoformat(acquisition_date.replace("Z", "+00:00")),
                    int_category="GEOINT",
                    source_url=f"STAC:{item.id}",
                    keyword=location_name,
                    raw_text=str(props),
                    summary=summary,
                    country=location_name, 
                    threat_score=0,
                    latitude=lat,
                    longitude=lon
                )
                self.db.add(intel)
            
            self.db.commit()
            console.print(f"[green]Successfully logged {len(items)} satellite passes.[/green]")

        except Exception as e:
            logger.error(f"STAC API Error: {e}")