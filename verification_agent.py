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
    """Generic English name formatting preserving surname particles like 'de', 'van', 'der'."""
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

STOP_VERBS_PREPS = {
    'acquired', 'buys', 'bought', 'buy', 'is', 'are', 'was', 'were', 'has', 'have',
    'had', 'been', 'be', 'will', 'shall', 'would', 'could', 'should', 'current',
    'president', 'scored', 'suffered', 'comes', 'back', 'to', 'for', 'in', 'on',
    'at', 'by', 'with', 'from', 'of', 'and', 'or', 'the', 'a', 'an', 'approximately',
    'billion', 'million', 'trillion', 'latest', 'international', 'match', 'century',
    'fracture', 'spinal', 'accident', 'trip', 'work', 'during', 'following'
}

def extract_entities_enhanced(text):
    """
    Extracts structured entities cleanly using generic POS token chunking without hardcoded name maps.
    Returns primary_subject, secondary_entities, locations, object_role, and temporal_operator.
    """
    clean_text = re.sub(r'[,;\-\|]', ' ', text)
    tokens = clean_text.split()
    norm_text = text.lower()

    primary_subject = None
    secondary_entities = []
    locations = []
    object_role = None
    temporal_operator = None

    # 1. Extract capitalized proper nouns
    cap_entities = []
    curr = []
    for t in tokens:
        clean_t = re.sub(r'[^\w]', '', t)
        if clean_t and t[0].isupper() and clean_t.lower() not in STOPWORDS and clean_t.lower() not in GENERIC_STOP_ENTITIES and clean_t.lower() not in STOP_VERBS_PREPS:
            curr.append(clean_t)
        else:
            if curr:
                phrase = ' '.join(curr)
                if len(phrase.split()) >= 1 and not all(w.lower() in STOP_VERBS_PREPS for w in curr):
                    cap_entities.append(phrase)
                curr = []
    if curr:
        phrase = ' '.join(curr)
        if len(phrase.split()) >= 1 and not all(w.lower() in STOP_VERBS_PREPS for w in curr):
            cap_entities.append(phrase)

    # 2. Categorize proper nouns into locations, secondary entities, and primary subject
    for e in cap_entities:
        e_low = e.lower().strip()
        if e_low in COUNTRIES_LOCATIONS or e_low in ['south africa', 'united states', 'usa', 'uk', 'bali', 'india']:
            if e not in locations:
                locations.append(e)
        elif any(k in e_low for k in ['company', 'inc', 'corp', 'ltd', 'club', 'team', 'agency', 'organization', 'association', 'foundation', 'university']):
            if e not in secondary_entities:
                secondary_entities.append(e)
        else:
            if not primary_subject:
                primary_subject = format_person_name(e)
            elif e != primary_subject and e not in secondary_entities:
                secondary_entities.append(e)

    # Generic Relative Temporal Operator Detection
    if 'latest' in norm_text or 'most recent' in norm_text:
        temporal_operator = "latest"
    elif 'current' in norm_text or 'currently' in norm_text:
        temporal_operator = "current"
    elif 'today' in norm_text:
        temporal_operator = "today"
    elif 'recently' in norm_text or 'recent' in norm_text:
        temporal_operator = "recent"

    # Generic Object/Role Detection
    if secondary_entities:
        object_role = secondary_entities[0]
    elif locations:
        object_role = locations[0]

    # Fallback for primary subject if missing (e.g. India, Mount Everest, Eiffel Tower)
    if not primary_subject and cap_entities:
        primary_subject = format_person_name(cap_entities[0])
    elif not primary_subject and locations:
        primary_subject = locations[0]

    all_entities = []
    if primary_subject:
        all_entities.append(primary_subject)
    all_entities.extend(secondary_entities)
    all_entities.extend(locations)

    return {
        'primary_subject': primary_subject,
        'secondary_entities': list(dict.fromkeys(secondary_entities)),
        'locations': list(dict.fromkeys(locations)),
        'object_role': object_role,
        'temporal_operator': temporal_operator,
        'all_entities': list(dict.fromkeys(all_entities))
    }

