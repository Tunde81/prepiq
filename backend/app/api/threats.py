from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
import re

router = APIRouter()

async def fetch_rss(url: str, source: str, limit: int = 5) -> list:
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": "PrepIQ/1.0 ThreatFeed"})
            if r.status_code != 200:
                return []
        root = ET.fromstring(r.text)
        items = []
        ns = {}
        for item in root.findall(".//item")[:limit]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            desc = item.findtext("description", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            # Clean HTML from description
            desc = re.sub(r"<[^>]+>", "", desc)[:200]
            if title:
                items.append({
                    "title": title,
                    "link": link,
                    "description": desc,
                    "published": pub_date,
                    "source": source,
                })
        return items
    except Exception as e:
        print(f"[ThreatFeed] Failed to fetch {source}: {e}")
        return []


async def fetch_cve_feed(limit: int = 5) -> list:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=5&cvssV3Severity=CRITICAL",
                headers={"User-Agent": "PrepIQ/1.0 ThreatFeed"}
            )
            if r.status_code != 200:
                return []
            data = r.json()
            items = []
            for vuln in data.get("vulnerabilities", [])[:limit]:
                cve = vuln.get("cve", {})
                cve_id = cve.get("id", "")
                descriptions = cve.get("descriptions", [])
                desc = next((d["value"] for d in descriptions if d["lang"] == "en"), "")[:200]
                metrics = cve.get("metrics", {})
                score = None
                severity = "CRITICAL"
                cvss_data = metrics.get("cvssMetricV31", metrics.get("cvssMetricV30", []))
                if cvss_data:
                    score = cvss_data[0].get("cvssData", {}).get("baseScore")
                    severity = cvss_data[0].get("cvssData", {}).get("baseSeverity", "CRITICAL")
                published = cve.get("published", "")
                items.append({
                    "title": f"{cve_id} — {desc[:80]}...",
                    "link": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                    "description": desc,
                    "published": published,
                    "source": "NVD/CVE",
                    "severity": severity,
                    "score": score,
                })
            return items
    except Exception as e:
        print(f"[ThreatFeed] CVE fetch failed: {e}")
        return []


@router.get("/feed")
async def get_threat_feed():
    import asyncio
    ncsc, cisa, cves = await asyncio.gather(
        fetch_rss("https://www.ncsc.gov.uk/api/1/services/v1/report-rss-feed.xml", "NCSC"),
        fetch_rss("https://www.cisa.gov/uscert/ncas/alerts.xml", "CISA"),
        fetch_cve_feed(),
    )
    all_items = ncsc + cisa + cves
    return {
        "items": all_items,
        "sources": {
            "ncsc": len(ncsc),
            "cisa": len(cisa),
            "cve": len(cves),
        },
        "fetched_at": datetime.utcnow().isoformat(),
    }
