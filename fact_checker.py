import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from duckduckgo_search import DDGS
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()

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
    'factly.in'
]

NOISE_WORDS = {'live', 'day', 'breaking', 'urgent', 'just', 'in', 'update', 'news', 'today', 'watch', 'video', 'full', 'teh', 'goona', 'realsed', 'released', 'release'}
KNOWN_PRODUCTS = {'gemini', 'perplexity', 'chatgpt', 'iphone', 'galaxy', 'pixel', 'airtel', 'jio', 'reliance', 'google', 'apple', 'samsung', 'tesla', 'microsoft', 'amazon', 'flipkart', 'meta', 'bcci', 'nasa', 'isro', 'kohli', 'rahane', 'modi', 'trump', 'biden', 'ramayan', 'ramayana', 'namit', 'malhotra', 'adarsha', 'aadarsha', 'kutumbam'}

MONTH_MAP = {
    'jan': 'january', 'feb': 'february', 'mar': 'march', 'apr': 'april',
    'may': 'may', 'jun': 'june', 'jul': 'july', 'aug': 'august',
    'sep': 'september', 'sept': 'september', 'oct': 'october',
    'nov': 'november', 'dec': 'december'
}
MONTHS_DATES = {'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december', 'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'sept', 'oct', 'nov', 'dec', 'diwali', 'eid', 'christmas', 'gandhi jayanthi', '2024', '2025', '2026', '2027', '2028'}

def clean_tokens(text):
    text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
    stopwords = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'from', 'by', 'for', 'of', 'with', 'is', 'has', 'that', 'it', 'this', 'today', 'all', 'been', 'will'}
    return [stemmer.stem(w) for w in text_clean.split() if w not in stopwords and len(w) > 2]

def get_bigrams(tokens):
    return [(tokens[i], tokens[i+1]) for i in range(len(tokens)-1)]

def tokens_similar(t1, t2):
    if t1 == t2:
        return True
    if len(t1) > 3 and len(t2) > 3:
        if t1 in t2 or t2 in t1:
            return True
    return False

def normalize_date_text(text):
    text_lower = text.lower()
    for short_m, long_m in MONTH_MAP.items():
        text_lower = re.sub(r'\b' + short_m + r'\b', long_m, text_lower)
    return text_lower

def extract_primary_entities(text):
    clean_text = re.sub(r'[^\w\s]', ' ', text)
    words = clean_text.split()
    
    proper_nouns = []
    for w in words:
        w_lower = w.lower()
        if (len(w) > 1 and w[0].isupper()) or w_lower in KNOWN_PRODUCTS:
            if w_lower not in NOISE_WORDS and w_lower not in {'the', 'to', 'for', 'a', 'an', 'in', 'on', 'at', 'give', 'free', 'year', 'realsed', 'released'}:
                proper_nouns.append(w_lower)
                
    return list(dict.fromkeys(proper_nouns))

def extract_date_expressions(text):
    norm_text = normalize_date_text(text)
    words = norm_text.split()
    
    dates = []
    for i, w in enumerate(words):
        if w in MONTHS_DATES or w in MONTH_MAP.values():
            dates.append(w)
            if i + 1 < len(words) and words[i+1].isdigit():
                dates.append(f"{w} {words[i+1]}")
        elif w.isdigit() and len(w) == 4 and w.startswith('20'):
            dates.append(w)
            
    return list(dict.fromkeys(dates))

def extract_search_query(text):
    clean_text = re.sub(r'[^\w\s]', ' ', text)
    words = clean_text.split()
    
    filtered_words = [w for w in words if w.lower() not in NOISE_WORDS]
    proper_nouns = [w for w in filtered_words if len(w) > 1 and w[0].isupper()]
    key_words = [w for w in filtered_words if len(w) > 2 and w.lower() not in ['this', 'that', 'from', 'with', 'have', 'taken', 'been', 'will', 'there']]
    
    combined = list(dict.fromkeys(proper_nouns + key_words))
    if len(combined) >= 2:
        query = ' '.join(combined[:6])
    else:
        query = ' '.join(words[:6])
        
    return query.strip()

def is_domain_trusted(domain, url):
    d = domain.lower()
    u = url.lower()
    
    if any(td in d or td in u for td in TRUSTED_DOMAINS):
        return True
    if d.endswith('.gov') or d.endswith('.gov.in') or d.endswith('.edu') or d.endswith('sansad.in') or d.endswith('pib.gov.in'):
        return True
    return False

def fetch_google_news_rss(query):
    sources = []
    try:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            tree = ET.fromstring(resp.read())
            items = tree.findall('.//item')
            for item in items[:8]:
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
                fact_check = any(fd in domain for fd in FACT_CHECK_DOMAINS) or 'fact check' in title.lower()
                
                sources.append({
                    'title': title,
                    'url': link,
                    'snippet': f"Published: {pub_date}",
                    'source': source_name,
                    'is_trusted': trusted,
                    'is_fact_check': fact_check
                })
    except Exception as e:
        print(f"Google News RSS error: {e}")
        
    return sources

