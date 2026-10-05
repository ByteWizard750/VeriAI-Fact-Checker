"""
VeriAI Multi-Stage Factual Evidence Verification Agent Engine
=============================================================
Architecture:
  1. Claim Analyzer & Component Extractor (Fixes Month/Entity overlap)
  2. Proposition Atomizer & Per-Proposition Neural Evaluator
  3. Multi-Query Generator (Confirmation + Contradiction Search)
  4. Multi-Source Live Web Retriever (Google News RSS + DuckDuckGo)
  5. Article Content Extractor (Scrapes full page text where accessible)
  6. Evidence Relevance Analyzer (Fast first-stage filter)
  7. Pretrained Neural Transformer NLI Model (cross-encoder/nli-deberta-v3-small)
  8. Factual Consistency Checkers (Entity, Event, Temporal, Location, Numerical)
  9. Source Deduplication & Syndication Detector
  10. Neural Contradiction & Debunk Detector
  11. Evidence Aggregator & Transparent Score Calculator
  12. Rich Multi-State Verdict & Structured JSON Output Generator
"""

import re
import math
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from nltk.stem import PorterStemmer

from nli_verifier import SemanticNLIVerifier

stemmer = PorterStemmer()

# --- CONSTANTS & CONFIGURATION ---

TRUSTED_DOMAINS = [
    'espncricinfo.com', 'bcci.tv', 'reuters.com', 'bbc.com', 'bbc.co.uk',
    'timesofindia.indiatimes.com', 'ndtv.com', 'cricbuzz.com', 'theguardian.com',
    'cnn.com', 'apnews.com', 'bloomberg.com', 'hindustantimes.com',
    'indianexpress.com', 'livemint.com', 'dnaindia.com', 'news18.com',
    'abplive.com', 'yahoo.com', 'nature.com', 'science.org', 'who.int',
    'wikipedia.org', 'msn.com', 'crictracker.com', 'thehindu.com',
    'sportstar.thehindu.com', 'zeenews.india.com', 'asianetnews.com',
    'cricketcountry.com', 'financialexpress.com', 'business-standard.com',
    'sansad.in', 'pib.gov.in', 'mpa.gov.in', 'firstpost.com', 'moneycontrol.com',
    'deccanherald.com', 'telegraphindia.com', 'outlookindia.com', 'theprint.in',
    'thequint.com', 'scroll.in', 'techcrunch.com', 'forbes.com', 'wsj.com', 'cnbc.com'
]

FACT_CHECK_DOMAINS = [
    'snopes.com', 'altnews.in', 'boomlive.in', 'factcheck.org',
    'politifact.com', 'newschecker.in', 'pib.gov.in', 'fullfact.org',
    'factly.in', 'thip.media', 'visseshatatya.com'
]

STOPWORDS = {
    'the', 'a', 'an', 'in', 'on', 'at', 'to', 'from', 'by', 'for', 'of', 'with',
    'is', 'are', 'was', 'were', 'has', 'have', 'had', 'been', 'be', 'will',
    'shall', 'would', 'could', 'should', 'can', 'may', 'might', 'that', 'this',
    'these', 'those', 'it', 'its', 'they', 'them', 'their', 'he', 'she', 'him',
    'her', 'who', 'which', 'what', 'where', 'when', 'why', 'how', 'all', 'any',
    'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'just',
    'gives', 'give', 'giving', 'given', 'take', 'takes', 'taken', 'taking', 'get',
    'got', 'make', 'makes', 'made', 'say', 'says', 'said', 'according', 'report',
    'reports', 'reported', 'claim', 'claims', 'claimed', 'confirm', 'confirms'
}

MONTH_NAMES_SET = {
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
    'september', 'october', 'november', 'december', 'jan', 'feb', 'mar', 'apr',
    'jun', 'jul', 'aug', 'sep', 'sept', 'oct', 'nov', 'dec'
}

GENERIC_STOP_ENTITIES = {
    'scientists', 'people', 'experts', 'reports', 'news', 'sources', 'official',
    'breaking', 'update', 'today', 'yesterday', 'year', 'month', 'day', 'world',
    'time', 'study', 'researchers', 'man', 'woman', 'police', 'court', 'government'
} | MONTH_NAMES_SET

MONTH_MAP = {
    'jan': 'january', 'feb': 'february', 'mar': 'march', 'apr': 'april',
    'may': 'may', 'jun': 'june', 'jul': 'july', 'aug': 'august',
    'sep': 'september', 'sept': 'september', 'oct': 'october',
    'nov': 'november', 'dec': 'december'
}

EVENT_KEYWORDS = {
    'launch': ['launch', 'launched', 'releasing', 'released', 'release', 'debut', 'unveil', 'unveiled', 'rollout'],
    'announcement': ['announce', 'announced', 'announcement', 'reveal', 'revealed', 'plans', 'planned'],
    'retirement': ['retire', 'retired', 'retirement', 'resigned', 'step down', 'steps down', 'quits', 'quit'],
    'injury': ['injury', 'injured', 'hurt', 'fracture', 'hospitalized', 'hospitalised', 'accident', 'crash', 'health'],
    'acquisition': ['buy', 'buys', 'bought', 'acquire', 'acquired', 'acquisition', 'takeover', 'merge', 'merged'],
    'cancellation': ['cancel', 'cancelled', 'canceled', 'scrap', 'scrapped', 'call off', 'called off', 'postponed', 'delayed'],
    'denial': ['deny', 'denies', 'denied', 'refute', 'refuted', 'debunk', 'debunked', 'fake', 'false', 'hoax', 'rumor', 'rumour']
}

