import feedparser
import requests
import json
from datetime import datetime
from rich.console import Console
from rich.progress import Progress
from geoscope.database import SessionLocal, IntelItem
from geoscope.core.utils import logger

console = Console()

# Enhanced feed sources
CYBER_FEEDS = {
    "The Hacker News": "http://feeds.feedburner.com/TheHackersNews",
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
    "Dark Reading": "https://www.darkreading.com/rss.xml",
    "US-CERT Alerts": "https://www.cisa.gov/uscert/ncas/alerts.xml",
    "Threatpost": "https://threatpost.com/feed/",
    "SecurityWeek": "https://feeds.feedburner.com/securityweek",
}


class CYBINTManager:
    def __init__(self):
        self.db = SessionLocal()

    def fetch_cisa_exploits(self):
        """
        Fetches the CISA Known Exploited Vulnerabilities Catalog (JSON).
        """
        url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        console.print(f"[cyan]Querying CISA Known Exploited Vulnerabilities...[/cyan]")
        
        try:
            resp = requests.get(url, timeout=15)
            data = resp.json()
            
            vulnerabilities = data.get("vulnerabilities", [])
            count = 0
            
            # Process most recent 20 (was 10)
            for vuln in vulnerabilities[:20]:
                cve_id = vuln.get("cveID")
                desc = vuln.get("shortDescription")
                vendor = vuln.get("vendorProject", "Unknown")
                product = vuln.get("product", "Unknown")
                
                # Deduplicate
                if self.db.query(IntelItem).filter_by(source_url=cve_id).first():
                    continue

                item = IntelItem(
                    timestamp=datetime.utcnow(),
                    int_category="CYBINT",
                    source_url=cve_id,
                    keyword=vendor,
                    raw_text=str(vuln),
                    summary=f"🔴 ACTIVE EXPLOIT: {cve_id} - {product} - {desc}",
                    country="Global",
                    threat_level="CRITICAL",
                    threat_score=95,
                    confidence=1.0
                )
                
                self.db.add(item)
                count += 1
            
            self.db.commit()
            console.print(f"[green]Ingested {count} new critical exploits from CISA.[/green]")

        except Exception as e:
            logger.error(f"CYBINT Error: {e}")

    def fetch_feed(self, url: str, source_name: str, limit: int = 10):
        """
        Generic RSS fetcher for Cyber feeds.
        """
        console.print(f"[cyan]Polling {source_name}...[/cyan]")
        
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            console.print(f"[yellow]Failed to fetch {source_name}: {e}[/yellow]")
            return 0
        
        count = 0
        for entry in feed.entries[:limit]:
            link = getattr(entry, 'link', None)
            if not link:
                continue
                
            if self.db.query(IntelItem).filter_by(source_url=link).first():
                continue
            
            title = getattr(entry, 'title', 'No Title')
            summary = getattr(entry, 'summary', getattr(entry, 'description', ''))
            
            # Determine threat level based on keywords
            threat_level = "UNKNOWN"
            threat_score = 50
            high_threat_keywords = ['critical', 'exploit', 'zero-day', '0day', 'ransomware', 
                                   'breach', 'attack', 'malware', 'vulnerability', 'CVE-']
            if any(kw.lower() in title.lower() or kw.lower() in summary.lower() 
                   for kw in high_threat_keywords):
                threat_level = "HIGH"
                threat_score = 75
            
            item = IntelItem(
                timestamp=datetime.utcnow(),
                int_category="CYBINT",
                source_url=link,
                keyword="Cyber News",
                raw_text=summary[:2000] if summary else '',
                summary=f"[{source_name}] {title}",
                author=source_name,
                country="Global",
                threat_level=threat_level,
                threat_score=threat_score
            )
            self.db.add(item)
            count += 1
            
        self.db.commit()
        if count > 0:
            console.print(f"[green]  ↳ Ingested {count} articles from {source_name}[/green]")
        return count

    def scan_all(self, limit_per_feed: int = 10):
        """
        Scan all configured cyber intelligence feeds.
        """
        console.print("[bold cyan]Starting comprehensive CYBINT scan...[/bold cyan]")
        
        total = 0
        
        # CISA Exploits first
        self.fetch_cisa_exploits()
        
        # All RSS feeds
        with Progress() as progress:
            task = progress.add_task("[cyan]Scanning feeds...", total=len(CYBER_FEEDS))
            
            for name, url in CYBER_FEEDS.items():
                count = self.fetch_feed(url, name, limit=limit_per_feed)
                total += count
                progress.advance(task)
        
        console.print(f"[bold green]CYBINT Scan Complete. Total new items: {total}[/bold green]")