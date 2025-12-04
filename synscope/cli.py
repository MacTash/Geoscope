import typer
import os
from rich.console import Console
from rich.panel import Panel
from datetime import timedelta, datetime, timezone
from sqlalchemy import or_

# Internal Imports
from synscope.config import settings
from synscope.database import init_db, SessionLocal, IntelItem
from synscope.ints.osint import OSINTManager
from synscope.ints.socmint import SOCMINTManager
from synscope.ints.geoint import GEOINTManager
from synscope.ints.adsint import ADSINTManager
from synscope.ints.cybint import CYBINTManager
from synscope.ints.maritint import MARITINTManager
from synscope.core.theme import print_banner, print_defcon_status, calculate_defcon, print_header

# --- HELP TEXTS ---
HELP_OSINT = "Fetch news articles via DuckDuckGo.\nExample: [green]synscope osint fetch --keyword 'Ukraine'[/green]"
HELP_SOCMINT = "Scrape Social Media (X, Reddit, Telegram).\nExample: [green]synscope socmint scrape --keyword 'Cyberattack'[/green]"
HELP_GEOINT = "Search Satellite Metadata (Sentinel-2).\nExample: [green]synscope geoint sat --target 'Suez Canal'[/green]"
HELP_REPORT = "Generate fusion intelligence briefings.\nExample: [green]synscope report brief --country 'Ukraine'[/green]"

app = typer.Typer(help="Geoscope CLI - Multi-INT Geopolitical Toolkit", rich_markup_mode="rich")

# Sub-Applications
osint_app = typer.Typer(help=HELP_OSINT, rich_markup_mode="rich")
socmint_app = typer.Typer(help=HELP_SOCMINT, rich_markup_mode="rich")
geoint_app = typer.Typer(help=HELP_GEOINT, rich_markup_mode="rich")
adsint_app = typer.Typer(help="Aircraft Intelligence (ADS-B Tracking)", rich_markup_mode="rich")
maritint_app = typer.Typer(help="Maritime Intelligence (Naval/Ship Tracking)", rich_markup_mode="rich")
cybint_app = typer.Typer(help="Cyber Intelligence (CISA/Exploits)", rich_markup_mode="rich")
report_app = typer.Typer(help=HELP_REPORT, rich_markup_mode="rich")

app.add_typer(osint_app, name="osint")
app.add_typer(socmint_app, name="socmint")
app.add_typer(geoint_app, name="geoint")
app.add_typer(adsint_app, name="adsint")
app.add_typer(maritint_app, name="maritint")
app.add_typer(cybint_app, name="cybint")
app.add_typer(report_app, name="report")

console = Console()

# --- GLOBAL COMMANDS ---

@app.command()
def init():
    """Initialize the Database with DEFCON-style welcome."""
    print_banner(show_greeting=True)
    init_db()
    console.print("[bold green]SYSTEM INITIALIZED. DATABASE ONLINE.[/bold green]")