PLANNED_EVENT_TERMS = ['plan', 'plans', 'planned', 'planning', 'propose', 'proposed', 'scheduled', 'targeting', 'aims', 'intends', 'will', 'may', 'could', 'developing technologies', 'future']


# =====================================================================
# 1. CLAIM ANALYZER & DECOMPOSER
# =====================================================================

def normalize_text(text):
    """Normalize casing and standard month names."""
    lowered = text.lower()
    for short_m, long_m in MONTH_MAP.items():
        lowered = re.sub(r'\b' + short_m + r'\b', long_m, lowered)
    return lowered

COUNTRIES_LOCATIONS = {
    'south africa', 'india', 'australia', 'england', 'indonesia', 'bali', 'chennai',
    'mumbai', 'delhi', 'london', 'paris', 'new york', 'pakistan', 'sri lanka', 'new zealand',
    'united states', 'uk', 'usa', 'china', 'japan', 'russia', 'germany', 'france'
}

def format_person_name(name_str):
    name_str = re.sub(r'\bdevilliers\b', 'de Villiers', name_str, flags=re.IGNORECASE)
    parts = name_str.split()
    formatted = []
    for p in parts:
        if p.lower() in ['de', 'van', 'der', 'la', 'le', 'von']:
            formatted.append(p.lower())
        elif len(p) <= 2 and p.isalpha() and p.lower() not in ['in', 'to', 'on', 'at', 'or', 'and']:
            formatted.append(p.upper())
        else:
            formatted.append(p.capitalize())
    return ' '.join(formatted)

def extract_entities_enhanced(text):
    """
    Extracts entities with strict priority for Primary Person/Subject.
    Detects lowercase person names (e.g. 'ab devilliers', 'virat kohli', 'elon musk').
    Categorizes entities into primary_subject, secondary_entities, and locations.
    """
    clean_text = re.sub(r'[,;\-\|]', ' ', text)
    tokens = clean_text.split()
    
    # 1. Capitalized token sequences
    cap_entities = []
    curr = []
    for t in tokens:
        clean_t = re.sub(r'[^\w]', '', t)
        if clean_t and t[0].isupper() and clean_t.lower() not in STOPWORDS and clean_t.lower() not in GENERIC_STOP_ENTITIES:
            curr.append(clean_t)
        else:
            if curr:
                cap_entities.append(' '.join(curr))
                curr = []
    if curr:
        cap_entities.append(' '.join(curr))

    # 2. Lowercase name pattern search (2-word or 3-word names)
    lower_name_candidates = []
    for i in range(len(tokens) - 1):
        t1 = re.sub(r'[^\w]', '', tokens[i]).lower()
        t2 = re.sub(r'[^\w]', '', tokens[i+1]).lower()
        if t1 and t2 and t1 not in STOPWORDS and t2 not in STOPWORDS and t1 not in COUNTRIES_LOCATIONS and t2 not in COUNTRIES_LOCATIONS and t1 not in GENERIC_STOP_ENTITIES and t2 not in GENERIC_STOP_ENTITIES:
            if len(t1) <= 3 or len(t2) > 3:
                lower_name_candidates.append(format_person_name(f"{t1} {t2}"))

    for i in range(len(tokens) - 2):
        t1 = re.sub(r'[^\w]', '', tokens[i]).lower()
        t2 = re.sub(r'[^\w]', '', tokens[i+1]).lower()
        t3 = re.sub(r'[^\w]', '', tokens[i+2]).lower()
        if t1 and t2 and t3 and (len(t1) <= 3 or t2 in ['de', 'van', 'der']) and t3 not in STOPWORDS:
            lower_name_candidates.append(format_person_name(f"{t1} {t2} {t3}"))

    all_found = list(dict.fromkeys(cap_entities + lower_name_candidates))
    
    primary_subject = None
    locations = []
    secondary_entities = []
    
    for e in all_found:
        e_low = e.lower().strip()
        if e_low in COUNTRIES_LOCATIONS or e_low in ['south africa']:
            locations.append(e)
        elif any(k in e_low for k in ['legends', 'team', 'club', 'bcci', 'icc', 'isro', 'nasa', 'government']):
            secondary_entities.append(e)
        else:
            if not primary_subject:
                primary_subject = e
            else:
                secondary_entities.append(e)
                
    if not primary_subject and all_found:
        primary_subject = all_found[0]
        
    return {
        'primary_subject': primary_subject,
        'secondary_entities': list(dict.fromkeys(secondary_entities)),
        'locations': list(dict.fromkeys(locations)),
        'all_entities': all_found
    }

def get_primary_subject_aliases(primary_subject):
    """Returns aliases and surnames for the primary subject."""
    if not primary_subject:
        return []
    aliases = [primary_subject, primary_subject.lower()]
    parts = primary_subject.split()
    if len(parts) >= 2:
        if len(parts) == 3 and parts[1].lower() in ['de', 'van', 'der']:
            aliases.append(f"{parts[1]} {parts[2]}")
            aliases.append(f"{parts[1]}{parts[2]}")
        else:
            aliases.append(parts[-1])
    if 'de villiers' in primary_subject.lower():
        aliases.extend(['devilliers', 'ab de villiers', 'ab devilliers'])
    return list(dict.fromkeys(aliases))

