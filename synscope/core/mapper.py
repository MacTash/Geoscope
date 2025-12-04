"""
Geoscope Mapper - Interactive map visualization for intelligence data.
Generates Folium maps with color-coded markers by intel category.
"""

import folium
from folium.plugins import MarkerCluster
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta, timezone
from rich.console import Console
from synscope.database import SessionLocal, IntelItem
from synscope.config import settings

console = Console()

# Color mapping for intel categories
CATEGORY_COLORS = {
    "OSINT": "blue",
    "SOCMINT": "purple",
    "GEOINT": "green",
    "COMINT": "orange",
    "CYBINT": "red",
    "SIGNALS": "orange"
}

# Icon mapping for intel categories
CATEGORY_ICONS = {
    "OSINT": "newspaper-o",
    "SOCMINT": "comments",
    "GEOINT": "globe",
    "COMINT": "signal",
    "CYBINT": "bug",
    "SIGNALS": "signal"
}

THREAT_COLORS = {
    "CRITICAL": "darkred",
    "HIGH": "red",
    "ELEVATED": "orange",
    "LOW": "green",
    "UNKNOWN": "gray"
}


class GeoMapper:
    """Generates interactive Folium maps from intelligence data."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.output_dir = settings.DATA_DIR / "maps"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_map(
        self,
        country: str = None,
        hours: int = 72,
        open_browser: bool = True
    ) -> Path:
        """
        Generate an interactive map from recent intelligence.
        
        Args:
            country: Filter by country/region (None = all)
            hours: Lookback window in hours
            open_browser: Auto-open in browser
            
        Returns:
            Path to generated HTML file
        """
        console.print(f"[cyan]Generating intelligence map...[/cyan]")
        
        # Query database
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        since = now_utc - timedelta(hours=hours)
        
        query = self.db.query(IntelItem).filter(
            IntelItem.timestamp >= since,
            IntelItem.latitude.isnot(None),
            IntelItem.longitude.isnot(None)
        )
        
        if country and country.lower() != "global":
            query = query.filter(IntelItem.country.ilike(f"%{country}%"))
        
        items = query.all()
        
        if not items:
            console.print("[yellow]No geolocated intelligence found. Try running geoint first.[/yellow]")
            # Still generate a base map
            items = []
        
        # Determine map center
        if items:
            avg_lat = sum(i.latitude for i in items) / len(items)
            avg_lon = sum(i.longitude for i in items) / len(items)
            zoom = 5
        else:
            # Default to world view
            avg_lat, avg_lon = 30.0, 0.0
            zoom = 2
        
        # Create base map with dark tiles
        m = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=zoom,
            tiles="CartoDB dark_matter"
        )
        
        # Add title
        title_html = f'''
            <div style="position: fixed; 
                        top: 10px; left: 50%; transform: translateX(-50%);
                        z-index: 9999; 
                        background: rgba(0,0,0,0.8); 
                        padding: 10px 20px; 
                        border-radius: 8px;
                        border: 1px solid #dc2626;">
                <h4 style="color: #dc2626; margin: 0; font-family: monospace;">
                    🌐 GEOSCOPE INTEL MAP
                </h4>
                <p style="color: #888; margin: 5px 0 0 0; font-size: 12px;">
                    {len(items)} items | Last {hours}h | {country or 'Global'}
                </p>
            </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Create marker cluster
        marker_cluster = MarkerCluster(name="Intelligence").add_to(m)
        
        # Add markers
        for item in items:
            color = CATEGORY_COLORS.get(item.int_category, "gray")
            icon_name = CATEGORY_ICONS.get(item.int_category, "info-sign")
            threat_color = THREAT_COLORS.get(item.threat_level, "gray")
            
            # Create popup content
            popup_html = f"""
            <div style="width: 300px; font-family: Arial, sans-serif;">
                <h4 style="color: {threat_color}; margin: 0 0 8px 0;">
                    [{item.int_category}] {item.threat_level or 'UNKNOWN'}
                </h4>
                <p style="font-size: 13px; margin: 0 0 8px 0;">
                    <strong>Summary:</strong><br>
                    {item.summary[:200] if item.summary else 'No summary'}...
                </p>
                <p style="font-size: 11px; color: #666; margin: 0;">
                    <strong>Country:</strong> {item.country}<br>
                    <strong>Keyword:</strong> {item.keyword}<br>
                    <strong>Confidence:</strong> {item.confidence:.0%}<br>
                    <strong>Time:</strong> {item.timestamp}
                </p>
                <a href="{item.source_url}" target="_blank" 
                   style="font-size: 11px; color: #3b82f6;">
                   View Source ↗
                </a>
            </div>
            """
            
            folium.Marker(
                location=[item.latitude, item.longitude],
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=f"{item.int_category}: {item.keyword}",
                icon=folium.Icon(
                    color=color,
                    icon=icon_name,
                    prefix="fa"
                )
            ).add_to(marker_cluster)
        
        # Add legend
        legend_html = self._create_legend()
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Save map
        filename = f"synscope_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        output_path = self.output_dir / filename
        m.save(str(output_path))
        
        console.print(f"[green]Map saved: {output_path}[/green]")
        
        if open_browser:
            console.print("[dim]Opening in browser...[/dim]")
            webbrowser.open(f"file://{output_path}")
        
        return output_path
    
    def _create_legend(self) -> str:
        """Create HTML legend for the map."""
        items = "".join([
            f'<li><span style="background:{color}; width:12px; height:12px; '
            f'display:inline-block; border-radius:50%; margin-right:8px;"></span>{cat}</li>'
            for cat, color in CATEGORY_COLORS.items()
        ])
        
        return f'''
            <div style="position: fixed; 
                        bottom: 30px; right: 30px;
                        z-index: 9999; 
                        background: rgba(0,0,0,0.85); 
                        padding: 12px 16px; 
                        border-radius: 8px;
                        border: 1px solid #333;
                        font-family: monospace;
                        font-size: 12px;
                        color: #ccc;">
                <strong style="color: white;">Intel Categories</strong>
                <ul style="list-style: none; padding: 0; margin: 8px 0 0 0;">
                    {items}
                </ul>
            </div>
        '''
    
    def generate_heatmap(self, country: str = None, hours: int = 72) -> Path:
        """Generate a heatmap visualization of threat intensity."""
        from folium.plugins import HeatMap
        
        console.print(f"[cyan]Generating threat heatmap...[/cyan]")
        
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        since = now_utc - timedelta(hours=hours)
        
        query = self.db.query(IntelItem).filter(
            IntelItem.timestamp >= since,
            IntelItem.latitude.isnot(None),
            IntelItem.longitude.isnot(None)
        )
        
        if country and country.lower() != "global":
            query = query.filter(IntelItem.country.ilike(f"%{country}%"))
        
        items = query.all()
        
        if not items:
            console.print("[yellow]No geolocated data for heatmap.[/yellow]")
            return None
        
        # Create heat data: [lat, lon, weight]
        heat_data = [
            [item.latitude, item.longitude, item.threat_score / 100]
            for item in items
            if item.threat_score
        ]
        
        # Create map
        avg_lat = sum(i.latitude for i in items) / len(items)
        avg_lon = sum(i.longitude for i in items) / len(items)
        
        m = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=4,
            tiles="CartoDB dark_matter"
        )
        
        HeatMap(
            heat_data,
            radius=25,
            blur=15,
            gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}
        ).add_to(m)
        
        filename = f"synscope_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        output_path = self.output_dir / filename
        m.save(str(output_path))
        
        console.print(f"[green]Heatmap saved: {output_path}[/green]")
        webbrowser.open(f"file://{output_path}")
        
        return output_path