@app.command()
def reset(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """
    Wipe the entire database and start fresh.
    """
    db_path = settings.DATA_DIR / settings.DB_NAME
    
    if not force:
        delete = typer.confirm(f"⚠️  WARNING: This will permanently delete all intelligence in {db_path}. Continue?")
        if not delete:
            console.print("[bold red]Aborted.[/bold red]")
            raise typer.Abort()
    
    if db_path.exists():
        os.remove(db_path)
        console.print(f"[yellow]Deleted database: {db_path}[/yellow]")
    else:
        console.print("[yellow]No database found to delete.[/yellow]")
        
    # Re-initialize immediately
    init_db()
    console.print("[bold green]System Reset Complete. New database ready.[/bold green]")


@app.command()
def clean(
    pycache: bool = typer.Option(True, "--pycache/--no-pycache", help="Remove __pycache__ directories"),
    reports: bool = typer.Option(False, "--reports", "-r", help="Remove old HTML reports and maps"),
    all_clean: bool = typer.Option(False, "--all", "-a", help="Clean everything")
):
    """
    Clean up cache files and old reports.
    
    [bold]Examples:[/bold]
    synscope clean              # Remove pycache only
    synscope clean --reports    # Also remove old reports
    synscope clean --all        # Remove everything
    """
    import shutil
    from pathlib import Path
    
    project_root = Path(__file__).resolve().parent.parent
    
    removed_count = 0
    
    # Clean __pycache__
    if pycache or all_clean:
        console.print("[cyan]Cleaning __pycache__ directories...[/cyan]")
        for cache_dir in project_root.rglob("__pycache__"):
            try:
                shutil.rmtree(cache_dir)
                removed_count += 1
                console.print(f"  [dim]Removed: {cache_dir}[/dim]")
            except Exception as e:
                console.print(f"  [red]Failed: {cache_dir} ({e})[/red]")
        
        # Also remove .pyc files
        for pyc_file in project_root.rglob("*.pyc"):
            try:
                pyc_file.unlink()
                removed_count += 1
            except:
                pass
    
    # Clean old reports and maps
    if reports or all_clean:
        console.print("[cyan]Cleaning old reports and maps...[/cyan]")
        
        data_dir = settings.DATA_DIR
        maps_dir = data_dir / "maps"
        reports_dir = data_dir / "reports"
        
        for target_dir in [maps_dir, reports_dir]:
            if target_dir.exists():
                for html_file in target_dir.glob("*.html"):
                    try:
                        html_file.unlink()
                        removed_count += 1
                        console.print(f"  [dim]Removed: {html_file.name}[/dim]")
                    except Exception as e:
                        console.print(f"  [red]Failed: {html_file} ({e})[/red]")
    
    console.print(f"[bold green]✓ Cleanup complete. Removed {removed_count} items.[/bold green]")

# --- OSINT ---
@osint_app.command("fetch")
def osint_fetch(
    keyword: str = typer.Option(..., help="Topic to track (e.g., 'Taiwan')"),
    limit: int = typer.Option(50, help="Max articles")
):
    """
    Fetch news from DuckDuckGo.
    
    [bold]Example:[/bold]
    synscope osint fetch --keyword "Gaza" --limit 20
    """
    manager = OSINTManager()
    manager.bulk_fetch(keyword, limit)

@osint_app.command("list")
def osint_list(
    limit: int = typer.Option(10, help="Max items to show"),
    keyword: str = typer.Option(None, help="Filter by keyword")
):
    """List recent OSINT items."""
    from rich.table import Table
    db = SessionLocal()
    query = db.query(IntelItem).filter(IntelItem.int_category == "OSINT")
    if keyword:
        query = query.filter(IntelItem.keyword.ilike(f"%{keyword}%"))
    items = query.order_by(IntelItem.timestamp.desc()).limit(limit).all()
    
    table = Table(title="📰 OSINT Intelligence")
    table.add_column("Time", style="dim")
    table.add_column("Keyword", style="cyan")
    table.add_column("Summary")
    table.add_column("Threat", style="red")
    
    for item in items:
        table.add_row(
            str(item.timestamp)[:16],
            item.keyword or "-",
            (item.summary or "")[:50] + "...",
            item.threat_level or "-"
        )
    console.print(table)

@osint_app.command("search")
def osint_search(query: str = typer.Argument(..., help="Search term")):
    """Search OSINT summaries."""
    db = SessionLocal()
    items = db.query(IntelItem).filter(
        IntelItem.int_category == "OSINT",
        or_(
            IntelItem.summary.ilike(f"%{query}%"),
            IntelItem.raw_text.ilike(f"%{query}%")
        )
    ).limit(20).all()
    
    console.print(f"[cyan]Found {len(items)} matches for '{query}'[/cyan]\n")
    for item in items:
        console.print(f"[{item.threat_level}] {item.summary[:80]}...")
        console.print(f"  [dim]Source: {item.source_url}[/dim]\n")


# --- SOCMINT ---
@socmint_app.command("scrape")
def socmint_scrape(
    keyword: str = typer.Option(..., help="Keyword to search for"),
    limit: int = typer.Option(50, help="Max posts to scrape"),
    user: str = typer.Option(None, help="Target specific X account (without @)"),
    subreddit: str = typer.Option(None, help="Target specific Subreddit (without r/)")
):
    """
    Scrape Social Media via DuckDuckGo.
    
    [bold]Examples:[/bold]
    1. Broad search:
       synscope socmint scrape --keyword "missile"
    
    2. Target X User:
       synscope socmint scrape --keyword "frontline" --user "ZelenskyyUa"
       
    3. Target Subreddit:
       synscope socmint scrape --keyword "analysis" --subreddit "geopolitics"
    """
    manager = SOCMINTManager()
    manager.run_social_search(keyword, limit, user, subreddit)

@socmint_app.command("list")
def socmint_list(
    limit: int = typer.Option(10, help="Max items"),
    platform: str = typer.Option(None, help="Filter: reddit, twitter, telegram")
):
    """List recent SOCMINT items."""
    from rich.table import Table
    db = SessionLocal()
    query = db.query(IntelItem).filter(IntelItem.int_category == "SOCMINT")
    if platform:
        query = query.filter(IntelItem.source_url.ilike(f"%{platform}%"))
    items = query.order_by(IntelItem.timestamp.desc()).limit(limit).all()
    
    table = Table(title="💬 SOCMINT Intelligence")
    table.add_column("Time", style="dim")
    table.add_column("Platform", style="purple")
    table.add_column("Summary")
    table.add_column("Threat")
    
    for item in items:
        platform_name = "Unknown"
        if "reddit" in (item.source_url or "").lower(): platform_name = "Reddit"
        elif "twitter" in (item.source_url or "").lower() or "x.com" in (item.source_url or "").lower(): platform_name = "X"
        elif "t.me" in (item.source_url or "").lower(): platform_name = "Telegram"
        
        table.add_row(
            str(item.timestamp)[:16],
            platform_name,
            (item.summary or "")[:50] + "...",
            item.threat_level or "-"
        )
    console.print(table)

@socmint_app.command("trending")
def socmint_trending():
    """Show trending keywords from SOCMINT."""
    from sqlalchemy import func
    db = SessionLocal()
    keywords = db.query(
        IntelItem.keyword, 
        func.count(IntelItem.id).label('count')
    ).filter(
        IntelItem.int_category == "SOCMINT"
    ).group_by(IntelItem.keyword).order_by(func.count(IntelItem.id).desc()).limit(10).all()
    
    console.print("[bold]📈 Trending SOCMINT Keywords:[/bold]")
    for kw, count in keywords:
        bar = "█" * min(count, 20)
        console.print(f"  {kw or 'N/A'}: {bar} ({count})")


# --- GEOINT ---
@geoint_app.command("sat")
def geoint_sat(
    target: str = typer.Option(..., help="Location name"),
    days: int = typer.Option(7, help="Days back"),
    clouds: int = typer.Option(50, help="Max cloud cover %")
):
    """
    Find recent satellite imagery metadata.
    
    [bold]Example:[/bold]
    synscope geoint sat --target "Kiev" --clouds 100
    """
    manager = GEOINTManager()
    manager.search_satellite_metadata(target, days_back=days, cloud_max=clouds)

@geoint_app.command("list")
def geoint_list(limit: int = typer.Option(10, help="Max items")):
    """List recent GEOINT items."""
    from rich.table import Table
    db = SessionLocal()
    items = db.query(IntelItem).filter(
        IntelItem.int_category == "GEOINT"
    ).order_by(IntelItem.timestamp.desc()).limit(limit).all()
    
    table = Table(title="🛰️ GEOINT Intelligence")
    table.add_column("Date", style="dim")
    table.add_column("Location", style="green")
    table.add_column("Summary")
    table.add_column("Coords")
    
    for item in items:
        coords = f"{item.latitude:.2f}, {item.longitude:.2f}" if item.latitude else "-"
        table.add_row(
            str(item.timestamp)[:10],
            item.keyword or "-",
            (item.summary or "")[:40] + "...",
            coords
        )
    console.print(table)

@geoint_app.command("locate")
def geoint_locate(location: str = typer.Argument(..., help="Location to geocode")):
    """Get coordinates for a location."""
    manager = GEOINTManager()
    lat, lon = manager.get_coordinates(location)
    if lat:
        console.print(f"[green]{location}:[/green] {lat:.6f}, {lon:.6f}")
    else:
        console.print(f"[red]Could not geocode '{location}'[/red]")


# --- ADSINT (Aircraft Intelligence) ---
@adsint_app.command("scan")
def adsint_scan(
    region: str = typer.Argument("ukraine", help="Region: ukraine, taiwan, baltic, korea, gulf, mediterranean")
):
    """
    Scan a region for military aircraft via ADS-B.
    
    [bold]Example:[/bold]
    synscope adsint scan ukraine
    synscope adsint scan taiwan
    """
    manager = ADSINTManager()
    results = manager.scan_preset(region)
    if results:
        console.print(f"[green]Tracked {len(results)} military aircraft.[/green]")

@adsint_app.command("track")
def adsint_track(callsign: str = typer.Argument(..., help="Aircraft callsign (e.g., REACH, FORTE)")):
    """Track a specific aircraft by callsign."""
    manager = ADSINTManager()
    manager.track_callsign(callsign)

@adsint_app.command("list")
def adsint_list(limit: int = typer.Option(10, help="Max items")):
    """List recently tracked aircraft."""
    manager = ADSINTManager()
    manager.list_recent(limit)


# --- MARITINT (Maritime Intelligence) ---
@maritint_app.command("scan")
def maritint_scan(
    region: str = typer.Argument("black_sea", help="Region: black_sea, baltic, south_china_sea, persian_gulf, taiwan_strait, mediterranean, arctic")
):
    """
    Scan a maritime region for naval activity.
    
    [bold]Example:[/bold]
    synscope maritint scan black_sea
    synscope maritint scan taiwan_strait
    """
    manager = MARITINTManager()
    manager.scan_preset(region)

@maritint_app.command("search")
def maritint_search(name: str = typer.Argument(..., help="Vessel name or MMSI")):
    """Search for a specific vessel."""
    manager = MARITINTManager()
    manager.search_vessel(name)

@maritint_app.command("list")
def maritint_list(limit: int = typer.Option(10, help="Max items")):
    """List recent maritime intelligence."""
    manager = MARITINTManager()
    manager.list_recent(limit)

# --- CYBINT ---
@cybint_app.command("scan")
def cybint_scan(
    all_feeds: bool = typer.Option(True, "--all", help="Scan all configured feeds"),
    limit: int = typer.Option(10, help="Max items per feed")
):
    """
    Fetch cyber threat intelligence from multiple sources.
    
    [bold]Example:[/bold]
    synscope cybint scan --all --limit 15
    """
    manager = CYBINTManager()
    if all_feeds:
        manager.scan_all(limit_per_feed=limit)
    else:
        manager.fetch_cisa_exploits()

@cybint_app.command("list")
def cybint_list(
    limit: int = typer.Option(10, help="Max items"),
    critical: bool = typer.Option(False, help="Show only CRITICAL items")
):
    """List cyber threat intelligence."""
    from rich.table import Table
    db = SessionLocal()
    query = db.query(IntelItem).filter(IntelItem.int_category == "CYBINT")
    if critical:
        query = query.filter(IntelItem.threat_level == "CRITICAL")
    items = query.order_by(IntelItem.timestamp.desc()).limit(limit).all()
    
    table = Table(title="🔒 CYBINT Intelligence")
    table.add_column("Time", style="dim")
    table.add_column("Source", style="cyan")
    table.add_column("Summary")
    table.add_column("Threat", style="red")
    
    for item in items:
        threat_style = "red bold" if item.threat_level == "CRITICAL" else ""
        table.add_row(
            str(item.timestamp)[:16],
            (item.author or item.keyword or "-")[:15],
            (item.summary or "")[:50] + "...",
            item.threat_level or "-",
            style=threat_style if item.threat_level == "CRITICAL" else None
        )
    console.print(table)

@cybint_app.command("cves")
def cybint_cves(limit: int = typer.Option(10, help="Max CVEs to show")):
    """List recent CISA known exploited vulnerabilities."""
    from rich.table import Table
    db = SessionLocal()
    items = db.query(IntelItem).filter(
        IntelItem.int_category == "CYBINT",
        IntelItem.source_url.like("CVE-%")
    ).order_by(IntelItem.timestamp.desc()).limit(limit).all()
    
    table = Table(title="🔴 Active Exploits (CISA KEV)")
    table.add_column("CVE ID", style="red bold")
    table.add_column("Vendor", style="cyan")
    table.add_column("Description")
    
    for item in items:
        table.add_row(
            item.source_url or "-",
            item.keyword or "-",
            (item.summary or "")[:60] + "..."
        )
    console.print(table)

@cybint_app.command("search")
def cybint_search(query: str = typer.Argument(..., help="Search term")):
    """Search cyber threat intelligence."""
    db = SessionLocal()
    items = db.query(IntelItem).filter(
        IntelItem.int_category == "CYBINT",
        or_(
            IntelItem.summary.ilike(f"%{query}%"),
            IntelItem.source_url.ilike(f"%{query}%"),
            IntelItem.raw_text.ilike(f"%{query}%")
        )
    ).limit(20).all()
    
    console.print(f"[cyan]Found {len(items)} matches for '{query}'[/cyan]\n")
    for item in items:
        console.print(f"[{item.threat_level}] {item.summary[:80]}...")
        console.print(f"  [dim]{item.source_url}[/dim]\n")

# --- REPORT ---
@report_app.command("brief")
def generate_brief(
    country: str = typer.Option(..., help="Country/Region"),
    hours: int = typer.Option(24, help="Lookback window")
):
    """
    Generate Fusion Intelligence Report.
    
    [bold]Example:[/bold]
    synscope report brief --country "Ukraine" --hours 48
    """
    from synscope.core.llm import generate_summary
    
    db = SessionLocal()
    
    # Time Calculation (UTC Naive)
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    since = now_utc - timedelta(hours=hours)
    
    # Query: Filter by timestamp AND (Country match OR text match)
    query = db.query(IntelItem).filter(IntelItem.timestamp >= since)

    if country.lower() != "global":
        query = query.filter(
            or_(
                IntelItem.country.ilike(f"%{country}%"),
                IntelItem.summary.ilike(f"%{country}%"),
                IntelItem.raw_text.ilike(f"%{country}%"),
                IntelItem.keyword.ilike(f"%{country}%")
            )
        )
    
    items = query.all()
    
    if not items:
        console.print(Panel(f"[red]No intelligence found for {country} in the last {hours} hours.[/red]", title="Briefing Error"))
        return

    # Categorize
    data = {
        "OSINT": [x.summary for x in items if x.int_category == "OSINT"],
        "SOCMINT": [x.summary for x in items if x.int_category == "SOCMINT"],
        "GEOINT": [x.summary for x in items if x.int_category == "GEOINT"],
        "SIGNALS": [x.summary for x in items if x.int_category == "COMINT"],
        "CYBINT": [x.summary for x in items if x.int_category == "CYBINT"]
    }
    
    context = f"TARGET: {country}\nTIMEFRAME: {hours}h\n\n"
    for cat, logs in data.items():
        context += f"=== {cat} ===\n" + ("\n".join(logs[:15]) if logs else "No Data") + "\n\n"
    
    console.print(f"[bold blue]Synthesizing {len(items)} items...[/bold blue]")
    brief = generate_summary(context)
    
    console.print(Panel(brief, title=f"GEOSCOPE SITREP: {country.upper()}", subtitle=str(now_utc.date())))


@report_app.command("full")
def generate_full(
    target: str = typer.Argument(..., help="Topic to analyze (country, threat, actor)"),
    sweep: bool = typer.Option(True, "--sweep", help="Run fresh collection sweep"),
    hours: int = typer.Option(72, help="Lookback window for existing data"),
    limit: int = typer.Option(20, help="Max items to collect per source"),
    export_html: bool = typer.Option(False, "--html", help="Export report as HTML"),
    with_map: bool = typer.Option(True, "--map", help="Generate accompanying map")
):
    """
    Generate comprehensive military-style intelligence report.
    
    Runs a full sweep of all INT sources (optional), then synthesizes
    everything into a professional assessment using the LLM.
    
    [bold]Examples:[/bold]
    synscope report full "Ukraine"
    synscope report full "ransomware" --sweep --html
    synscope report full "China" --no-sweep --hours 48
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from synscope.core.llm import generate_full_report, assess_topic
    from pathlib import Path
    import time
    
    console.print(Panel(
        f"[bold red]GEOSCOPE FULL INTELLIGENCE SWEEP[/bold red]\n"
        f"[dim]Target: {target.upper()}[/dim]",
        border_style="red"
    ))
    
    db = SessionLocal()
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Step 1: Assess topic using LLM to get smart keywords
    if sweep:
        console.print("\n[cyan]Phase 1: Topic Assessment[/cyan]")
        with console.status("[bold]Analyzing target with LLM..."):
            assessment = assess_topic(target)
        
        keywords = assessment.get("keywords", [target])
        target_type = assessment.get("type", "unknown")
        domains = assessment.get("domains", ["OSINT", "CYBINT"])
        
        console.print(f"  Type: [yellow]{target_type}[/yellow]")
        console.print(f"  Keywords: [green]{', '.join(keywords)}[/green]")
        console.print(f"  Domains: [blue]{', '.join(domains)}[/blue]")
        
        # Step 2: Collection sweep
        console.print("\n[cyan]Phase 2: Intelligence Collection[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # OSINT
            if "OSINT" in domains:
                task = progress.add_task("[blue]Collecting OSINT...", total=None)
                try:
                    manager = OSINTManager()
                    for kw in keywords[:2]:
                        manager.bulk_fetch(kw, limit=limit)
                except Exception as e:
                    console.print(f"[yellow]OSINT collection warning: {e}[/yellow]")
                progress.remove_task(task)
            
            # SOCMINT
            if "SOCMINT" in domains:
                task = progress.add_task("[purple]Collecting SOCMINT...", total=None)
                try:
                    manager = SOCMINTManager()
                    for kw in keywords[:2]:
                        manager.run_social_search(kw, limit=limit)
                except Exception as e:
                    console.print(f"[yellow]SOCMINT collection warning: {e}[/yellow]")
                progress.remove_task(task)
            
            # GEOINT (if it's a location-type target)
            if "GEOINT" in domains and target_type in ["country", "region", "event"]:
                task = progress.add_task("[green]Collecting GEOINT...", total=None)
                try:
                    manager = GEOINTManager()
                    manager.search_satellite_metadata(target, days_back=7, cloud_max=80)
                except Exception as e:
                    console.print(f"[yellow]GEOINT collection warning: {e}[/yellow]")
                progress.remove_task(task)
            
            # CYBINT
            if "CYBINT" in domains:
                task = progress.add_task("[red]Collecting CYBINT...", total=None)
                try:
                    manager = CYBINTManager()
                    manager.scan_all(limit_per_feed=limit // 2)
                except Exception as e:
                    console.print(f"[yellow]CYBINT collection warning: {e}[/yellow]")
                progress.remove_task(task)
        
        console.print("[green]✓ Collection complete[/green]")
        time.sleep(1)
    
    # Step 3: Query all relevant intel
    console.print("\n[cyan]Phase 3: Data Aggregation[/cyan]")
    since = now_utc - timedelta(hours=hours)
    
    # Build query for relevant items
    query = db.query(IntelItem).filter(IntelItem.timestamp >= since)
    
    # Filter by target if not a broad topic like "cyber" or "malware"
    if target.lower() not in ["cyber", "malware", "ransomware", "threat", "global"]:
        query = query.filter(
            or_(
                IntelItem.country.ilike(f"%{target}%"),
                IntelItem.summary.ilike(f"%{target}%"),
                IntelItem.raw_text.ilike(f"%{target}%"),
                IntelItem.keyword.ilike(f"%{target}%")
            )
        )
    
    items = query.all()
    
    if not items:
        console.print(Panel(
            f"[red]No intelligence found for '{target}'.[/red]\n"
            f"Try running with --sweep or check if Ollama is running.",
            title="No Data"
        ))
        return
    
    console.print(f"  Found [bold]{len(items)}[/bold] relevant items")
    
    # Organize by category
    intel_data = {
        "OSINT": [x.summary for x in items if x.int_category == "OSINT" and x.summary],
        "SOCMINT": [x.summary for x in items if x.int_category == "SOCMINT" and x.summary],
        "GEOINT": [x.summary for x in items if x.int_category == "GEOINT" and x.summary],
        "SIGNALS": [x.summary for x in items if x.int_category == "COMINT" and x.summary],
        "CYBINT": [x.summary for x in items if x.int_category == "CYBINT" and x.summary]
    }
    
    # Calculate stats
    critical_count = len([x for x in items if x.threat_level == "CRITICAL"])
    threat_scores = [x.threat_score for x in items if x.threat_score]
    avg_score = sum(threat_scores) / len(threat_scores) if threat_scores else 0
    
    stats = {
        "timestamp": now_utc.isoformat(),
        "item_count": len(items),
        "critical_count": critical_count,
        "avg_threat_score": avg_score
    }
    
    # Print category breakdown
    for cat, summaries in intel_data.items():
        status = f"[green]{len(summaries)}[/green]" if summaries else "[dim]0[/dim]"
        console.print(f"  {cat}: {status}")
    
    # Step 4: Generate report with LLM
    console.print("\n[cyan]Phase 4: LLM Synthesis[/cyan]")
    with console.status("[bold]Generating comprehensive assessment (this may take 1-2 minutes)..."):
        report = generate_full_report(target, intel_data, stats)
    
    # Display report
    console.print("\n")
    console.print(Panel(
        report,
        title=f"[bold red]INTEL ASSESSMENT: {target.upper()}[/bold red]",
        subtitle=f"Generated: {now_utc.strftime('%Y-%m-%d %H:%M')} UTC",
        border_style="red",
        padding=(1, 2)
    ))
    
    # Step 5: Export options
    if export_html:
        from pathlib import Path
        export_path = settings.DATA_DIR / f"report_{target.lower().replace(' ', '_')}_{now_utc.strftime('%Y%m%d_%H%M%S')}.html"
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>GEOSCOPE Report: {target}</title>
    <style>
        body {{ font-family: 'Courier New', monospace; background: #0a0a0f; color: #e0e0e0; padding: 40px; }}
        .header {{ color: #dc2626; border-bottom: 2px solid #dc2626; padding-bottom: 20px; }}
        .content {{ white-space: pre-wrap; line-height: 1.6; }}
        .stats {{ background: #1a1a24; padding: 15px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌐 GEOSCOPE INTELLIGENCE ASSESSMENT</h1>
        <h2>TARGET: {target.upper()}</h2>
        <p>Generated: {now_utc.isoformat()}</p>
    </div>
    <div class="stats">
        <strong>Statistics:</strong> {len(items)} items analyzed | {critical_count} critical | Avg Score: {avg_score:.1f}/100
    </div>
    <div class="content">{report}</div>
</body>
</html>"""
        
        with open(export_path, "w") as f:
            f.write(html_content)
        console.print(f"[green]Report exported to: {export_path}[/green]")
    
    # Step 6: Generate map
    if with_map:
        console.print("\n[cyan]Phase 5: Map Generation[/cyan]")
        try:
            from synscope.core.mapper import GeoMapper
            mapper = GeoMapper()
            map_path = mapper.generate_map(country=target, hours=hours, open_browser=True)
        except Exception as e:
            console.print(f"[yellow]Map generation skipped: {e}[/yellow]")
    
    console.print("\n[bold green]✓ Full report complete[/bold green]")


# --- MAP COMMANDS ---
map_app = typer.Typer(help="Generate interactive intelligence maps.", rich_markup_mode="rich")
app.add_typer(map_app, name="map")

@map_app.command("generate")
def map_generate(
    country: str = typer.Option("global", help="Filter by country (or 'global' for all)"),
    hours: int = typer.Option(72, help="Lookback window in hours"),
    no_open: bool = typer.Option(False, help="Don't auto-open browser")
):
    """
    Generate an interactive intelligence map.
    
    [bold]Example:[/bold]
    synscope map generate --country "Ukraine" --hours 48
    """
    from synscope.core.mapper import GeoMapper
    mapper = GeoMapper()
    mapper.generate_map(country=country, hours=hours, open_browser=not no_open)

@map_app.command("heatmap")
def map_heatmap(
    country: str = typer.Option("global", help="Filter by country"),
    hours: int = typer.Option(72, help="Lookback window")
):
    """
    Generate a threat intensity heatmap.
    
    [bold]Example:[/bold]
    synscope map heatmap --country "Russia"
    """
    from synscope.core.mapper import GeoMapper
    mapper = GeoMapper()
    mapper.generate_heatmap(country=country, hours=hours)


# --- STATUS COMMAND ---
@app.command()
def status():
    """
    Show DEFCON status and database statistics.
    """
    from rich.table import Table
    from sqlalchemy import func
    
    print_banner()
    
    db = SessionLocal()
    
    # Get counts by category
    stats = db.query(
        IntelItem.int_category,
        func.count(IntelItem.id)
    ).group_by(IntelItem.int_category).all()
    
    total = sum(s[1] for s in stats)
    
    # Calculate threat metrics
    critical_count = db.query(IntelItem).filter(IntelItem.threat_level == "CRITICAL").count()
    avg_score_result = db.query(func.avg(IntelItem.threat_score)).scalar()
    avg_score = float(avg_score_result) if avg_score_result else 0.0
    
    # Calculate and display DEFCON level
    defcon_level = calculate_defcon(avg_score, critical_count)
    print_defcon_status(defcon_level, {
        "total": total,
        "critical": critical_count,
        "avg_score": avg_score
    })
    
    # Recent items
    recent = db.query(IntelItem).order_by(IntelItem.timestamp.desc()).limit(5).all()
    
    # Display stats table
    if stats:
        table = Table(title="═══ INTELLIGENCE BY DOMAIN ═══", border_style="green", header_style="bold green")
        table.add_column("CATEGORY", style="cyan")
        table.add_column("COUNT", style="green")
        for cat, count in stats:
            table.add_row(cat, str(count))
        console.print(table)
    
    if recent:
        console.print("\\n[bold green]>>> RECENT ACTIVITY[/bold green]")
        for item in recent:
            threat_style = "red" if item.threat_level == "CRITICAL" else "yellow" if item.threat_level == "HIGH" else "dim"
            console.print(f"  [{item.int_category}] {item.summary[:60]}...", style=threat_style)


# --- EXPORT COMMAND ---
@app.command()
def export(
    format: str = typer.Option("json", help="Export format: json or csv"),
    output: str = typer.Option(None, help="Output file path")
):
    """
    Export all intelligence to JSON or CSV.
    
    [bold]Examples:[/bold]
    synscope export --format json
    synscope export --format csv --output intel.csv
    """
    import json
    import csv
    from pathlib import Path
    
    db = SessionLocal()
    items = db.query(IntelItem).all()
    
    if not items:
        console.print("[yellow]No data to export.[/yellow]")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format.lower() == "json":
        output_path = Path(output) if output else settings.DATA_DIR / f"export_{timestamp}.json"
        data = [
            {
                "id": i.id,
                "timestamp": str(i.timestamp),
                "category": i.int_category,
                "keyword": i.keyword,
                "summary": i.summary,
                "country": i.country,
                "threat_level": i.threat_level,
                "threat_score": i.threat_score,
                "source_url": i.source_url,
                "latitude": i.latitude,
                "longitude": i.longitude
            }
            for i in items
        ]
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        console.print(f"[green]Exported {len(items)} items to {output_path}[/green]")
    
    elif format.lower() == "csv":
        output_path = Path(output) if output else settings.DATA_DIR / f"export_{timestamp}.csv"
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "timestamp", "category", "keyword", "summary", "country", 
                           "threat_level", "threat_score", "source_url", "lat", "lon"])
            for i in items:
                writer.writerow([i.id, i.timestamp, i.int_category, i.keyword, i.summary, 
                               i.country, i.threat_level, i.threat_score, i.source_url,
                               i.latitude, i.longitude])
        console.print(f"[green]Exported {len(items)} items to {output_path}[/green]")
    else:
        console.print("[red]Invalid format. Use 'json' or 'csv'.[/red]")


if __name__ == "__main__":
    app()