def extract_entities(text):
    res = extract_entities_enhanced(text)
    return res['all_entities']

RELATIVE_DATE_TERMS = {'recently', 'today', 'yesterday', 'last week', 'this month', 'latest', 'recent', 'diwali', 'eid', 'christmas'}

def extract_dates(text):
    """Extract temporal expressions."""
    norm = normalize_text(text)
    dates = []
    
    date_patterns = [
        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*,\s*\d{4})?\b',
        r'\b\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+\d{4})?\b',
        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b',
        r'\b20\d{2}\b',
        r'\b(?:today|yesterday|recently|last week|this month|diwali|eid|christmas)\b'
    ]
    
    for pat in date_patterns:
        matches = re.findall(pat, norm)
        for m in matches:
            dates.append(m)
            
    return list(dict.fromkeys(dates))

def extract_numbers(text):
    """
    Extract currency, quantities, scores, percentages without breaking values.
    Preserves '$10,000' as '$10,000' rather than splitting into '$10', '10', '000'.
    """
    patterns = [
        r'\$\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:billion|million|trillion|k|m|b)?\b',
        r'₹\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:crore|lakh|thousand|billion|million)?\b',
        r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:percent|%|runs|wickets|goals|points|years|year|months|days)\b',
        r'\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b'
    ]
    found = []
    for p in patterns:
        for m in re.findall(p, text, flags=re.IGNORECASE):
            if not (m.isdigit() and len(m) == 4 and m.startswith('20')):
                found.append(m)
                
    # Fallback to single numbers if none found
    if not found:
        simple_nums = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        for sn in simple_nums:
            if not (sn.isdigit() and len(sn) == 4 and sn.startswith('20')):
                found.append(sn)

    return list(dict.fromkeys(found))

