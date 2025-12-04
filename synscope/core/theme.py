"""
Synscope Theme - WarGames DEFCON Style
Inspired by the WOPR terminal from WarGames (1983)
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from datetime import datetime

console = Console()

# DEFCON ASCII Banner
SYNSCOPE_BANNER = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ███████╗██╗   ██╗███╗   ██╗███████╗ ██████╗ ██████╗ ██████╗ ███████╗        ║
║   ██╔════╝╚██╗ ██╔╝████╗  ██║██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝        ║
║   ███████╗ ╚████╔╝ ██╔██╗ ██║███████╗██║     ██║   ██║██████╔╝█████╗          ║
║   ╚════██║  ╚██╔╝  ██║╚██╗██║╚════██║██║     ██║   ██║██╔═══╝ ██╔══╝          ║
║   ███████║   ██║   ██║ ╚████║███████║╚██████╗╚██████╔╝██║     ███████╗        ║
║   ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚══════╝        ║
║                                                                               ║
║                    M U L T I - I N T   F U S I O N   E N G I N E              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

WOPR_GREETING = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                     GREETINGS, PROFESSOR MAYUKH.                              ║
║                                                                               ║
║                     SHALL WE PLAY A GAME?                                     ║
║                                                                               ║
║     > GLOBAL THERMONUCLEAR WAR                                                ║
║     > GEOPOLITICAL ANALYSIS                                                   ║
║     > THREAT INTELLIGENCE FUSION                                              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

# DEFCON Level Definitions
DEFCON_LEVELS = {
    1: {"name": "COCKED PISTOL", "color": "white on red", "desc": "Nuclear war imminent"},
    2: {"name": "FAST PACE", "color": "red", "desc": "Next step to nuclear war"},
    3: {"name": "ROUND HOUSE", "color": "yellow", "desc": "Increase force readiness"},
    4: {"name": "DOUBLE TAKE", "color": "green", "desc": "Above normal readiness"},
    5: {"name": "FADE OUT", "color": "blue", "desc": "Lowest state of readiness"},
}


def calculate_defcon(avg_threat_score: float, critical_count: int) -> int:
    """Calculate DEFCON level based on threat metrics."""
    if critical_count >= 5 or avg_threat_score >= 85:
        return 1
    elif critical_count >= 3 or avg_threat_score >= 70:
        return 2
    elif critical_count >= 1 or avg_threat_score >= 50:
        return 3
    elif avg_threat_score >= 30:
        return 4
    else:
        return 5


def print_banner(show_greeting: bool = False):
    """Print the SYNSCOPE ASCII banner."""
    console.print(SYNSCOPE_BANNER, style="bold green")
    if show_greeting:
        console.print(WOPR_GREETING, style="green")


def print_defcon_status(level: int, stats: dict = None):
    """Display current DEFCON status."""
    defcon = DEFCON_LEVELS[level]
    
    # Create DEFCON indicator
    defcon_text = f"""
╔══════════════════════════════════════╗
║     D E F C O N   L E V E L   {level}      ║
║                                      ║
║     {defcon['name']:^30}     ║
║     {defcon['desc']:^30}     ║
╚══════════════════════════════════════╝
"""
    console.print(defcon_text, style=defcon['color'])
    
    if stats:
        console.print(f"  Intel Items: {stats.get('total', 0)}", style="dim")
        console.print(f"  Critical Alerts: {stats.get('critical', 0)}", style="dim red")
        console.print(f"  Avg Threat Score: {stats.get('avg_score', 0):.1f}", style="dim")


def print_header(title: str, subtitle: str = None):
    """Print a military-style section header."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    header = f"""
╔{'═' * 78}╗
║  {title.upper():<74}  ║
║  {'─' * 74}  ║
║  {subtitle or timestamp:<74}  ║
╚{'═' * 78}╝
"""
    console.print(header, style="green")


def print_intel_item(item: dict, index: int = None):
    """Print a single intel item in WOPR style."""
    prefix = f"[{index:03d}]" if index else ">>>"
    
    console.print(f"  {prefix} [{item.get('category', 'INTEL')}] {item.get('threat_level', 'UNKNOWN')}", style="green")
    console.print(f"        {item.get('summary', 'No summary')[:70]}...", style="dim green")
    if item.get('country'):
        console.print(f"        LOC: {item.get('country')} | TIME: {item.get('timestamp', 'N/A')}", style="dim")
    console.print()


def print_separator():
    """Print a visual separator."""
    console.print("═" * 80, style="green dim")


def print_status_line(label: str, value: str, status: str = "OK"):
    """Print a status line like old terminals."""
    status_style = "green" if status == "OK" else "yellow" if status == "WARN" else "red"
    console.print(f"  [{status:^6}] {label:<30} {value}", style=status_style)


def create_threat_table(items: list) -> Table:
    """Create a DEFCON-style threat table."""
    table = Table(
        title="═══ THREAT MATRIX ═══",
        title_style="bold green",
        border_style="green",
        header_style="bold green",
        show_lines=True
    )
    
    table.add_column("TIME", style="dim green")
    table.add_column("CATEGORY", style="cyan")
    table.add_column("THREAT", style="yellow")
    table.add_column("SUMMARY", style="green")
    table.add_column("LOCATION", style="dim")
    
    for item in items[:15]:
        threat_style = "red bold" if item.get('threat_level') == "CRITICAL" else ""
        table.add_row(
            str(item.get('timestamp', ''))[:16],
            item.get('category', '-'),
            item.get('threat_level', '-'),
            (item.get('summary', '')[:40] + "...") if item.get('summary') else "-",
            item.get('country', '-'),
            style=threat_style
        )
    
    return table
