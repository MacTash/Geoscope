from duckduckgo_search import DDGS
import newspaper
import time
from datetime import datetime, timezone
from rich.console import Console
from synscope.database import SessionLocal, IntelItem
from synscope.core.llm import analyze_text
from synscope.core.utils import logger, clean_text
from synscope.config import settings

console = Console()

class OSINTManager:
    def __init__(self):
        self.db = SessionLocal()

    def bulk_fetch(self, keyword: str, limit: int = 50):
        """
        Fetches news via DuckDuckGo (DDG).
        Implements Rate-Limit handling by switching backends.
        """
        console.print(f"[cyan]Querying DuckDuckGo News for: '{keyword}' (Limit: {limit})...[/cyan]")
        
        results = []
        
        # Attempt 1: Standard News Endpoint
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(keywords=keyword, region="wt-wt", safesearch="off", max_results=limit))
        except Exception as e:
            console.print(f"[yellow]Standard News API Rate Limited ({e}). Switching to HTML backend...[/yellow]")
            time.sleep(2) # Brief pause to cool down
            
            # Attempt 2: Text Search with HTML Backend (Robust)
            try:
                with DDGS() as ddgs:
                    # backend='html' is slower but rarely rate-limited
                    # timelimit='d' ensures we still get recent news (last 24h)
                    results = list(ddgs.text(
                        keywords=f"{keyword} news", 
                        region="wt-wt", 
                        safesearch="off", 
                        timelimit="d", 
                        backend="html", 
                        max_results=limit
                    ))
            except Exception as e2:
                console.print(f"[red]Critical Search Failure: {e2}[/red]")
                return

        if not results:
            console.print("[yellow]No news found. Try a broader keyword.[/yellow]")
            return

        console.print(f"[cyan]Found {len(results)} results. Starting ingestion...[/cyan]")

        count = 0
        skipped = 0
        
        news_config = newspaper.Config()
        news_config.browser_user_agent = settings.USER_AGENT
        news_config.request_timeout = 10

        for r in results:
            # Handle different dictionary keys between 'news' and 'text' search results
            url = r.get('url') or r.get('href')
            title = r.get('title')
            source = r.get('source', 'Web Search')
            
            if not url or self.db.query(IntelItem).filter_by(source_url=url).first():
                skipped += 1
                continue

            try:
                # Extract
                article = newspaper.Article(url, config=news_config)
                article.download()
                article.parse()
                
                raw_body = clean_text(article.text)
                # Fallback if scraping failed
                if len(raw_body) < 100: 
                    raw_body = r.get('body', '')

                # Analyze
                analysis = analyze_text(raw_body[:3000])

                # Force Timestamp to NOW for report visibility
                ingest_time = datetime.now(timezone.utc).replace(tzinfo=None)

                item = IntelItem(
                    timestamp=ingest_time,
                    int_category="OSINT",
                    source_url=url,
                    keyword=keyword,
                    raw_text=f"{title}\n\n{raw_body}",
                    author=str(article.authors) if article.authors else source,
                    summary=analysis.get('summary', 'Analysis Failed'),
                    country=analysis.get('country', 'Unknown'),
                    threat_level=analysis.get('threat_level', 'UNKNOWN'),
                    threat_score=analysis.get('threat_score', 0),
                    confidence=analysis.get('confidence', 0.0)
                )
                
                self.db.add(item)
                self.db.commit()
                count += 1
                console.print(f"[green][{count}/{len(results)}] Ingested: {title[:50]}...[/green]")

            except Exception as e:
                continue
                
        console.print(f"[bold]OSINT Batch Complete. Ingested: {count} | Skipped: {skipped}[/bold]")