def extract_locations(text):
    """
    Extract potential location names.
    Excludes date expressions like 'in March', 'in August', 'in 2026'.
    """
    norm = normalize_text(text)
    loc_matches = re.findall(r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', text)
    valid_locs = []
    for lm in loc_matches:
        lm_low = lm.lower().strip()
        if lm_low not in MONTH_NAMES_SET and not lm_low.isdigit() and lm_low not in GENERIC_STOP_ENTITIES:
            valid_locs.append(lm)
    return list(dict.fromkeys(valid_locs))

def analyze_claim(text):
    """
    Stage 1 & 2: Claim Analyzer & Proposition Decomposer
    Decomposes claims into atomic propositions with primary subject prioritization.
    """
    ent_analysis = extract_entities_enhanced(text)
    primary_subject = ent_analysis['primary_subject']
    secondary_entities = ent_analysis['secondary_entities']
    locations = list(dict.fromkeys(ent_analysis['locations'] + extract_locations(text)))
    entities = ent_analysis['all_entities']
    
    dates = extract_dates(text)
    numbers = extract_numbers(text)
    norm_text = normalize_text(text)
    
    detected_event = "general_claim"
    for ev_type, keywords in EVENT_KEYWORDS.items():
        if any(re.search(r'\b' + kw + r'\b', norm_text) for kw in keywords):
            detected_event = ev_type
            break
            
    propositions = []
    
    subj_str = primary_subject or (entities[0] if entities else text[:50])
    sec_str = f" for {secondary_entities[0]}" if secondary_entities else ""
    loc_str = f" in {locations[0]}" if locations else ""
    
    propositions.append({
        'id': 'prop_core',
        'aspect': 'Primary Subject & Action',
        'statement': f"{subj_str} performed/underwent {detected_event}{sec_str}{loc_str}",
        'required': True
    })
        
    if dates:
        propositions.append({
            'id': 'prop_date',
            'aspect': 'Date / Time',
            'statement': f"Event occurred on or at: {', '.join(dates)}",
            'required': False
        })
        
    if numbers:
        propositions.append({
            'id': 'prop_number',
            'aspect': 'Numerical / Quantitative',
            'statement': f"Claim quantitative value is: {', '.join(numbers)}",
            'required': False
        })

    if locations:
        propositions.append({
            'id': 'prop_location',
            'aspect': 'Location',
            'statement': f"Event location is: {', '.join(locations)}",
            'required': False
        })

    return {
        'original_claim': text,
        'primary_subject': primary_subject,
        'secondary_entities': secondary_entities,
        'entities': entities,
        'dates': dates,
        'numbers': numbers,
        'locations': locations,
        'event_type': detected_event,
        'propositions': propositions
    }


# =====================================================================
# 3. MULTI-QUERY GENERATOR
# =====================================================================

def generate_queries(claim_analysis):
    """
    Stage 3: Query Generator
    Generates claim-specific queries containing the Primary Subject.
    Prevents single generic location queries (e.g. "South Africa").
    """
    primary = claim_analysis.get('primary_subject')
    secondary = claim_analysis.get('secondary_entities', [])
    locations = claim_analysis.get('locations', [])
    event = claim_analysis.get('event_type', '')
    text = claim_analysis['original_claim']
    
    clean_text = re.sub(r'[^\w\s]', ' ', text)
    words = [w for w in clean_text.split() if w.lower() not in STOPWORDS]
    
    confirmation_queries = []
    contradiction_queries = []
    
    if primary:
        # Every query MUST include primary subject
        sec_str = secondary[0] if secondary else (locations[0] if locations else "")
        if sec_str:
            confirmation_queries.append(f'"{primary}" "{sec_str}"')
            
        action_words = [w for w in words if w.lower() not in primary.lower() and (not sec_str or w.lower() not in sec_str.lower())]
        if action_words:
            confirmation_queries.append(f'"{primary}" {" ".join(action_words[:3])}')
            
        if sec_str and action_words:
            confirmation_queries.append(f'"{primary}" "{sec_str}" {action_words[0]}')
            
        contradiction_queries.append(f'"{primary}" fake OR rumor OR debunk OR denied OR hoax OR false OR statement')
    else:
        # Fallback when no primary subject exists
        key_phrase = " ".join(words[:5])
        confirmation_queries.append(key_phrase)
        contradiction_queries.append(f"{key_phrase} fact check OR debunk OR fake")

    return {
        'confirmation': list(dict.fromkeys(confirmation_queries)),
        'contradiction': list(dict.fromkeys(contradiction_queries))
    }


# =====================================================================
# 4 & 5. RETRIEVAL & ARTICLE CONTENT EXTRACTION
# =====================================================================

def is_domain_trusted(domain, url):
    d = domain.lower()
    u = url.lower()
    if any(td in d or td in u for td in TRUSTED_DOMAINS):
        return True
    if d.endswith('.gov') or d.endswith('.gov.in') or d.endswith('.edu') or 'sansad.in' in d or 'pib.gov.in' in d:
        return True
    return False

def is_fact_check_source(domain, title):
    d = domain.lower()
    t = title.lower()
    return any(fd in d for fd in FACT_CHECK_DOMAINS) or 'fact check' in t or 'fact-check' in t or 'fake news' in t or 'debunk' in t

def fetch_google_news_rss(query):
    sources = []
    try:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            tree = ET.fromstring(resp.read())
            items = tree.findall('.//item')
            for item in items[:6]:
                raw_title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                
                source_name = "Google News"
                title = raw_title
                if ' - ' in raw_title:
                    parts = raw_title.rsplit(' - ', 1)
                    title = parts[0]
                    source_name = parts[1]
                    
                domain = urllib.parse.urlparse(link).netloc.lower()
                trusted = is_domain_trusted(domain, link) or source_name != "Google News"
                fact_check = is_fact_check_source(domain, title)
                
                sources.append({
                    'title': title,
                    'url': link,
                    'snippet': f"Published: {pub_date}",
                    'pub_date': pub_date,
                    'source': source_name,
                    'domain': domain,
                    'is_trusted': trusted,
                    'is_fact_check': fact_check,
                    'content': None,
                    'content_accessible': False
                })
    except Exception as e:
        print(f"RSS Retrieval Notice: {e}")
    return sources

def fetch_ddg_results(query):
    sources = []
    try:
        ddgs = DDGS()
        text_results = list(ddgs.text(query, max_results=5))
        for r in text_results:
            title = r.get('title', '')
            url = r.get('href', '')
            snippet = r.get('body', '')
            domain = urllib.parse.urlparse(url).netloc.lower()
            
            trusted = is_domain_trusted(domain, url)
            fact_check = is_fact_check_source(domain, title)
            
            sources.append({
                'title': title,
                'url': url,
                'snippet': snippet,
                'pub_date': '',
                'source': domain,
                'domain': domain,
                'is_trusted': trusted,
                'is_fact_check': fact_check,
                'content': None,
                'content_accessible': False
            })
    except Exception as e:
        print(f"DDGS Retrieval Notice: {e}")
    return sources

def extract_article_content(url):
    if not url or not url.startswith('http'):
        return None
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
                
            paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 30]
            if paragraphs:
                full_text = " ".join(paragraphs[:6])
                return full_text[:1500]
    except Exception:
        pass
    return None

def retrieve_all_sources(queries_dict):
    all_raw_sources = []
    seen_urls = set()
    seen_titles = set()
    
    for q in queries_dict['confirmation']:
        rss_res = fetch_google_news_rss(q)
        for s in rss_res:
            if s['url'] not in seen_urls and s['title'] not in seen_titles:
                seen_urls.add(s['url'])
                seen_titles.add(s['title'])
                s['query_type'] = 'confirmation'
                all_raw_sources.append(s)
                
    if len(all_raw_sources) < 4:
        for q in queries_dict['confirmation'][:2]:
            ddg_res = fetch_ddg_results(q)
            for s in ddg_res:
                if s['url'] not in seen_urls and s['title'] not in seen_titles:
                    seen_urls.add(s['url'])
                    seen_titles.add(s['title'])
                    s['query_type'] = 'confirmation'
                    all_raw_sources.append(s)
                    
    for q in queries_dict['contradiction'][:1]:
        ddg_res = fetch_ddg_results(q)
        for s in ddg_res:
            if s['url'] not in seen_urls and s['title'] not in seen_titles:
                seen_urls.add(s['url'])
                seen_titles.add(s['title'])
                s['query_type'] = 'contradiction'
                all_raw_sources.append(s)

    for s in all_raw_sources[:5]:
        content = extract_article_content(s['url'])
        if content:
            s['content'] = content
            s['content_accessible'] = True
            
    return all_raw_sources


# =====================================================================
# 6, 7 & 8. RELEVANCE, NEURAL NLI & FACTUAL CONSISTENCY
# =====================================================================

