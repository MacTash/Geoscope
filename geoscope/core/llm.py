import requests
import json
from geoscope.config import settings
from geoscope.core.utils import logger

def analyze_text(text: str):
    """
    Analyzes a single piece of text to extract structured data (JSON).
    """
    url = f"{settings.OLLAMA_HOST}/api/generate"
    
    # Strict JSON instruction
    prompt = (
        "Analyze the text below. Return ONLY a valid JSON object with these keys: "
        "summary (concise string), country (string), threat_level (string: LOW, ELEVATED, HIGH, CRITICAL), "
        "threat_score (int 0-100), confidence (float 0.0-1.0). "
        "No markdown, no explanations.\n\n"
        f"TEXT: {text[:2000]}"
    )
    
    payload = {
        "model": settings.MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json().get('response', '{}')
        return json.loads(result)
    except Exception as e:
        logger.error(f"LLM Analysis Failed: {e}")
        return {
            "summary": "Analysis failed due to model error.",
            "country": "Unknown",
            "threat_level": "UNKNOWN",
            "threat_score": 0,
            "confidence": 0.0
        }

def generate_summary(context: str):
    """
    Generates the final fused SITREP.
    Updated to remove roleplay elements (signatures, next steps).
    """
    url = f"{settings.OLLAMA_HOST}/api/generate"
    
    # NEW PROMPT: Enforces a cold, impersonal report style
    prompt = (
        "You are an automated intelligence fusion engine. "
        "Task: Synthesize the provided data into a strictly factual Intelligence Briefing.\n\n"
        "FORMATTING RULES:\n"
        "1. Start immediately with an Executive Summary.\n"
        "2. Use bullet points for key domains (OSINT, SOCMINT, etc).\n"
        "3. End with a 'Threat Assessment' section.\n\n"
        "NEGATIVE CONSTRAINTS (DO NOT INCLUDE):\n"
        "- DO NOT include 'Next Steps', 'Recommendations', or 'Action Items'.\n"
        "- DO NOT include 'Signing Off', signatures, or placeholders like '[Your Name]'.\n"
        "- DO NOT use conversational filler like 'Here is the report'.\n"
        "- Tone must be cold, objective, and analytical.\n\n"
        f"INTELLIGENCE DATA:\n{context}"
    )
    
    try:
        resp = requests.post(url, json={
            "model": settings.MODEL_NAME, 
            "prompt": prompt, 
            "stream": False,
            "options": {"temperature": 0.1}
        }, timeout=120)
        return resp.json().get('response', 'Generation failed.')
    except Exception as e:
        return f"Error generating brief: {e}"


def generate_full_report(target: str, intel_data: dict, stats: dict):
    """
    Generates a comprehensive military-style intelligence report.
    
    Args:
        target: The topic/country being analyzed
        intel_data: Dict with keys for each INT category containing summaries
        stats: Dict with threat_score, item_count, critical_count, etc.
    
    Returns:
        Formatted report string
    """
    url = f"{settings.OLLAMA_HOST}/api/generate"
    
    # Build context from intel data
    context_parts = []
    for category, items in intel_data.items():
        if items:
            context_parts.append(f"=== {category} INTELLIGENCE ({len(items)} items) ===")
            context_parts.extend(items[:20])  # Limit per category
            context_parts.append("")
    
    context = "\n".join(context_parts)
    
    prompt = f"""You are GEOSCOPE, an automated multi-INT fusion analysis engine with multi-domain analysis capabilities.

TARGET: {target.upper()}
COLLECTION TIMESTAMP: {stats.get('timestamp', 'N/A')}
TOTAL ITEMS ANALYZED: {stats.get('item_count', 0)}
CRITICAL INDICATORS: {stats.get('critical_count', 0)}
AGGREGATE THREAT SCORE: {stats.get('avg_threat_score', 0):.1f}/100

Generate a CLASSIFIED-style intelligence assessment in the following format:

═══════════════════════════════════════════════════════════════
                    INTELLIGENCE ASSESSMENT
                    TARGET: {target.upper()}
═══════════════════════════════════════════════════════════════

1. EXECUTIVE SUMMARY
   - 2-3 sentence overview of the current threat landscape
   - Key takeaway for decision makers

2. THREAT MATRIX
   | Domain   | Activity Level | Confidence |
   |----------|---------------|------------|
   (Fill based on data: OSINT, SOCMINT, GEOINT, SIGNALS, CYBINT)

3. KEY INTELLIGENCE (by domain)
   - OSINT: [key findings]
   - SOCMINT: [key findings]
   - GEOINT: [key findings]
   - SIGNALS: [key findings]  
   - CYBINT: [key findings]

4. THREAT ACTORS & TTPs
   - Identified or suspected actors
   - Tactics, Techniques, Procedures observed

5. INDICATORS OF COMPROMISE (IOCs)
   - Any CVEs, malware hashes, IPs mentioned
   - Actionable technical indicators

6. ASSESSMENT
   - Overall threat level: [LOW/ELEVATED/HIGH/CRITICAL]
   - Trend: [INCREASING/STABLE/DECREASING]
   - Confidence: [LOW/MEDIUM/HIGH]

7. INTELLIGENCE GAPS
   - What data is missing or uncertain

═══════════════════════════════════════════════════════════════
                    END OF ASSESSMENT
═══════════════════════════════════════════════════════════════

CONSTRAINTS:
- Be factual and cite specific data from the intelligence provided.
- If a domain has no data, state "NO COLLECTION".
- Do NOT fabricate or hallucinate information.
- Do NOT include recommendations or action items.
- Maintain cold, analytical military intelligence tone.
- CRITICAL: Do NOT list social media accounts (e.g., @users), reporters, or news outlets as "Threat Actors" or "TTPs". Only list actual hostile entities (e.g., APT groups, military units, malware families).
- CRITICAL: Distinguish between the SOURCE of the intel and the SUBJECT of the intel.
- CRITICAL: Do NOT list x.com accounts as IOCs.
- CRITICAL: Do NOT stray away from the command and the keyword provided.

INTELLIGENCE DATA:
{context[:8000]}"""

    try:
        resp = requests.post(url, json={
            "model": settings.MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 2000
            }
        }, timeout=180)
        return resp.json().get('response', 'Report generation failed.')
    except Exception as e:
        return f"Error generating full report: {e}"


def assess_topic(topic: str):
    """
    Quick LLM assessment of a topic to determine search strategy.
    Returns dict with suggested keywords and domains to search.
    """
    url = f"{settings.OLLAMA_HOST}/api/generate"
    
    prompt = f"""Analyze this intelligence target: "{topic}"

Return a JSON object with:
- "type": "country" | "region" | "actor" | "threat" | "event"
- "keywords": list of 3-5 search terms to gather intelligence
- "domains": list of relevant INT domains ["OSINT", "SOCMINT", "GEOINT", "SIGNALS", "CYBINT"]
- "related_countries": list of countries that may be relevant

Example for "Ukraine conflict":
{{"type": "event", "keywords": ["Ukraine", "Russia", "Donbas", "military"], "domains": ["OSINT", "SOCMINT", "GEOINT"], "related_countries": ["Ukraine", "Russia", "Belarus"]}}

Return ONLY valid JSON, no explanation."""

    try:
        resp = requests.post(url, json={
            "model": settings.MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2}
        }, timeout=60)
        result = resp.json().get('response', '{}')
        return json.loads(result)
    except Exception as e:
        logger.error(f"Topic assessment failed: {e}")
        return {
            "type": "unknown",
            "keywords": [topic],
            "domains": ["OSINT", "CYBINT"],
            "related_countries": []
        }