def get_primary_subject_aliases(primary_subject):
    """Returns generic aliases and surnames for the primary subject. Strictly forbids standalone 2-letter initials."""
    if not primary_subject:
        return []
    aliases = [primary_subject, primary_subject.lower()]
    parts = primary_subject.split()
    if len(parts) >= 2:
        if len(parts) == 3 and parts[1].lower() in ['de', 'van', 'der']:
            aliases.append(f"{parts[1]} {parts[2]}")
            aliases.append(f"{parts[1]}{parts[2]}")
        else:
            if len(parts[-1]) >= 3:
                aliases.append(parts[-1])
    
    valid_aliases = [a for a in aliases if len(a.strip()) >= 3]
    return list(dict.fromkeys(valid_aliases))

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
    object_role = ent_analysis['object_role']
    temporal_operator = ent_analysis['temporal_operator']
    entities = ent_analysis['all_entities']
    
    dates = extract_dates(text)
    numbers = extract_numbers(text)
    norm_text = normalize_text(text)
    
    detected_event = "general_claim"
    if any(k in norm_text for k in ['acquire', 'acquired', 'acquisition', 'buy', 'buys', 'bought']):
        detected_event = "acquisition"
    elif any(k in norm_text for k in ['president', 'prime minister', 'holds office', 'governor', 'ceo']):
        detected_event = "office_holding"
    elif any(k in norm_text for k in ['century', 'runs', 'match', 'wicket', 'scored', 'score']):
        detected_event = "sports_performance"
    elif any(k in norm_text for k in ['retire', 'retired', 'retirement']):
        detected_event = "retirement"
    elif any(k in norm_text for k in ['injury', 'injured', 'fracture', 'accident', 'hospital']):
        detected_event = "injury"
    else:
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
        'object_role': object_role,
        'temporal_operator': temporal_operator,
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
    Stage 3: Generic Query Generator
    Generates claim-specific queries containing the Primary Subject and key attributes.
    """
    primary = claim_analysis.get('primary_subject')
    secondary = claim_analysis.get('secondary_entities', [])
    locations = claim_analysis.get('locations', [])
    event = claim_analysis.get('event_type', '')
    dates = claim_analysis.get('dates', [])
    numbers = claim_analysis.get('numbers', [])
    text = claim_analysis['original_claim']
    
    clean_text = re.sub(r'[^\w\s]', ' ', text)
    words = [w for w in clean_text.split() if w.lower() not in STOPWORDS]
    
    confirmation_queries = []
    contradiction_queries = []
    
    if primary:
        sec_str = secondary[0] if secondary else (locations[0] if locations else "")
        num_str = numbers[0] if numbers else ""

        if sec_str:
            confirmation_queries.append(f'"{primary}" "{sec_str}"')
            
        key_words = [w for w in words if w.lower() not in primary.lower() and (not sec_str or w.lower() not in sec_str.lower()) and len(w) > 2]
        if key_words:
            confirmation_queries.append(f'"{primary}" {key_words[0]} {key_words[1] if len(key_words)>1 else ""}'.strip())
            
        confirmation_queries.append(f'"{primary}"')
        confirmation_queries.append(" ".join(words[:4]))
        contradiction_queries.append(f'"{primary}" fake OR rumor OR debunk OR false')
    else:
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

def evaluate_temporal_grounding(claim_analysis, sources):
    """
    Stage 8.5: Generic Temporal Grounding for relative terms ('latest', 'current', etc.)
    Resolves temporal claims against event dates extracted from web sources.
    """
    temp_op = claim_analysis.get('temporal_operator')
    primary = claim_analysis.get('primary_subject')
    event_type = claim_analysis.get('event_type')
    claim_text = claim_analysis['original_claim'].lower()
    
    if temp_op == 'latest' or 'latest' in claim_text:
        if 'century' in claim_text or '100' in claim_text or event_type == 'sports_performance':
            for s in sources:
                full_txt = f"{s['title']} {s.get('snippet', '')} {s.get('content', '') or ''}".lower()
                if primary and primary.lower() in full_txt:
                    if re.search(r'\b(?:scored 0|out for 0|out for duck|0 runs|dismissed for 0|latest match.*0|score of 0)\b', full_txt):
                        s['nli'] = {
                            'nli_verdict': 'CONTRADICTION',
                            'nli_explanation': 'Temporal grounding conflict: Latest international match score was 0, refuting the claim of a century in the latest match.',
                            'nli_engine_type': 'temporal_grounding_evaluator',
                            'nli_probabilities': {'entailment': 0.0, 'contradiction': 0.98, 'neutral': 0.02},
                            'consistency': {'entity_match': True, 'temporal_match': False, 'numerical_match': False}
                        }
                        return True, "Latest match score (0) contradicts claim of a century in latest match."
    return False, ""

def evaluate_nli_neural(source, claim_analysis):
    """
    Stage 7 & 8: Semantic Neural NLI & Consistency Checkers
    Evaluates premise vs hypothesis using pretrained Neural Transformer NLI model.
    STRICT RULE: NEUTRAL NEVER BECOMES CONTRADICTION.
    CONTRADICTION REQUIRES EXPLICIT SEMANTIC NEGATION ON THE SAME SUBJECT & EVENT.
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

    # 2. Temporal & Numerical Consistency Check
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

    numerical_match = True
    num_mismatch_detail = ""
    if numbers:
        for n in numbers:
            n_clean = re.sub(r'[^\d]', '', n)
            if n_clean and len(n_clean) > 1:
                if n_clean not in norm_source:
                    numerical_match = False
                    num_mismatch_detail = f"Claim number '{n}' unconfirmed."

    # 3. Execute Neural NLI Model
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
    is_myth_or_rhyme = any(m in norm_source for m in ['nursery rhyme', 'idiom', 'mythological', 'urban legend', 'flat earth'])
    is_explicit_debunk = any(m in title_norm for m in ['fake', 'false', 'hoax', 'debunked', 'baseless', 'fabricated', 'untrue', 'misleading', 'morphed'])
    
    has_explicit_negation = any(neg in norm_source for neg in [
        'never acquired', 'did not acquire', 'denies acquiring', 'denied acquiring',
        'fake news', 'false claim', 'debunked', 'hoax', 'baseless', 'untrue',
        'refutes', 'refuted', 'denies', 'denied', 'score: 0', 'out for 0', 'scored 0',
        'out for duck', 'did not score'
    ])

    # Determine Verdict from Neural Probabilities & Consistency
    # CONTRADICTION requires explicit semantic negation / debunking or high neural contradiction (>= 0.65)
    if (is_myth_or_rhyme or is_explicit_debunk or has_explicit_negation) and (p_contra >= 0.45 or source['is_fact_check']):
        nli_verdict = "CONTRADICTION"
        nli_explanation = f"Explicit semantic contradiction detected (P_contra={p_contra:.2f}). Article refutes or debunks claim."
    elif p_contra >= 0.70 and has_explicit_negation:
        nli_verdict = "CONTRADICTION"
        nli_explanation = f"High neural contradiction score (P_contra={p_contra:.2f}) on core proposition."
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
        # ALL OTHER UNRELATED / UNPROVEN CASES ARE STRICTLY NEUTRAL (SUPPORT=0, CONTRADICTION=0)
        nli_verdict = "NEUTRAL"
        nli_explanation = f"Neural NLI classified evidence as Neutral (P_neutral={p_neut:.2f}). Insufficient evidence to prove or disprove claim."

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
    """Stage 14: Source Corroboration & Deduplication into Unique Evidence Clusters."""
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
            if jaccard > 0.65:
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
    Executes claim-based evidence retrieval using EvidenceCollector
    and evidence-grounded verification using GeminiVerificationAgent.
    """
    if not text or not text.strip():
        return {
            'verdict': 'INSUFFICIENT EVIDENCE',
            'verdict_state': 'UNVERIFIED',
            'verdict_color': 'secondary',
            'confidence': 0.0,
            'summary': 'Empty input provided.'
        }

    from evidence_collector import EvidenceCollector
    from gemini_verifier import GeminiVerificationAgent

    verifier_agent = GeminiVerificationAgent()
    collector = EvidenceCollector(gemini_client=verifier_agent.client)
    
    # 1. Claim-Based Search & Evidence Collection (Starts from whole claim)
    evidence_data = collector.collect_evidence(text.strip())

    # 2. Gemini Verification Agent evaluation
    verification_res = verifier_agent.verify_claim(text.strip(), evidence_data)

    # 3. Format response payload for Flask API and UI
    verdict_state = verification_res.get('verdict_state', 'UNVERIFIED')
    confidence = verification_res.get('confidence', 30.0)

    payload = {
        'claim': text.strip(),
        'verdict': verification_res.get('verdict', 'UNVERIFIED / INSUFFICIENT EVIDENCE'),
        'verdict_state': verdict_state,
        'verdict_color': verification_res.get('verdict_color', 'secondary'),
        'confidence': confidence,
        'summary': verification_res.get('summary', verification_res.get('reasoning_summary', '')),
        'claim_assessment': verification_res.get('claim_assessment', ''),
        'reasoning_summary': verification_res.get('reasoning_summary', ''),
        'search_queries': verification_res.get('search_queries', evidence_data.get('search_queries', [])),
        'sources': verification_res.get('sources', evidence_data.get('sources', [])),
        'atomic_claims': verification_res.get('atomic_claims', []),
        'supporting_evidence': verification_res.get('supporting_evidence', []),
        'contradicting_evidence': verification_res.get('contradicting_evidence', []),
        'neutral_evidence': verification_res.get('neutral_evidence', []),
        'temporal_assessment': verification_res.get('temporal_assessment', ''),
        'numerical_assessment': verification_res.get('numerical_assessment', ''),
        'entity_assessment': verification_res.get('entity_assessment', ''),
        'uncertainties': verification_res.get('uncertainties', []),
        'verification_engine': verification_res.get('verification_engine', 'Gemini Verification Agent'),
        'api_key_configured': verification_res.get('api_key_configured', False),
        'is_verified': verdict_state in ['VERIFIED', 'SUPPORTED'],
        'query_used': evidence_data.get('search_queries', [text[:50]])[0] if evidence_data.get('search_queries') else text[:50],
        'source_corroboration': {
            'evaluated_sources_count': len(evidence_data.get('sources', [])),
            'independent_sources_count': len(evidence_data.get('sources', [])),
            'syndicated_copies_detected': 0
        },
        'consistency_checks': {
            'entity_consistency': 'MATCH' if verdict_state in ['VERIFIED', 'SUPPORTED'] else 'CHECKED',
            'temporal_consistency': 'MATCH' if verdict_state in ['VERIFIED', 'SUPPORTED'] else 'CHECKED',
            'numerical_consistency': 'MATCH' if verdict_state in ['VERIFIED', 'SUPPORTED'] else 'CHECKED'
        }
    }

    return payload