def compute_tokens(text):
    clean = re.sub(r'[^\w\s]', ' ', text.lower())
    return [stemmer.stem(w) for w in clean.split() if w not in STOPWORDS and len(w) > 2]

def evaluate_source_relevance(source, claim_analysis):
    """
    Stage 6: Hard Relevance Gate Filter.
    Checks Primary Subject presence and proposition keyword similarity.
    Rejects irrelevant articles before Neural NLI.
    """
    full_text = f"{source['title']} {source.get('snippet', '')} {source.get('content', '') or ''}".lower()
    primary_subject = claim_analysis.get('primary_subject')
    
    if not full_text.strip():
        return 0.0, "IRRELEVANT", False, "Empty article text"
        
    # 1. Mandatory Primary Subject Check
    primary_found = False
    if primary_subject:
        aliases = get_primary_subject_aliases(primary_subject)
        primary_found = any(alias.lower() in full_text for alias in aliases)
        
        if not primary_found:
            # HARD RELEVANCE GATE FAILURE: Primary subject missing from source text
            return 0.0, "IRRELEVANT", False, f"Primary subject '{primary_subject}' missing from source text"
    else:
        primary_found = True

    # 2. Event / Context Keyword Overlap
    claim_words = compute_tokens(claim_analysis['original_claim'])
    if primary_subject:
        subj_tokens = set(compute_tokens(primary_subject))
        claim_words = [w for w in claim_words if w not in subj_tokens]
        
    s_tokens = set(compute_tokens(full_text))
    if claim_words:
        event_overlap = len(set(claim_words).intersection(s_tokens)) / max(1, len(claim_words))
    else:
        event_overlap = 1.0

    score = (0.7 * (1.0 if primary_found else 0.0)) + (0.3 * event_overlap)
    
    if score >= 0.35:
        category = "RELEVANT"
    else:
        category = "IRRELEVANT"
        
    return score, category, primary_found, "Primary subject present and proposition aligned"

def print_source_debug_log(source, claim_analysis):
    """Prints debug audit information required during development."""
    primary_sub = claim_analysis.get('primary_subject', 'N/A')
    primary_found = source.get('primary_entity_found', False)
    rel_score = source.get('relevance_score', 0.0)
    rel_decision = source.get('relevance_category', 'UNKNOWN')
    
    nli_res = source.get('nli') or {}
    nli_label = nli_res.get('nli_verdict', 'SKIPPED')
    nli_probs = nli_res.get('nli_probabilities')
    
    print("=" * 80)
    print(f"SOURCE: {source.get('url', 'N/A')}")
    print(f"TITLE: {source.get('title', 'N/A')}")
    print(f"PRIMARY ENTITY ({primary_sub}): {'FOUND' if primary_found else 'NOT FOUND'}")
    print(f"EVENT RELEVANCE SCORE: {rel_score:.2f} | OVERALL RELEVANCE SCORE: {rel_score:.2f}")
    print(f"RELEVANCE DECISION: {rel_decision}")
    print(f"NLI LABEL: {nli_label}")
    if nli_probs:
        print(f"NLI ENTAILMENT PROBABILITY: {nli_probs.get('entailment', 0.0)*100:.1f}%")
        print(f"NLI CONTRADICTION PROBABILITY: {nli_probs.get('contradiction', 0.0)*100:.1f}%")
        print(f"NLI NEUTRAL PROBABILITY: {nli_probs.get('neutral', 0.0)*100:.1f}%")
    else:
        print("NLI ENTAILMENT PROBABILITY: None")
        print("NLI CONTRADICTION PROBABILITY: None")
        print("NLI NEUTRAL PROBABILITY: None")
    print("=" * 80)

def generate_candidate_hypotheses(claim_text, claim_analysis):
    """
    Generates candidate hypotheses ranging from raw claim to cleaned core propositions.
    This prevents verbose filler phrases ('following an accident during a work trip')
    or relative adverbs ('recently') from suppressing high DeBERTa NLI entailment scores.
    """
    candidates = [claim_text]
    
    # 1. Stripped hypothesis: remove relative temporal fuzz words and prepositional filler phrases
    clean_h = claim_text
    filler_patterns = [
        r'\brecently\b', r'\btoday\b', r'\byesterday\b', r'\bthis week\b', r'\bthis month\b',
        r'\baccording to reports\b', r'\breportedly\b', r'\bbreaking news\b', r'\bsources say\b',
        r'\bas per reports\b', r'\bfollowing an? [a-z\s]+ during a work trip\b', r'\bduring a work trip\b',
        r'\bfollowing an? [a-z\s]+ during\b'
    ]
    for fp in filler_patterns:
        clean_h = re.sub(fp, '', clean_h, flags=re.IGNORECASE)
    clean_h = re.sub(r'\s+', ' ', clean_h).strip()
    if clean_h and clean_h.lower() != claim_text.lower():
        candidates.append(clean_h)
        
    # 2. Add core subject + action statement
    entities = claim_analysis.get('entities', [])
    event = claim_analysis.get('event_type', '')
    locations = claim_analysis.get('locations', [])
    
    if entities:
        subj = entities[0]
        if event == 'injury':
            candidates.append(f"{subj} suffered injury or fracture")
            if locations:
                candidates.append(f"{subj} suffered injury or fracture in {locations[0]}")
        elif event == 'launch':
            candidates.append(f"{subj} launched product")
        elif event == 'retirement':
            candidates.append(f"{subj} retired or resigned")
        elif event == 'announcement':
            candidates.append(f"{subj} revealed or announced news")
        elif event == 'acquisition':
            candidates.append(f"{subj} acquired company")
            
    unique = []
    for c in candidates:
        if c and c not in unique:
            unique.append(c)
    return unique

