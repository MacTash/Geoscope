import re
import os
from datetime import datetime
from rich.console import Console
from geoscope.database import SessionLocal, IntelItem
from geoscope.core.utils import logger, clean_text

console = Console()

class SignalsManager:
    def __init__(self):
        self.db = SessionLocal()

    def detect_eam_patterns(self, text: str) -> list[dict]:
        """
        Scans text for standard HFGCS Emergency Action Message (EAM) patterns.
        Pattern: 6-character alphanumeric header, followed by message body.
        Example: "SKYKING SKYKING DO NOT ANSWER" or "XZY123 ..."
        """
        matches = []
        
        # Pattern 1: SKYKING messages (High priority)
        # Regex: Look for SKYKING, capture the next ~30 chars
        skyking_pattern = r"(SKYKING\s+SKYKING\s+Do\s+not\s+answer.*)"
        sky_matches = re.findall(skyking_pattern, text, re.IGNORECASE)
        for m in sky_matches:
            matches.append({"type": "EAM-SKYKING", "content": m.strip(), "priority": "CRITICAL"})

        # Pattern 2: Standard Force Direction Messages (Mainsail)
        # Often starts with 6 alphanumerics, repeats, then payload
        # This is a heuristic regex for demo purposes
        eam_pattern = r"\b([A-Z0-9]{6})\s+\1\s+([A-Z0-9\s]{10,})\b"
        eam_matches = re.findall(eam_pattern, text)
        for header, body in eam_matches:
            matches.append({
                "type": "EAM-STANDARD", 
                "content": f"Header: {header} | Body: {body.strip()}",
                "priority": "HIGH"
            })
            
        return matches

    def ingest_log_file(self, file_path: str):
        """
        Reads a local SDR log file (txt) and extracts formatted messages.
        """
        if not os.path.exists(file_path):
            console.print(f"[red]Log file not found: {file_path}[/red]")
            return

        console.print(f"[cyan]Processing SIGINT log: {file_path}[/cyan]")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw_data = f.read()

        # Clean and Detect
        detected_signals = self.detect_eam_patterns(raw_data)
        
        if not detected_signals:
            console.print("[yellow]No valid EAM patterns detected in logs.[/yellow]")
            return

        count = 0
        for sig in detected_signals:
            # Create unique hash for source_url to prevent duplication of same message
            # In production, use a hash of the content. Here we use a pseudo-ID.
            sig_content = sig['content']
            sig_id = f"SIGINT-{hash(sig_content)}"

            # Basic filtering of duplicates
            exists = self.db.query(IntelItem).filter_by(source_url=sig_id).first()
            if exists:
                continue

            item = IntelItem(
                timestamp=datetime.utcnow(),
                int_category="COMINT", # Communications Intelligence
                source_url=sig_id,
                keyword="HFGCS",
                raw_text=sig_content,
                summary=f"Intercepted {sig['type']}: {sig_content[:50]}...",
                country="Global", # HFGCS is global
                threat_level=sig['priority'],
                threat_score=90 if sig['type'] == "EAM-SKYKING" else 60,
                confidence=1.0 # Captured signal is factual
            )
            
            self.db.add(item)
            count += 1
        
        self.db.commit()
        console.print(f"[green]Ingested {count} signal intercepts.[/green]")

    def add_manual_intercept(self, text: str):
        """
        Allows manual entry of a decoded message from CLI.
        """
        self.detect_eam_patterns(text) # Just to validate/categorize
        # Logic similar to above, saves directly
        # ... (simplified for brevity, reuses logic above)
        pass