from duckduckgo_search import DDGS
from datetime import datetime, timezone
from rich.console import Console
from synscope.database import SessionLocal, IntelItem
from synscope.core.llm import analyze_text
from synscope.core.utils import logger

console = Console()

class SOCMINTManager:
    def __init__(self):
        self.db = SessionLocal()

    def run_social_search(self, keyword: str, limit: int = 50, user: str = None, subreddit: str = None):
        """
        Searches Social Media with optional targeting for specific Users (X) or Subreddits.
        """
        # --- QUERY CONSTRUCTION ---
        if user:
            # Target specific X/Twitter User
            # Example: "tanks site:x.com/OSINTtechnical"
            console.print(f"[cyan]Targeting X User: @{user}[/cyan]")
            query = f"{keyword} (site:twitter.com/{user} OR site:x.com/{user})"
            
        elif subreddit:
            # Target specific Subreddit
            # Example: "frontline site:reddit.com/r/CombatFootage"
            console.print(f"[cyan]Targeting Subreddit: r/{subreddit}[/cyan]")
            query = f"{keyword} site:reddit.com/r/{subreddit}"
            
        else:
            # Broad Search (Default)
            query = f"{keyword} (site:twitter.com OR site:x.com OR site:reddit.com OR site:t.me)"

        console.print(f"[dim]Search Query: {query}[/dim]")
        
        try:
            # backend='html' to avoid rate limits
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    keywords=query, 
                    region="wt-wt", 
                    safesearch="off", 
                    backend="html", 
                    max_results=limit
                ))
        except Exception as e:
            console.print(f"[red]SOCMINT Search failed: {e}[/red]")
            return

        if not results:
            console.print("[yellow]No results found. Try a broader keyword.[/yellow]")
            return

        console.print(f"[cyan]Found {len(results)} results. Ingesting...[/cyan]")
        
        count = 0
        skipped = 0

        for r in results:
            url = r.get('href', '')
            title = r.get('title', '')
            body = r.get('body', '')
            
            # Refined Platform Detection
            platform = "Unknown"
            if "reddit.com" in url: platform = "Reddit"
            elif "t.me" in url: platform = "Telegram"
            elif "twitter.com" in url or "x.com" in url: 
                platform = "X (Twitter)"

            # Check Duplication
            if self.db.query(IntelItem).filter_by(source_url=url).first():
                skipped += 1
                continue
            
            # Analyze
            full_text = f"[{platform}] {title}\n{body}"
            analysis = analyze_text(full_text)
            
            timestamp = datetime.now(timezone.utc).replace(tzinfo=None)

            try:
                item = IntelItem(
                    timestamp=timestamp, 
                    int_category="SOCMINT",
                    source_url=url,
                    keyword=keyword,
                    raw_text=full_text,
                    author=f"@{user}" if user else (f"r/{subreddit}" if subreddit else platform),
                    summary=analysis.get('summary', body),
                    country=analysis.get('country', 'Unknown'),
                    threat_level=analysis.get('threat_level', 'UNKNOWN'),
                    threat_score=analysis.get('threat_score', 0),
                    confidence=analysis.get('confidence', 0.0)
                )
                
                self.db.add(item)
                self.db.commit()
                count += 1
                console.print(f"[green][{count}] {platform}: {title[:50]}...[/green]")
                
            except Exception as e:
                logger.error(f"Error saving SOCMINT item: {e}")
                continue

        console.print(f"[bold]SOCMINT Batch Complete. Ingested: {count} | Skipped: {skipped}[/bold]")