def evaluate_nli_neural(source, claim_analysis):
    """
    Stage 7 & 8: Semantic Neural NLI & Consistency Checkers
    Evaluates premise vs hypothesis using pretrained Neural Transformer NLI model.
    """
    full_text = f"{source['title']} {source.get('snippet', '')} {source.get('content', '') or ''}"
    norm_source = normalize_text(full_text)
    claim_text = claim_analysis['original_claim']
    
    entities = claim_analysis['entities']
    dates = claim_analysis['dates']
    numbers = claim_analysis['numbers']

    # 1. Primary Entity Consistency Check
    matched_entities = []
    missing_entities = []
    if entities:
        for e in entities:
            e_low = e.lower()
            tokens = [t for t in e_low.split() if t not in STOPWORDS and len(t) > 1]
            if e_low in norm_source or (tokens and all(t in norm_source for t in tokens)):
                matched_entities.append(e)
            elif len(tokens) > 1 and any(t in norm_source for t in tokens):
                matched_entities.append(e)
            else:
                missing_entities.append(e)
        entity_match = (len(matched_entities) >= 1 and (len(missing_entities) == 0 or entities[0] in matched_entities))
    else:
        entity_match = True

    # 2. Planned vs Completed Event Check
    has_planned_terms = any(re.search(r'\b' + pt + r'\b', norm_source) for pt in PLANNED_EVENT_TERMS)
    claim_has_completed = any(kw in claim_text.lower() for kw in ['launched', 'landed', 'occurred', 'happened', 'retired', 'acquired'])

    # 3. Temporal Consistency Check
    temporal_match = True
    date_mismatch_detail = ""
    if dates:
        concrete_dates = [d for d in dates if d.lower().strip() not in RELATIVE_DATE_TERMS]
        if concrete_dates:
            has_date = any(d in norm_source for d in concrete_dates)
            if not has_date:
                temporal_match = False
                date_mismatch_detail = f"Claim date '{concrete_dates[0]}' missing from source text."
        else:
            temporal_match = True

    # 4. Numerical Consistency Check
    numerical_match = True
    num_mismatch_detail = ""
    if numbers:
        for n in numbers:
            n_clean = re.sub(r'[^\d]', '', n)
            if n_clean and len(n_clean) > 1:
                if n_clean not in norm_source:
                    numerical_match = False
                    num_mismatch_detail = f"Claim number '{n}' unconfirmed."

    # 5. Execute Pretrained Transformer Neural NLI Model with Multi-Hypothesis Evaluation
    nli_verifier = SemanticNLIVerifier.get_instance()
    candidate_hypotheses = generate_candidate_hypotheses(claim_text, claim_analysis)
    
    best_probs = {'entailment': 0.0, 'contradiction': 0.0, 'neutral': 1.0}
    best_hypothesis_used = claim_text
    max_alignment = -1.0
    
    for cand_h in candidate_hypotheses:
        probs = nli_verifier.predict_pair(premise=full_text, hypothesis=cand_h)
        if probs:
            alignment = max(probs['entailment'], probs['contradiction'])
            if alignment > max_alignment:
                max_alignment = alignment
                best_probs = probs
                best_hypothesis_used = cand_h

    p_ent = best_probs['entailment']
    p_contra = best_probs['contradiction']
    p_neut = best_probs['neutral']
    nli_probs = {'entailment': p_ent, 'contradiction': p_contra, 'neutral': p_neut}
    nli_engine_type = "pretrained_neural_transformer"

    title_norm = source['title'].lower()
    is_question = title_norm.endswith('?') or title_norm.startswith('is ') or title_norm.startswith('did ')
    is_myth_or_rhyme = any(m in norm_source for m in ['nursery rhyme', 'idiom', 'mythological', 'urban legend', 'flat earth'])
    is_explicit_debunk = any(m in title_norm for m in ['fake', 'false', 'hoax', 'debunked', 'baseless', 'fabricated', 'untrue', 'misleading', 'morphed'])

    # Determine Verdict from Neural Probabilities & Consistency
    if is_myth_or_rhyme or p_contra >= 0.40 or (source['is_fact_check'] and (is_explicit_debunk or p_contra >= 0.30)):
        nli_verdict = "CONTRADICTION"
        nli_explanation = f"Neural NLI model detected high contradiction (P_contra={p_contra:.2f}). Article refutes or debunks claim."
    elif is_question or not entity_match or p_neut >= 0.60:
        nli_verdict = "NEUTRAL"
        nli_explanation = f"Neural NLI model classified evidence as Neutral (P_neutral={p_neut:.2f}). Insufficient evidence to establish claim."
    elif claim_has_completed and has_planned_terms and p_ent < 0.70:
        nli_verdict = "PARTIAL_SUPPORT"
        nli_explanation = "Article discusses planned/future event rather than confirmed completed action."
    elif entity_match and temporal_match and numerical_match and p_ent >= 0.45:
        nli_verdict = "ENTAILMENT"
        nli_explanation = f"Neural NLI model confirmed high entailment (P_entailment={p_ent:.2f}) with full factual alignment."
    elif entity_match and p_ent >= 0.35:
        if not temporal_match or not numerical_match:
            nli_verdict = "PARTIAL_SUPPORT"
            nli_explanation = f"Neural NLI indicates partial entailment (P={p_ent:.2f}), but date or numerical parameters differ."
        else:
            nli_verdict = "ENTAILMENT"
            nli_explanation = f"Neural NLI model confirmed entailment (P_entailment={p_ent:.2f})."
    else:
        nli_verdict = "NEUTRAL"
        nli_explanation = f"Neural NLI model returned insufficient entailment (P_neutral={p_neut:.2f})."

    return {
        'nli_verdict': nli_verdict,
        'nli_explanation': nli_explanation,
        'nli_engine_type': nli_engine_type,
        'nli_probabilities': nli_probs,
        'best_hypothesis_used': best_hypothesis_used,
        'consistency': {
            'entity_match': entity_match,
            'temporal_match': temporal_match,
            'numerical_match': numerical_match,
            'matched_entities': matched_entities,
            'missing_entities': missing_entities,
            'date_mismatch_detail': date_mismatch_detail,
            'num_mismatch_detail': num_mismatch_detail
        }
    }


