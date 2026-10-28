"""
Evidence Collector Module
-------------------------
Collects, cleans, deduplicates, and ranks live external web & news evidence for a given natural-language claim.
Initial search starts from the WHOLE user claim to preserve semantic context.
"""

import os
import re
import html
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import warnings
warnings.filterwarnings('ignore')

try:
    from duckduckgo_search import DDGS
    DDG_AVAILABLE = True
except ImportError:
    DDG_AVAILABLE = False

HIGH_TRUST_DOMAINS = [
    "reuters.com", "apnews.com", "bloomberg.com", "bbc.com", "bbc.co.uk",
    "nytimes.com", "wsj.com", "theguardian.com", "afp.com", "npr.org",
    "washingtonpost.com", "nature.com", "science.org", "wikipedia.org",
    "gov", "edu", "cnn.com", "nbcnews.com", "cbsnews.com", "abcnews.go.com",
    "ft.com", "economist.com", "forbes.com", "time.com"
]

class EvidenceCollector:
    def __init__(self, gemini_client=None):
        self.gemini_client = gemini_client

    def generate_search_queries(self, claim: str) -> list[str]:
        """
        Generate search queries starting from the WHOLE claim,
        followed by semantically equivalent variations.
        """
        clean_claim = claim.strip().rstrip('.!?')
        queries = []

        # 1. Full raw claim (Primary)
        queries.append(clean_claim)

        # 2. Generically derive variation queries without stop words
        stopwords = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'for', 'with', 'about',
            'against', 'between', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off',
            'over', 'under', 'again', 'further', 'then', 'once', 'that', 'this',
            'these', 'those', 'of', 'at', 'by'
        }
        words = re.findall(r'\b[a-zA-Z0-9$%\.\-]+\b', clean_claim)
        keywords = [w for w in words if w.lower() not in stopwords]
        
        if len(keywords) >= 3:
            kw_query = " ".join(keywords)
            if kw_query not in queries:
                queries.append(kw_query)
        
        # 3. Add news-focused query variation if numbers/years/entities present
        if len(keywords) >= 2:
            news_query = f"{' '.join(keywords[:5])} news reporting"
            if news_query not in queries:
                queries.append(news_query)

        # 4. If Gemini client is active, request AI-driven search query variations
        if self.gemini_client:
            try:
                from google.genai import types
                prompt = (
                    f"Given the user claim: '{clean_claim}'\n"
                    "Generate 2 concise news search queries to retrieve fact-checking evidence.\n"
                    "Return ONLY a raw JSON array of strings, e.g. [\"query 1\", \"query 2\"]."
                )
                for m_name in ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]:
                    try:
                        response = self.gemini_client.models.generate_content(
                            model=m_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                temperature=0.1
                            )
                        )
                        import json
                        ai_queries = json.loads(response.text)
                        if isinstance(ai_queries, list):
                            for q in ai_queries:
                                if isinstance(q, str) and q.strip() and q.strip() not in queries:
                                    queries.append(q.strip())
                        break
                    except Exception:
                        continue
            except Exception as e:
                print(f"Notice: AI query generation fallback ({e})")

        return queries[:3]

    def _fetch_google_rss(self, query: str, max_results: int = 8) -> list[dict]:
        """Fetch news results from Google RSS News Feed"""
        sources = []
        try:
            encoded_q = urllib.parse.quote(query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-US&gl=US&ceid=US:en"
            req = urllib.request.Request(
                rss_url,
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                content = resp.read()

            root = ET.fromstring(content)
            for item in root.findall('.//item')[:max_results]:
                title = item.findtext('title', '').strip()
                link = item.findtext('link', '').strip()
                pub_date = item.findtext('pubDate', '').strip()
                source_elem = item.find('source')
                publisher = source_elem.text.strip() if source_elem is not None and source_elem.text else ""

                if not publisher and " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title_clean = parts[0].strip()
                    publisher = parts[1].strip()
                else:
                    title_clean = title

                sources.append({
                    "title": html.unescape(title_clean),
                    "url": link,
                    "publisher": publisher or "Google News",
                    "published_at": pub_date,
                    "snippet": f"Published: {pub_date}. Publisher: {publisher}",
                    "content": "",
                    "source_type": "news"
                })
        except Exception as e:
            print(f"Notice: Google RSS fetch error for '{query}': {e}")
        return sources

    def _fetch_ddg_news(self, query: str, max_results: int = 5) -> list[dict]:
        """Fetch news from DuckDuckGo News if available"""
        sources = []
        if not DDG_AVAILABLE:
            return sources
        try:
            ddgs = DDGS()
            results = list(ddgs.news(query, max_results=max_results))
            for item in results:
                sources.append({
                    "title": item.get('title', ''),
                    "url": item.get('url', ''),
                    "publisher": item.get('source', 'Web Source'),
                    "published_at": item.get('date', ''),
                    "snippet": item.get('body', ''),
                    "content": item.get('body', ''),
                    "source_type": "news"
                })
        except Exception as e:
            print(f"Notice: DDG News fetch error for '{query}': {e}")
        return sources

    def rank_and_deduplicate(self, sources: list[dict], claim: str) -> list[dict]:
        """Deduplicate syndicated copies and rank by domain quality and relevance."""
        seen_titles = set()
        seen_urls = set()
        cleaned_sources = []

        claim_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', claim.lower()))

        for src in sources:
            url = src.get('url', '')
            title = src.get('title', '')
            
            # Simple title normalization for deduplication
            title_norm = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
            if not title_norm or title_norm in seen_titles or url in seen_urls:
                continue

            seen_titles.add(title_norm)
            seen_urls.add(url)

            # Compute quality & relevance score
            quality_score = 0.5
            domain = ""
            try:
                parsed = urllib.parse.urlparse(url)
                domain = parsed.netloc.lower()
            except Exception:
                pass

            if any(h in domain for h in HIGH_TRUST_DOMAINS):
                quality_score += 0.35

            # Relevance boost based on keyword overlap with title/snippet
            text_combined = (title + " " + src.get('snippet', '')).lower()
            overlap_count = sum(1 for w in claim_words if w in text_combined)
            relevance_score = min(1.0, overlap_count / max(1, len(claim_words)))

            total_score = (quality_score * 0.5) + (relevance_score * 0.5)
            src['quality_score'] = round(total_score, 3)

            cleaned_sources.append(src)

        # Sort by quality score descending
        cleaned_sources.sort(key=lambda s: s.get('quality_score', 0), reverse=True)

        # Assign unique source_ids (src_1, src_2, ...)
        for idx, src in enumerate(cleaned_sources, 1):
            src['source_id'] = f"src_{idx}"

        return cleaned_sources

    def collect_evidence(self, claim: str, max_sources: int = 15) -> dict:
        """
        Main evidence collection entrypoint. Parallelized for sub-second retrieval.
        """
        search_queries = self.generate_search_queries(claim)
        raw_sources = []

        from concurrent.futures import ThreadPoolExecutor
        def fetch_worker(query):
            res = self._fetch_google_rss(query, max_results=6)
            if len(res) < 4:
                res.extend(self._fetch_ddg_news(query, max_results=3))
            return res

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(fetch_worker, q) for q in search_queries]
            for f in futures:
                try:
                    raw_sources.extend(f.result(timeout=4.0))
                except Exception:
                    pass

        ranked_sources = self.rank_and_deduplicate(raw_sources, claim)[:max_sources]

        return {
            "claim": claim,
            "search_queries": search_queries,
            "sources": ranked_sources,
            "total_collected": len(ranked_sources)
        }