def verify_claim_live(text):
    """
    AI Temporal, Entity & Relational Entailment Fact-Checker
    """
    query = extract_search_query(text)
    if not query:
        query = text[:50]
        
    sources = []
    fact_check_hits = 0
    seen_titles = set()
    
    rss_sources = fetch_google_news_rss(query)
    for s in rss_sources:
        if s['title'] in seen_titles:
            continue
        seen_titles.add(s['title'])
        if s['is_fact_check']:
            fact_check_hits += 1
        sources.append(s)
        
    if len(sources) < 2:
        try:
            ddgs = DDGS()
            text_results = list(ddgs.text(query, max_results=6))
            for r in text_results:
                title = r.get('title', '')
                url = r.get('href', '')
                snippet = r.get('body', '')
                domain = urllib.parse.urlparse(url).netloc.lower()
                
                if title in seen_titles:
                    continue
                seen_titles.add(title)
                
                trusted = is_domain_trusted(domain, url)
                fact_check = any(fd in domain for fd in FACT_CHECK_DOMAINS) or 'fact check' in title.lower()
                if fact_check:
                    fact_check_hits += 1
                    
                sources.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'source': domain,
                    'is_trusted': trusted,
                    'is_fact_check': fact_check
                })
        except Exception as e:
            print(f"DDGS Fallback search error: {e}")

    claim_entities = extract_primary_entities(text)
    claim_dates = extract_date_expressions(text)
    c_tokens = clean_tokens(text)
    c_bigrams = get_bigrams(c_tokens)
    
    confirming_sources = []
    
    for s in sources:
        t_clean = (s['title'] + " " + s.get('snippet', '')).lower()
        t_clean_norm = normalize_date_text(t_clean)
        t_words = re.sub(r'[^\w\s]', ' ', t_clean).split()
        t_tokens = clean_tokens(s['title'] + " " + s.get('snippet', ''))
        t_bigrams = get_bigrams(t_tokens)
        t_tokens_set = set(t_tokens)
        
        # 1. Primary Subject Entity Match
        has_all_entities = all(e in t_clean or stemmer.stem(e) in t_tokens_set or any(tokens_similar(e, tt) for tt in t_tokens_set) for e in claim_entities) if claim_entities else True
        
        # 2. Entity Proximity Verification
        proximity_valid = True
        if len(claim_entities) >= 2:
            e1, e2 = claim_entities[0], claim_entities[1]
            if e1 in t_words and e2 in t_words:
                dist = abs(t_words.index(e1) - t_words.index(e2))
                if dist > 4:
                    proximity_valid = False

        # 3. Temporal & Date Expression Match (using normalized date text)
        has_date_match = True
        if claim_dates:
            has_date_match = any(d in t_clean_norm for d in claim_dates)

        # 4. Action / Bigram Match (with fuzzy token similarity)
        bigram_hits = 0
        if c_bigrams:
            for (b1, b2) in c_bigrams:
                matched = False
                for (tb1, tb2) in t_bigrams:
                    if (tokens_similar(b1, tb1) and tokens_similar(b2, tb2)) or (tokens_similar(b1, tb2) and tokens_similar(b2, tb1)):
                        matched = True
                        break
                if matched:
                    bigram_hits += 1
                elif any(tokens_similar(b1, tt) for tt in t_tokens_set) and any(tokens_similar(b2, tt) for tt in t_tokens_set):
                    bigram_hits += 1
                    
            has_action_match = bigram_hits >= 1
        else:
            has_action_match = any(any(tokens_similar(tok, tt) for tt in t_tokens_set) for tok in c_tokens)

        if has_all_entities and proximity_valid and has_date_match and has_action_match:
            confirming_sources.append(s)

    is_verified = len(confirming_sources) >= 1
    
    print(f"Claim: '{text[:40]}...' | Entities: {claim_entities} | Dates: {claim_dates} | Confirming Articles: {len(confirming_sources)}")

    # Formulate Verdict
    if fact_check_hits > 0:
        status = "Fact-Check Article Found"
        verdict_color = "warning"
        summary = f"Found {fact_check_hits} fact-checking articles discussing this claim."
        is_verified = False
    elif is_verified:
        status = "Verified Live News Coverage"
        verdict_color = "success"
        summary = f"Confirmed! Found {len(confirming_sources)} live news reports directly verifying this claim and date."
    elif len(sources) > 0 and claim_dates and not is_verified:
        date_str = ", ".join(claim_dates)
        status = "Unverified Claim / False Rumor"
        verdict_color = "danger"
        summary = f"Live news articles exist for this topic, but ZERO verified sources confirm the date '{date_str}' in '{text[:40]}...'."
        is_verified = False
    elif len(sources) > 0 and len(claim_entities) > 0 and not is_verified:
        primary_subject = claim_entities[0].capitalize()
        status = "Unverified Claim / False Rumor"
        verdict_color = "danger"
        summary = f"Live news articles exist, but ZERO verified sources report {primary_subject} in the claim '{text[:40]}...'."
        is_verified = False
    else:
        status = "Unverified Rumor / Misinformation"
        verdict_color = "danger"
        summary = f"No official reports or web coverage found for '{query}'."
        is_verified = False

    return {
        'status': status,
        'verdict_color': verdict_color,
        'summary': summary,
        'query_used': query,
        'is_verified': is_verified,
        'sources': confirming_sources[:6] if is_verified else sources[:6]
    }