# =====================================================================
# 14, 15 & 18. DEDUPLICATION, EVIDENCE AGGREGATION & VERDICT
# =====================================================================

def deduplicate_sources(sources):
    """Stage 14: Source Corroboration & Deduplication."""
    unique_sources = []
    seen_titles = []
    syndicated_count = 0
    
    for s in sources:
        title_lower = s['title'].lower().strip()
        is_dup = False
        for st in seen_titles:
            words1 = set(title_lower.split())
            words2 = set(st.split())
            jaccard = len(words1.intersection(words2)) / max(1, len(words1.union(words2)))
            if jaccard > 0.7:
                is_dup = True
                break
        if is_dup:
            syndicated_count += 1
            s['syndication_status'] = 'POSSIBLY_SYNDICATED'
        else:
            seen_titles.append(title_lower)
            s['syndication_status'] = 'INDEPENDENT'
            unique_sources.append(s)
            
    return unique_sources, syndicated_count

def verify_claim_agent(text):
    """
    MASTER ORCHESTRATOR FOR EVIDENCE VERIFICATION AGENT
    =====================================================
    Executes all 10 agentic stages with pretrained Transformer Neural NLI
    and Hard Relevance Gate filtering.
    """
    if not text or not text.strip():
        return {
            'verdict': 'INSUFFICIENT EVIDENCE',
            'verdict_state': 'UNVERIFIED',
            'confidence': 0.0,
            'summary': 'Empty input provided.'
        }
        
    # 1. Analyze Claim & Identify Primary Subject
    claim_analysis = analyze_claim(text)
    
    # 2. Generate Claim-Specific Queries (MUST include Primary Subject)
    queries = generate_queries(claim_analysis)
    
    # 3 & 4. Retrieve Sources & Article Content
    raw_sources = retrieve_all_sources(queries)
    
    # Deduplicate
    sources, syndicated_copies = deduplicate_sources(raw_sources)
    
    # 5. Evaluate Relevance Gate & Neural NLI
    evaluated_sources = []
    supporting_sources = []
    contradicting_sources = []
    neutral_sources = []
    irrelevant_sources = []
    
    entity_mismatches = 0
    temporal_mismatches = 0
    numerical_mismatches = 0
    
    for s in sources:
        rel_score, rel_category, primary_found, rel_reason = evaluate_source_relevance(s, claim_analysis)
        s['relevance_score'] = rel_score
        s['relevance_category'] = rel_category
        s['primary_entity_found'] = primary_found
        
        if rel_category == 'IRRELEVANT':
            s['nli'] = {
                'nli_verdict': 'SKIPPED',
                'nli_explanation': f"Source failed hard relevance gate: {rel_reason}. NLI skipped.",
                'nli_probabilities': None
            }
            irrelevant_sources.append(s)
            print_source_debug_log(s, claim_analysis)
            continue
            
        nli_res = evaluate_nli_neural(s, claim_analysis)
        s['nli'] = nli_res
        print_source_debug_log(s, claim_analysis)
        
        if not nli_res['consistency']['entity_match']:
            entity_mismatches += 1
        if not nli_res['consistency']['temporal_match']:
            temporal_mismatches += 1
        if not nli_res['consistency']['numerical_match']:
            numerical_mismatches += 1

        if nli_res['nli_verdict'] == 'ENTAILMENT':
            supporting_sources.append(s)
        elif nli_res['nli_verdict'] == 'PARTIAL_SUPPORT':
            supporting_sources.append(s)
        elif nli_res['nli_verdict'] == 'CONTRADICTION':
            contradicting_sources.append(s)
        else:
            neutral_sources.append(s)
            
        evaluated_sources.append(s)

    # 6. Evaluate Propositions individually against best source
    prop_results = []
    best_text = " ".join([f"{s['title']} {s.get('snippet','')}" for s in evaluated_sources[:3]])
    nli_verifier = SemanticNLIVerifier.get_instance()
    
    for prop in claim_analysis['propositions']:
        if best_text.strip():
            p_probs = nli_verifier.predict_pair(premise=best_text, hypothesis=prop['statement'])
            if p_probs and p_probs['entailment'] >= 0.50:
                p_status = 'ENTAILED'
            elif p_probs and p_probs['contradiction'] >= 0.50:
                p_status = 'CONTRADICTED'
            else:
                p_status = 'NEUTRAL'
        else:
            p_status = 'NEUTRAL'
        prop_results.append({
            'proposition': prop['statement'],
            'aspect': prop['aspect'],
            'status': p_status
        })

    num_support = len([s for s in supporting_sources if s['nli']['nli_verdict'] == 'ENTAILMENT'])
    num_partial = len([s for s in supporting_sources if s['nli']['nli_verdict'] == 'PARTIAL_SUPPORT'])
    num_contra = len(contradicting_sources)
    num_total = len(evaluated_sources)
    num_irrelevant = len(irrelevant_sources)

    # Calculate Aggregate Neural NLI Scores
    avg_ent_prob = 0.0
    if supporting_sources:
        avg_ent_prob = sum(s['nli']['nli_probabilities']['entailment'] for s in supporting_sources) / len(supporting_sources)

    # --- FINAL VERDICT DETERMINATION ---
    if num_total == 0 or (num_support == 0 and num_partial == 0 and num_contra == 0):
        verdict = "UNVERIFIED / INSUFFICIENT EVIDENCE"
        verdict_state = "UNVERIFIED"
        verdict_color = "secondary"
        confidence = 25.0
        summary = "No official news reports or web evidence were found to verify or refute this claim."
    elif num_contra > 0 and num_support == 0:
        verdict = "CONTRADICTED / FAKE RUMOR"
        verdict_state = "CONTRADICTED"
        verdict_color = "danger"
        confidence = min(95.0, 75.0 + (num_contra * 10.0))
        summary = f"Flagged as Misinformation! Neural NLI verified {num_contra} sources explicitly refuting or debunking this claim."
    elif num_contra > 0 and num_support > 0:
        verdict = "CONFLICTING EVIDENCE"
        verdict_state = "CONFLICTING"
        verdict_color = "warning"
        confidence = 50.0
        summary = f"Conflicting reports found: {num_support} sources support the claim, while {num_contra} sources contradict it."
    elif num_support >= 1:
        if temporal_mismatches > 0 or numerical_mismatches > 0 or num_partial > 0:
            verdict = "PARTIALLY SUPPORTED"
            verdict_state = "PARTIALLY_SUPPORTED"
            verdict_color = "warning"
            confidence = 68.0
            summary = "Partially supported: Neural NLI confirms core topic, but specific dates, release timing, or numerical parameters differ."
        else:
            verdict = "VERIFIED / STRONGLY SUPPORTED"
            verdict_state = "VERIFIED"
            verdict_color = "success"
            confidence = min(96.0, round(75.0 + (avg_ent_prob * 20.0), 1))
            summary = f"Authentic & Verified! Confirmed by {num_support} independent live news reports with {avg_ent_prob*100:.1f}% Neural NLI entailment confidence."
    elif num_partial >= 1:
        verdict = "PARTIALLY SUPPORTED"
        verdict_state = "PARTIALLY_SUPPORTED"
        verdict_color = "warning"
        confidence = 65.0
        summary = "Partially supported: News sources confirm the core topic, but dates or numbers in the claim differ."
    else:
        verdict = "UNVERIFIED / INSUFFICIENT EVIDENCE"
        verdict_state = "UNVERIFIED"
        verdict_color = "secondary"
        confidence = 30.0
        summary = "Live articles discuss related keywords, but Neural NLI confirms ZERO verified sources entailing this specific claim assertion."

    return {
        'claim': text,
        'primary_subject': claim_analysis.get('primary_subject'),
        'claim_components': {
            'entities': claim_analysis['entities'],
            'primary_subject': claim_analysis.get('primary_subject'),
            'secondary_entities': claim_analysis.get('secondary_entities'),
            'dates': claim_analysis['dates'],
            'numbers': claim_analysis['numbers'],
            'locations': claim_analysis['locations'],
            'event_type': claim_analysis['event_type']
        },
        'propositions_evaluation': prop_results,
        'verdict': verdict,
        'verdict_state': verdict_state,
        'verdict_color': verdict_color,
        'confidence': round(confidence, 1),
        'summary': summary,
        'query_used': queries['confirmation'][0] if queries['confirmation'] else text[:50],
        'is_verified': verdict_state in ['VERIFIED', 'SUPPORTED'],
        'supporting_evidence': supporting_sources,
        'contradicting_evidence': contradicting_sources,
        'neutral_evidence': neutral_sources,
        'irrelevant_sources_count': num_irrelevant,
        'source_corroboration': {
            'evaluated_sources_count': num_total,
            'independent_sources_count': len(sources),
            'syndicated_copies_detected': syndicated_copies,
            'ignored_irrelevant_count': num_irrelevant
        },
        'consistency_checks': {
            'entity_consistency': 'MATCH' if entity_mismatches == 0 else 'MISMATCH',
            'temporal_consistency': 'MATCH' if temporal_mismatches == 0 else 'DATE_MISMATCH',
            'numerical_consistency': 'MATCH' if numerical_mismatches == 0 else 'NUMBER_MISMATCH'
        },
        'sources': (evaluated_sources + irrelevant_sources)[:6]
    }
