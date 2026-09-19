import streamlit as st
import requests
import pandas as pd
from rapidfuzz import fuzz
from fpdf import FPDF
import os
from datetime import datetime
import re

# ============================================================
# ORIC Research Paper Verification Portal
# Office of Research, Innovation and Commercialization (ORIC)
# Standardized Academic Registry Cross-Verification System
# ============================================================

st.set_page_config(
    page_title="ORIC | Research Paper Verification Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Configuration & Constants ---
CROSSREF_API = "https://api.crossref.org/works"
DOAJ_API = "https://doaj.org/api/v2/search/articles/"
DOAJ_JOURNAL_API = "https://doaj.org/api/v2/search/journals/"
DATACITE_API = "https://api.datacite.org/dois"
PUBMED_SEARCH_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
OPEN_CITATIONS_API = "https://opencitations.net/index/api/v1"
ISSN_PORTAL_API = "https://portal.issn.org/resource/ISSN"

STATUS_VERIFIED = "Verified"
STATUS_PARTIAL = "Partial Match"
STATUS_SUSPICIOUS = "Suspicious"
STATUS_NOT_FOUND = "Not Found"

THRESHOLD_EXACT = 95
THRESHOLD_HIGH = 85
THRESHOLD_MEDIUM = 70

# --- Academic Sage & Peach Theme CSS ---
# Soft sage + warm peach + ivory: academic, institutional and less "corporate dark blue".
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Libre+Baskerville:wght@400;700&display=swap');

    :root {
        --ivory: #F8F6F0;
        --paper: #FFFDF8;
        --sage: #5F8D78;
        --sage-dark: #3F6B59;
        --sage-soft: #E7F0EA;
        --peach: #E9A889;
        --peach-soft: #FBE9DF;
        --ink: #24332D;
        --muted: #66736D;
        --line: #D9DED8;
        --gold: #B88A4A;
        --danger: #B65B55;
        --warning: #B47A3C;
    }

    .stApp {
        background: linear-gradient(180deg, #F8F6F0 0%, #F5F3EC 100%) !important;
        color: var(--ink) !important;
        font-family: 'DM Sans', sans-serif;
    }

    .stApp, .stApp p, .stApp span, .stApp li, .stApp label,
    .stApp div[data-testid="stMarkdownContainer"],
    .stApp div[data-testid="stMarkdownContainer"] p,
    .stApp div[data-testid="stCaptionContainer"],
    .stApp [data-testid="stWidgetLabel"] p,
    .stApp .stTextInput input, .stApp .stTextArea textarea {
        color: var(--ink) !important;
    }

    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2.5rem;
        max-width: 1420px;
    }

    /* Header */
    .inst-header {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, #EEF4EF 0%, #FBE9DF 100%);
        border: 1px solid #D8E2DA;
        border-left: 7px solid var(--sage);
        border-radius: 18px;
        padding: 30px 38px;
        margin-bottom: 24px;
        box-shadow: 0 10px 28px rgba(63,107,89,.08);
    }
    .inst-header:after {
        content: "ORIC";
        position: absolute;
        right: 30px;
        top: 18px;
        font-family: 'Libre Baskerville', serif;
        font-size: 4.5rem;
        font-weight: 700;
        color: rgba(95,141,120,.08);
        letter-spacing: .08em;
    }
    .inst-header .sub-caption {
        font-size: .72rem;
        letter-spacing: 1.7px;
        color: var(--sage-dark) !important;
        font-weight: 700;
        margin-bottom: 7px;
    }
    .inst-header h1 {
        font-family: 'Libre Baskerville', Georgia, serif;
        font-size: 2rem;
        font-weight: 700;
        color: var(--ink) !important;
        margin: 0 0 8px 0;
    }
    .inst-header p {
        margin: 0;
        color: #58675F !important;
        font-size: .91rem;
        max-width: 78ch;
        line-height: 1.6;
    }

    /* Cards */
    .panel-card {
        background: rgba(255,253,248,.92);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 24px 26px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(36,51,45,.055);
    }
    .panel-header {
        font-family: 'Libre Baskerville', Georgia, serif;
        font-size: 1.12rem;
        font-weight: 700;
        color: var(--sage-dark) !important;
        padding-bottom: 11px;
        border-bottom: 2px solid #D8E6DD;
        margin-bottom: 18px;
    }
    .field-group-label {
        font-size: .73rem;
        font-weight: 700;
        color: #B06F50 !important;
        text-transform: uppercase;
        letter-spacing: .09em;
        margin: 17px 0 7px 0;
    }

    /* Inputs */
    .stTextInput > label, .stTextArea > label {
        font-weight: 600 !important;
        font-size: .84rem !important;
        color: var(--ink) !important;
    }
    .stTextInput input, .stTextArea textarea {
        background: #FFFDF9 !important;
        border: 1px solid #CBD5CE !important;
        border-radius: 10px !important;
        box-shadow: none !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--sage) !important;
        box-shadow: 0 0 0 2px rgba(95,141,120,.12) !important;
    }

    /* Buttons */
    div.stButton > button, .stLinkButton > a {
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: .86rem !important;
        min-height: 42px !important;
        border: 1px solid #C8D4CC !important;
        background: #F7FAF7 !important;
        color: var(--sage-dark) !important;
        transition: all .15s ease;
    }
    div.stButton > button:hover, .stLinkButton > a:hover {
        border-color: var(--sage) !important;
        transform: translateY(-1px);
        box-shadow: 0 5px 14px rgba(63,107,89,.12);
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--sage), #6FA087) !important;
        color: white !important;
        border: none !important;
    }

    /* Registry chips */
    .registry-chip {
        display: inline-block;
        padding: 5px 10px;
        background: var(--sage-soft);
        border: 1px solid #C9DED1;
        border-radius: 999px;
        font-size: .7rem;
        font-weight: 700;
        color: var(--sage-dark) !important;
        margin: 0 5px 6px 0;
    }

    /* Verdict */
    .seal-wrap {
        display: flex;
        align-items: center;
        gap: 20px;
        padding: 20px 22px;
        background: linear-gradient(135deg, #F1F6F2, #FFF6F0);
        border: 1px solid #D9E3DC;
        border-radius: 14px;
        margin-bottom: 16px;
    }
    .seal-box {
        border: 2px solid var(--seal-color);
        border-radius: 10px;
        padding: 11px 16px;
        font-family: 'Libre Baskerville', serif;
        font-weight: 700;
        font-size: .92rem;
        letter-spacing: .07em;
        color: var(--seal-color) !important;
        background: #FFFDF8;
        white-space: nowrap;
    }
    .seal-meta { flex: 1; }
    .seal-meta .conf-line { font-size: .92rem; color: var(--ink) !important; }
    .seal-meta .conf-value {
        font-weight: 800;
        color: var(--seal-color) !important;
        font-size: 1.15rem;
    }
    .seal-meta .rationale {
        font-size: .81rem;
        color: var(--muted) !important;
        margin-top: 5px;
        line-height: 1.55;
    }

    /* Notes */
    .ledger-note {
        border: 1px solid #D8E1DB;
        border-left: 4px solid var(--sage);
        border-radius: 9px;
        background: #F1F6F2;
        padding: 12px 15px;
        font-size: .81rem;
        color: #405149 !important;
        margin-top: 13px;
        line-height: 1.5;
    }
    .ledger-note.consensus {
        border-left-color: var(--sage);
        background: var(--sage-soft);
        color: #315644 !important;
    }
    .ledger-note.conflict {
        border-left-color: var(--danger);
        background: #FBECE9;
        color: #713F3A !important;
        font-weight: 600;
    }

    .id-code {
        font-family: monospace;
        font-size: .82rem;
        background: #F2EEE5;
        color: #4D554F !important;
        padding: 2px 6px;
        border-radius: 5px;
    }

    /* Dataframe / expander */
    [data-testid="stDataFrame"] {
        border: 1px solid #DCE2DD;
        border-radius: 10px;
        overflow: hidden;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #D8E1DB !important;
        border-radius: 10px !important;
        background: #FBFAF6 !important;
    }

    footer { visibility: hidden; }

    @media (max-width: 900px) {
        .inst-header { padding: 24px 22px; }
        .inst-header:after { display: none; }
        .inst-header h1 { font-size: 1.55rem; }
        .seal-wrap { align-items: flex-start; flex-direction: column; }
    }
</style>
""", unsafe_allow_html=True)

# --- Utility Functions ---
def safe_get(data, *keys, default=""):
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        elif isinstance(data, list) and isinstance(key, int) and key < len(data):
            data = data[key]
        else:
            return default
    return data if data is not None else default

def normalize_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', str(text).lower().strip())

def exact_match(str1, str2):
    if not str1 or not str2:
        return 0
    s1 = normalize_text(str1).replace("-", "").replace(" ", "")
    s2 = normalize_text(str2).replace("-", "").replace(" ", "")
    if s1 == s2 and s1 != "":
        return 100
    return 0

def strict_text_score(str1, str2):
    """
    Conservative similarity for titles / journal names / authors.

    The previous implementation scored these fields with fuzz.partial_ratio,
    which finds the best-matching SUBSTRING. That means a fabricated title
    that happens to share a run of words with an unrelated, real, indexed
    paper (e.g. a generic phrase, or a real title with a few words added or
    swapped) could score close to 100 even though it is not the same paper.
    That is the main mechanism behind fake papers being marked "Verified".

    We instead average a full-string ratio with a token-sort ratio (which
    tolerates word reordering but not substring padding), so a genuine
    near-duplicate still scores highly while a partial/incidental overlap
    does not.
    """
    if not str1 or not str2:
        return 0
    a, b = normalize_text(str1), normalize_text(str2)
    if not a or not b:
        return 0
    full = fuzz.ratio(a, b)
    token = fuzz.token_sort_ratio(a, b)
    return round((full + token) / 2)

def fuzzy_match_text(str1, str2):
    if not str1 or not str2:
        return 0
    return fuzz.ratio(normalize_text(str1), normalize_text(str2))

# --- API Fetching Functions ---
def _best_by_title(candidates, title, doi, get_title, get_doi):
    """
    Pick the candidate record that actually resembles the submitted paper,
    instead of blindly trusting the registry's top search hit.

    A registry search endpoint ranks by its own relevance signals, not by
    textual similarity to what the user typed - so item 0 is frequently
    "the closest thing we have", not "a match". If nothing clears the
    medium similarity threshold, we return None rather than silently
    substituting an unrelated record.
    """
    if not candidates:
        return None
    if doi:
        for c in candidates:
            if exact_match(doi, get_doi(c)) >= 98:
                return c
    if title:
        scored = [(strict_text_score(title, get_title(c)), c) for c in candidates]
        scored.sort(key=lambda x: x[0], reverse=True)
        if scored and scored[0][0] >= THRESHOLD_MEDIUM:
            return scored[0][1]
        return None
    return candidates[0]

def fetch_crossref_paper(title=None, doi=None, author=None):
    try:
        params = {"rows": 5}
        if doi:
            params["query.bibliographic"] = doi
        elif title:
            params["query.title"] = title
        if author:
            params["query.author"] = author
        response = requests.get(CROSSREF_API, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        items = safe_get(data, "message", "items", default=[])
        best = _best_by_title(
            items, title, doi,
            get_title=lambda it: (it.get("title") or [""])[0],
            get_doi=lambda it: it.get("DOI", "")
        )
        if best:
            return {"api": "Crossref", "data": best}
    except Exception as e:
        st.warning(f"Crossref Registry Error: {e}")
    return None

def fetch_crossref_journal(issn=None, title=None):
    if not issn and not title:
        return None
    try:
        params = {"rows": 5, "filter": "type:journal"}
        if issn:
            params["query"] = issn
        elif title:
            params["query"] = title
        response = requests.get(CROSSREF_API, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        items = safe_get(data, "message", "items", default=[])
        if not items:
            return None
        if issn:
            return {"api": "Crossref Journal", "data": items[0]}
        best = _best_by_title(
            items, title, None,
            get_title=lambda it: (it.get("container-title") or it.get("title") or [""])[0],
            get_doi=lambda it: ""
        )
        if best:
            return {"api": "Crossref Journal", "data": best}
    except Exception as e:
        st.warning(f"Crossref Journal Registry Error: {e}")
    return None

def fetch_doaj_paper(title=None, doi=None):
    try:
        query_parts = []
        if doi:
            query_parts.append(f"doi:{doi}")
        if title:
            query_parts.append(title)
        query = " AND ".join(query_parts) if query_parts else title or ""
        response = requests.get(DOAJ_API, params={"q": query, "pageSize": 5}, timeout=15)
        response.raise_for_status()
        data = response.json()
        results = safe_get(data, "results", default=[])
        bibs = [r.get("bibjson", {}) for r in results]

        def get_doi_from_bib(bib):
            for ident in bib.get("identifier", []):
                if ident.get("type") == "doi":
                    return ident.get("id", "")
            return ""

        best = _best_by_title(
            bibs, title, doi,
            get_title=lambda b: b.get("title", ""),
            get_doi=get_doi_from_bib
        )
        if best:
            return {"api": "DOAJ", "data": best}
    except Exception as e:
        st.warning(f"DOAJ Registry Error: {e}")
    return None

def fetch_doaj_journal(issn=None, title=None):
    if not issn and not title:
        return None
    try:
        query_parts = []
        if issn:
            query_parts.append(f"issn:{issn}")
        if title:
            query_parts.append(title)
        query = " AND ".join(query_parts) if query_parts else title or ""
        response = requests.get(DOAJ_JOURNAL_API, params={"q": query, "pageSize": 5}, timeout=15)
        response.raise_for_status()
        data = response.json()
        results = safe_get(data, "results", default=[])
        bibs = [r.get("bibjson", {}) for r in results]
        if not bibs:
            return None
        if issn:
            return {"api": "DOAJ Journal", "data": bibs[0]}
        best = _best_by_title(
            bibs, title, None,
            get_title=lambda b: b.get("title", ""),
            get_doi=lambda b: ""
        )
        if best:
            return {"api": "DOAJ Journal", "data": best}
    except Exception as e:
        st.warning(f"DOAJ Journal Registry Error: {e}")
    return None

def fetch_datacite_paper(doi=None):
    if not doi:
        return None
    try:
        url = f"{DATACITE_API}/{doi}"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return {"api": "DataCite", "data": safe_get(data, "data", "attributes", default={})}
    except Exception as e:
        st.warning(f"DataCite Registry Error: {e}")
    return None

def fetch_pubmed_paper(title=None, doi=None):
    try:
        if doi:
            search_params = {"db": "pubmed", "term": f"{doi}[DOI]", "retmode": "json", "retmax": 5}
            search_resp = requests.get(PUBMED_SEARCH_API, params=search_params, timeout=15)
            search_resp.raise_for_status()
            search_data = search_resp.json()
            idlist = safe_get(search_data, "esearchresult", "idlist", default=[])
            if idlist:
                return {"api": "PubMed", "data": {"pmid": idlist[0], "found": True}}
        elif title:
            search_params = {"db": "pubmed", "term": title, "retmode": "json", "retmax": 5}
            search_resp = requests.get(PUBMED_SEARCH_API, params=search_params, timeout=15)
            search_data = search_resp.json()
            idlist = safe_get(search_data, "esearchresult", "idlist", default=[])
            if idlist:
                return {"api": "PubMed", "data": {"pmid": idlist[0], "found": True}}
    except Exception as e:
        st.warning(f"PubMed Registry Error: {e}")
    return None

def fetch_open_citations(doi=None):
    if not doi:
        return None
    try:
        url = f"{OPEN_CITATIONS_API}/citations/{doi}"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            citations = response.json()
            return {"api": "OpenCitations", "data": {"citation_count": len(citations), "citations": citations[:3]}}
    except Exception as e:
        st.warning(f"OpenCitations Registry Error: {e}")
    return None

def fetch_issn_portal(issn=None):
    if not issn:
        return None
    try:
        url = f"{ISSN_PORTAL_API}/{issn}?format=json"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return {"api": "ISSN Portal", "data": response.json()}
    except Exception as e:
        st.warning(f"ISSN Portal Registry Error: {e}")
    return None

def fetch_doi_resolver(doi):
    if not doi:
        return None
    try:
        url = f"https://doi.org/{doi}"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if response.status_code == 200:
            try:
                return {"api": "DOI.org", "data": response.json()}
            except Exception:
                return {"api": "DOI.org", "data": {"resolved": True, "url": response.url}}
    except Exception as e:
        st.warning(f"DOI Resolution Error: {e}")
    return None

# --- Data Extraction Functions ---
def extract_from_crossref(item):
    msg = item.get("message", item)
    titles = safe_get(msg, "title", default=[])
    found_title = titles[0] if titles else ""
    found_doi = safe_get(msg, "DOI", default="")
    found_volume = str(safe_get(msg, "volume", default=""))
    found_issue = str(safe_get(msg, "issue", default=""))

    found_year = str(safe_get(msg, "published-print", "date-parts", 0, 0, default=""))
    if not found_year:
        found_year = str(safe_get(msg, "published-online", "date-parts", 0, 0, default=""))
    if not found_year:
        found_year = str(safe_get(msg, "created", "date-parts", 0, 0, default=""))

    authors_list = safe_get(msg, "author", default=[])
    found_authors = ", ".join([f"{a.get('given','')} {a.get('family','')}".strip() for a in authors_list[:3]])

    container = safe_get(msg, "container-title", default=[])
    found_journal = container[0] if container else ""

    issns = safe_get(msg, "ISSN", default=[])
    found_pissn = issns[0] if len(issns) > 0 else ""
    found_eissn = issns[1] if len(issns) > 1 else ""

    url = safe_get(msg, "URL", default="")
    if not url and found_doi:
        url = f"https://doi.org/{found_doi}"

    return {
        "title": found_title, "doi": found_doi, "journal": found_journal,
        "pissn": found_pissn, "eissn": found_eissn, "volume": found_volume,
        "issue": found_issue, "year": found_year, "authors": found_authors,
        "url": url, "publisher": safe_get(msg, "publisher", default=""),
        "type": safe_get(msg, "type", default="")
    }

def extract_from_doaj(bib):
    found_title = safe_get(bib, "title", default="")
    found_doi = ""
    ids = safe_get(bib, "identifier", default=[])
    for ident in ids:
        if ident.get("type") == "doi":
            found_doi = ident.get("id", "")

    journal_obj = safe_get(bib, "journal", default={})
    found_journal = journal_obj.get("title", "") if isinstance(journal_obj, dict) else ""
    found_volume = str(journal_obj.get("volume", "")) if isinstance(journal_obj, dict) else ""
    found_issue = str(journal_obj.get("number", "")) if isinstance(journal_obj, dict) else ""
    found_year = str(safe_get(bib, "year", default=""))

    authors_list = safe_get(bib, "author", default=[])
    found_authors = ", ".join([a.get("name", "") for a in authors_list[:3]])

    issns = safe_get(bib, "identifier", default=[])
    found_pissn = found_eissn = ""
    for ident in issns:
        if ident.get("type") == "pissn":
            found_pissn = ident.get("id", "")
        elif ident.get("type") == "eissn":
            found_eissn = ident.get("id", "")

    return {
        "title": found_title, "doi": found_doi, "journal": found_journal,
        "pissn": found_pissn, "eissn": found_eissn, "volume": found_volume,
        "issue": found_issue, "year": found_year, "authors": found_authors,
        "url": f"https://doi.org/{found_doi}" if found_doi else "",
        "type": "journal-article"
    }

def extract_from_datacite(attrs):
    found_title = safe_get(attrs, "titles", 0, "title", default="")
    found_doi = safe_get(attrs, "doi", default="")
    found_year = str(safe_get(attrs, "publicationYear", default=""))

    creators = safe_get(attrs, "creators", default=[])
    found_authors = ", ".join([c.get("name", "") for c in creators[:3]])

    return {
        "title": found_title, "doi": found_doi, "journal": "",
        "pissn": "", "eissn": "", "volume": "", "issue": "",
        "year": found_year, "authors": found_authors,
        "url": f"https://doi.org/{found_doi}" if found_doi else "",
        "type": safe_get(attrs, "types", "resourceTypeGeneral", default="")
    }

# --- Consensus Scoring Logic ---
def calculate_consensus_score(api_results, user_inputs):
    """
    Returns (match_results, confidence, field_sources, title_score).

    title_score is surfaced separately (not just folded into the weighted
    average) because it is the single field that actually identifies WHICH
    paper we are looking at. Everything else (year, volume, a well-known
    journal name) can coincidentally match many real, unrelated papers, so
    the calling code gates the final verdict on title_score rather than
    letting a strong showing on the easy fields outvote a weak title match.
    """
    field_scores = {}
    field_sources = {}

    weights = {
        "Paper Title": 2.5, "Journal Title": 2.0, "DOI": 3.0,
        "p-ISSN": 1.5, "e-ISSN": 1.0, "Volume": 0.8,
        "Issue": 0.5, "Year": 1.2, "Author": 1.5
    }

    exact_fields = {"DOI", "p-ISSN", "e-ISSN", "Volume", "Issue", "Year"}
    text_fields = {"Paper Title", "Journal Title", "Author"}

    field_getters = {
        "Paper Title": lambda e: e.get("title", ""),
        "Journal Title": lambda e: e.get("journal", ""),
        "DOI": lambda e: e.get("doi", ""),
        "p-ISSN": lambda e: e.get("pissn", ""),
        "e-ISSN": lambda e: e.get("eissn", ""),
        "Volume": lambda e: e.get("volume", ""),
        "Issue": lambda e: e.get("issue", ""),
        "Year": lambda e: e.get("year", ""),
        "Author": lambda e: e.get("authors", ""),
    }

    for api_name, extracted in api_results.items():
        if not extracted:
            continue
        for field, user_val in user_inputs.items():
            if not user_val:
                continue
            found_val = field_getters.get(field, lambda e: "")(extracted)
            if not found_val:
                continue

            if field in exact_fields:
                score = exact_match(user_val, found_val)
            elif field in text_fields:
                score = strict_text_score(user_val, found_val)
            else:
                score = strict_text_score(user_val, found_val)

            field_scores.setdefault(field, []).append(score)
            field_sources.setdefault(field, []).append(api_name)

    match_results = []
    total_score = 0
    weighted_count = 0
    title_score = None

    for field, user_val in user_inputs.items():
        if not user_val:
            match_results.append({
                "Field": field, "Submitted Data": "Not provided", "Registry Match": "Not provided",
                "Status": "Not Provided", "Score": "N/A", "Sources": "None"
            })
            continue

        scores = field_scores.get(field, [])
        sources = field_sources.get(field, [])

        if not scores:
            match_results.append({
                "Field": field, "Submitted Data": user_val,
                "Registry Match": "Not found in registries", "Status": "Not Found",
                "Score": "0%", "Sources": "None"
            })
            if field == "Paper Title":
                title_score = 0
            continue

        max_score = max(scores)
        agreeing_apis = sum(1 for s in scores if s >= THRESHOLD_HIGH)

        if agreeing_apis >= 2 and max_score >= THRESHOLD_EXACT:
            status = "Exact Match"
            consensus_score = 100
        elif max_score >= THRESHOLD_EXACT:
            status = "Exact Match"
            consensus_score = min(100, max_score)
        elif max_score >= THRESHOLD_HIGH:
            status = "High Match"
            consensus_score = max_score
        elif max_score >= THRESHOLD_MEDIUM:
            status = "Partial Match"
            consensus_score = max_score
        else:
            status = "Mismatch"
            consensus_score = max_score

        if field == "Paper Title":
            title_score = consensus_score

        best_idx = scores.index(max_score)
        best_source = sources[best_idx]
        best_value = ""
        for api_name, extracted in api_results.items():
            if api_name == best_source and extracted:
                best_value = field_getters.get(field, lambda e: "")(extracted)
                break

        weight = weights.get(field, 1.0)
        total_score += (consensus_score / 100.0) * weight
        weighted_count += weight

        sources_formatted = ", ".join(sorted(set(sources)))

        match_results.append({
            "Field": field,
            "Submitted Data": user_val,
            "Registry Match": best_value if best_value else "Not returned",
            "Status": status,
            "Score": f"{consensus_score}%",
            "Sources": sources_formatted
        })

    confidence = round((total_score / weighted_count) * 100, 1) if weighted_count > 0 else 0
    return match_results, confidence, field_sources, title_score

# --- Main Verification Function ---
def verify_paper_v3(title, journal_title, doi, pissn, eissn, volume, issue, year, author):
    st.info("Initiating cross-reference search across public academic registries...")

    progress = st.progress(0)
    api_status = st.empty()

    api_status.text("Querying Crossref Metadata API...")
    crossref_paper = fetch_crossref_paper(title=title, doi=doi, author=author)
    progress.progress(15)

    api_status.text("Querying Directory of Open Access Journals (DOAJ)...")
    doaj_paper = fetch_doaj_paper(title=title, doi=doi)
    progress.progress(30)

    api_status.text("Querying DataCite Infrastructure...")
    datacite_paper = fetch_datacite_paper(doi=doi)
    progress.progress(45)

    api_status.text("Querying PubMed / NCBI Entrez Engine...")
    pubmed_paper = fetch_pubmed_paper(title=title, doi=doi)
    progress.progress(60)

    api_status.text("Querying OpenCitations Infrastructure...")
    oc_data = fetch_open_citations(doi=doi)
    progress.progress(75)

    api_status.text("Querying ISSN International Centre & Journal Registries...")
    issn = pissn or eissn
    crossref_journal = fetch_crossref_journal(issn=issn, title=journal_title)
    doaj_journal = fetch_doaj_journal(issn=issn, title=journal_title)
    issn_portal = fetch_issn_portal(issn=issn)
    doi_resolver = fetch_doi_resolver(doi)
    progress.progress(90)

    api_status.text("Evaluating multi-registry consensus scoring...")

    api_results = {}
    if crossref_paper:
        api_results["Crossref"] = extract_from_crossref(crossref_paper["data"])
    if doaj_paper:
        api_results["DOAJ"] = extract_from_doaj(doaj_paper["data"])
    if datacite_paper:
        api_results["DataCite"] = extract_from_datacite(datacite_paper["data"])

    primary_record = None
    live_candidates = [(name, e) for name, e in api_results.items() if e]
    if live_candidates:
        if title:
            scored = [
                (strict_text_score(title, e.get("title", "")), name, e)
                for name, e in live_candidates
            ]
            scored.sort(key=lambda x: x[0], reverse=True)
            best_score, best_name, best_e = scored[0]
            if best_score >= THRESHOLD_MEDIUM:
                primary_record = dict(best_e)
                primary_record["source"] = best_name
                primary_record["title_match_score"] = best_score
        else:
            name, e = live_candidates[0]
            primary_record = dict(e)
            primary_record["source"] = name
            primary_record["title_match_score"] = None

    journal_data = None
    for src_name, src_data in [("Crossref Journal", crossref_journal), ("DOAJ Journal", doaj_journal)]:
        if src_data and src_data.get("data"):
            data = src_data["data"]
            try:
                if "message" in data or "container-title" in str(data):
                    msg = data if "title" in data else data.get("message", {})
                    titles = safe_get(msg, "title", default=[]) or safe_get(msg, "container-title", default=[])
                    found_title = titles[0] if titles else ""
                    issns = safe_get(msg, "ISSN", default=[])
                    publisher = safe_get(msg, "publisher", default="")
                else:
                    bib = data.get("bibjson", data)
                    found_title = safe_get(bib, "title", default="") or safe_get(bib, "journal", "title", default="")
                    issns = safe_get(bib, "identifier", default=[]) or safe_get(bib, "issns", default=[])
                    publisher = safe_get(bib, "publisher", default="")

                if journal_title and strict_text_score(journal_title, found_title) < THRESHOLD_MEDIUM:
                    continue

                found_pissn = found_eissn = ""
                for ident in issns:
                    if isinstance(ident, dict):
                        if ident.get("type") == "pissn":
                            found_pissn = ident.get("id", "")
                        elif ident.get("type") == "eissn":
                            found_eissn = ident.get("id", "")
                    elif isinstance(ident, str):
                        if not found_pissn:
                            found_pissn = ident
                        else:
                            found_eissn = ident

                issn_valid = bool(issn_portal and isinstance(issn_portal, dict) and issn_portal.get("data"))

                journal_data = {
                    "source": src_name, "title": found_title,
                    "pissn": found_pissn, "eissn": found_eissn,
                    "publisher": publisher, "issn_valid": issn_valid
                }
                break
            except Exception as e:
                st.warning(f"Journal metadata parsing error ({src_name}): {e}")
                continue

    user_inputs = {
        "Paper Title": title or "",
        "Journal Title": journal_title or "",
        "DOI": doi or "",
        "p-ISSN": pissn or "",
        "e-ISSN": eissn or "",
        "Volume": str(volume) if volume else "",
        "Issue": str(issue) if issue else "",
        "Year": str(year) if year else "",
        "Author": author or ""
    }

    match_results, confidence, field_sources, title_score = calculate_consensus_score(api_results, user_inputs)
    api_count = len(api_results)
    title_score = title_score if title_score is not None else 0

    rationale = ""

    if api_count == 0:
        overall_status = STATUS_NOT_FOUND
        confidence = 0
        rationale = "No registry returned a record resembling the submitted paper."
    elif title_score < THRESHOLD_MEDIUM:
        overall_status = STATUS_SUSPICIOUS
        confidence = min(confidence, max(title_score, 15.0))
        rationale = (
            f"Title match against registry records was only {title_score}%, "
            "below the threshold required to confirm this is the same paper "
            "as the one indexed under matching metadata."
        )
    elif confidence >= 90 and api_count >= 2 and title_score >= THRESHOLD_EXACT:
        overall_status = STATUS_VERIFIED
        rationale = f"Title, and a majority of supporting fields, matched independently across {api_count} registries."
    elif confidence >= 80 and api_count >= 2 and title_score >= THRESHOLD_HIGH:
        overall_status = STATUS_VERIFIED
        rationale = f"Strong title match ({title_score}%) corroborated by {api_count} registries."
    elif confidence >= 55 and title_score >= THRESHOLD_MEDIUM:
        overall_status = STATUS_PARTIAL
        rationale = f"Title match ({title_score}%) found, but supporting metadata only partially agrees across registries."
    else:
        overall_status = STATUS_SUSPICIOUS
        rationale = "Overall registry agreement was too low to confirm this record."

    doi_title_conflict = False
    if doi and doi_resolver and doi_resolver.get("data", {}).get("resolved"):
        doi_match = False
        title_match = False
        for api_name, extracted in api_results.items():
            if extracted and extracted.get("doi"):
                if exact_match(doi, extracted["doi"]) >= 98:
                    doi_match = True
                    if title and extracted.get("title"):
                        t_score = strict_text_score(title, extracted.get("title", ""))
                        if t_score >= THRESHOLD_HIGH:
                            title_match = True
                        elif t_score < THRESHOLD_MEDIUM:
                            doi_title_conflict = True
                    else:
                        title_match = True
                break
        if doi_match and title_match and confidence >= 70 and title_score >= THRESHOLD_HIGH:
            overall_status = STATUS_VERIFIED
            confidence = max(confidence, 98.0)
            rationale = "DOI resolves and independently matches the submitted title across registries."

    if doi_title_conflict:
        overall_status = STATUS_SUSPICIOUS
        confidence = min(confidence, 15.0)
        rationale = (
            "The submitted DOI resolves, but the title on file for that DOI in the "
            "registries does not match the submitted title. This paper appears to be "
            "citing an identifier that belongs to a different published work."
        )

    fields_checked = sum(1 for r in match_results if r["Status"] != "Not Provided")
    title_word_count = len(normalize_text(title).split()) if title else 0

    NON_PAPER_TYPES = {
        "entry-encyclopedia", "reference-entry", "entry", "component",
        "dataset", "peer-review", "grant", "book-part"
    }
    record_type = (primary_record or {}).get("type", "") if primary_record else ""
    type_flag = record_type in NON_PAPER_TYPES

    if type_flag:
        overall_status = STATUS_SUSPICIOUS
        confidence = min(confidence, 20.0)
        rationale = (
            f"The best-matching registry record is indexed as a '{record_type}' "
            "(e.g. a dictionary or reference-work entry), not a journal article, "
            "book chapter, thesis, or conference paper. A text match to that kind "
            "of record does not verify this as a genuine academic publication."
        )
    elif title_word_count and title_word_count < 3:
        if overall_status == STATUS_VERIFIED:
            overall_status = STATUS_PARTIAL
        confidence = min(confidence, 45.0)
        rationale += (
            f" Caution: the submitted title is only {title_word_count} word(s) long - "
            "short or generic titles can coincidentally match unrelated indexed "
            "records, so this cannot be treated as a reliable identification on "
            "its own. Add a DOI, journal, year, or author to strengthen the check."
        )
    elif fields_checked <= 1:
        if overall_status == STATUS_VERIFIED:
            overall_status = STATUS_PARTIAL
        confidence = min(confidence, 55.0)
        rationale += (
            " Caution: only the title could be checked against registries - no "
            "DOI, journal, year, or author was supplied to independently "
            "corroborate this specific record."
        )

    df = pd.DataFrame(match_results)

    if journal_data:
        journal_info_parts = [
            "**Journal Title:** " + str(journal_data.get('title', 'N/A')),
            "**Publisher:** " + str(journal_data.get('publisher', 'N/A')),
            "**ISSN Registration:** " + ('Confirmed via ISSN Portal' if journal_data.get('issn_valid') else 'Unconfirmed'),
            "**Primary Registry:** " + str(journal_data.get('source', 'N/A')),
        ]
        journal_info_text = "\n\n".join(journal_info_parts)
    else:
        journal_info_text = "No matching journal record found in public registries."

    api_coverage = []
    if crossref_paper: api_coverage.append("Crossref")
    if doaj_paper: api_coverage.append("DOAJ")
    if datacite_paper: api_coverage.append("DataCite")
    if pubmed_paper: api_coverage.append("PubMed")
    if oc_data: api_coverage.append("OpenCitations")
    if issn_portal: api_coverage.append("ISSN Portal")

    links_parts = []
    if doi:
        links_parts.append(f"- [DOI Permanent Link](https://doi.org/{doi})")
    if crossref_paper and crossref_paper.get("data"):
        url = safe_get(crossref_paper["data"], "URL", default="")
        if url:
            links_parts.append(f"- [Crossref Metadata Record]({url})")
    if pubmed_paper:
        pmid = safe_get(pubmed_paper["data"], "pmid", default="")
        if pmid:
            links_parts.append(f"- [PubMed Entry (PMID: {pmid})](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
    links_text = "\n".join(links_parts) if links_parts else "No direct links available."

    open_url = ""
    if crossref_paper:
        open_url = safe_get(crossref_paper["data"], "URL", default="")
    if not open_url and doi:
        open_url = f"https://doi.org/{doi}"

    progress.empty()
    api_status.empty()

    return (overall_status, confidence, df, journal_info_text, links_text,
            open_url, api_coverage, api_results, rationale, doi_title_conflict,
            primary_record)

# --- PDF Export Engine ---
class PDFReport(FPDF):
    def header(self):
        self.set_fill_color(95, 141, 120)       # sage
        self.rect(0, 0, 210, 7, "F")
        self.set_y(13)
        self.set_font("Times", "B", 15)
        self.set_text_color(63, 107, 89)
        self.cell(0, 8, "OFFICE OF RESEARCH, INNOVATION & COMMERCIALIZATION", ln=True, align="C")
        self.set_font("Times", "", 9.5)
        self.set_text_color(92, 103, 96)
        self.cell(0, 6, "Research Paper Verification & Cross-Registry Audit Report", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-16)
        self.set_draw_color(217, 222, 216)
        self.line(12, self.get_y(), 198, self.get_y())
        self.ln(2)
        self.set_font("Times", "I", 8)
        self.set_text_color(115, 123, 118)
        self.cell(0, 8, f"ORIC Research Verification System  |  Page {self.page_no()}", align="C")

    def section_title(self, title):
        self.set_font("Times", "B", 11)
        self.set_text_color(63, 107, 89)
        self.cell(0, 7, sanitize_for_pdf(title).upper(), ln=True)
        self.set_draw_color(190, 207, 196)
        self.line(12, self.get_y(), 198, self.get_y())
        self.ln(3)

    def body(self, text, size=9.5):
        self.set_font("Times", "", size)
        self.set_text_color(45, 55, 50)
        self.multi_cell(0, 5, sanitize_for_pdf(text))
        self.ln(2)


def sanitize_for_pdf(text):
    """Keep FPDF's built-in fonts safe for arbitrary registry/API text."""
    if text is None:
        return ""
    text = str(text)
    replacements = {
        "✅": "[VERIFIED]", "⚠️": "[PARTIAL]", "❌": "[SUSPICIOUS]",
        "🔍": "[NOT FOUND]", "🔗": "[LINK]", "📄": "[PDF]", "🏥": "[PUBMED]",
        "→": "->", "–": "-", "—": "-", "‘": "'", "’": "'", "“": '"',
        "”": '"', "…": "...", "•": "*", "·": "-", "\u00a0": " "
    }
    for uni, asc in replacements.items():
        text = text.replace(uni, asc)
    return text.encode("latin-1", "replace").decode("latin-1")


def _pdf_status_color(status):
    return {
        STATUS_VERIFIED: (63, 107, 89),
        STATUS_PARTIAL: (180, 122, 60),
        STATUS_SUSPICIOUS: (182, 91, 85),
        STATUS_NOT_FOUND: (100, 112, 105)
    }.get(status, (100, 112, 105))


def generate_pdf(status, confidence, df, journal_info, links, api_coverage, rationale,
                 submitted=None, primary_record=None, doi_title_conflict=False):
    """Return PDF bytes directly so Streamlit can download reliably."""
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Report identity strip
    pdf.set_fill_color(247, 241, 231)
    pdf.rect(12, 40, 186, 31, style="F", round_corners=True, corner_radius=3)
    pdf.set_xy(18, 45)
    pdf.set_font("Times", "B", 10)
    pdf.set_text_color(63, 107, 89)
    pdf.cell(37, 6, "REPORT STATUS")
    r, g, b = _pdf_status_color(status)
    pdf.set_text_color(r, g, b)
    pdf.set_font("Times", "B", 13)
    pdf.cell(55, 6, sanitize_for_pdf(status))
    pdf.set_font("Times", "", 9)
    pdf.set_text_color(70, 78, 73)
    pdf.cell(42, 6, "Confidence")
    pdf.set_font("Times", "B", 12)
    pdf.set_text_color(r, g, b)
    pdf.cell(30, 6, f"{confidence}%")
    pdf.set_font("Times", "", 8.5)
    pdf.set_text_color(90, 98, 93)
    pdf.ln(9)
    pdf.set_x(18)
    pdf.cell(0, 5, "Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    pdf.set_y(79)
    pdf.section_title("Audit Summary")
    pdf.body(
        f"Verification status: {status}\n"
        f"Consensus confidence score: {confidence}%\n"
        f"Registries consulted: {', '.join(api_coverage) if api_coverage else 'None'}\n"
        f"Verification rationale: {rationale}"
    )

    if doi_title_conflict:
        pdf.set_fill_color(251, 236, 233)
        pdf.set_text_color(113, 63, 58)
        pdf.set_font("Times", "B", 9)
        pdf.multi_cell(0, 6, sanitize_for_pdf(
            "DOI / title conflict detected: the supplied DOI resolves to a registered publication "
            "whose title does not match the submitted title."
        ), fill=True)
        pdf.ln(3)

    if submitted:
        pdf.section_title("Submitted Paper Metadata")
        rows = [
            ("Paper Title", submitted.get("title", "")),
            ("Journal / Venue", submitted.get("journal", "")),
            ("DOI", submitted.get("doi", "")),
            ("Print ISSN", submitted.get("pissn", "")),
            ("Online ISSN", submitted.get("eissn", "")),
            ("Volume", submitted.get("volume", "")),
            ("Issue", submitted.get("issue", "")),
            ("Year", submitted.get("year", "")),
            ("Author", submitted.get("author", "")),
        ]
        for label, value in rows:
            if value:
                pdf.set_font("Times", "B", 9)
                pdf.set_text_color(63, 107, 89)
                pdf.cell(36, 5, sanitize_for_pdf(label) + ":")
                pdf.set_font("Times", "", 9)
                pdf.set_text_color(45, 55, 50)
                pdf.multi_cell(0, 5, sanitize_for_pdf(value))
                pdf.ln(.5)

    if primary_record:
        pdf.ln(2)
        pdf.section_title("Registry-Discovered Record")
        record_rows = [
            ("Source", primary_record.get("source", "")),
            ("Title", primary_record.get("title", "")),
            ("Authors", primary_record.get("authors", "")),
            ("Journal", primary_record.get("journal", "")),
            ("Year", primary_record.get("year", "")),
            ("Volume / Issue", ", ".join(filter(None, [
                f"Vol. {primary_record.get('volume')}" if primary_record.get("volume") else "",
                f"Issue {primary_record.get('issue')}" if primary_record.get("issue") else ""
            ]))),
            ("DOI", primary_record.get("doi", "")),
            ("ISSN", ", ".join(filter(None, [
                primary_record.get("pissn", ""),
                primary_record.get("eissn", "")
            ]))),
        ]
        for label, value in record_rows:
            if value:
                pdf.set_font("Times", "B", 9)
                pdf.set_text_color(63, 107, 89)
                pdf.cell(36, 5, sanitize_for_pdf(label) + ":")
                pdf.set_font("Times", "", 9)
                pdf.set_text_color(45, 55, 50)
                pdf.multi_cell(0, 5, sanitize_for_pdf(value))
                pdf.ln(.5)

    pdf.ln(3)
    pdf.section_title("Bibliographic Field Comparison")
    col_widths = [30, 51, 51, 25, 20]
    headers = ["Field", "Submitted", "Registry Match", "Status", "Score"]

    pdf.set_fill_color(95, 141, 120)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Times", "B", 8)
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 7, sanitize_for_pdf(h), border=1, fill=True, align="C")
    pdf.ln()

    for _, row in df.iterrows():
        values = [
            row.get("Field", ""),
            row.get("Submitted Data", ""),
            row.get("Registry Match", ""),
            row.get("Status", ""),
            row.get("Score", ""),
        ]
        pdf.set_font("Times", "", 7.5)
        pdf.set_text_color(45, 55, 50)
        # Multi-line rows: use a compact one-line textual audit entry.
        line = " | ".join(sanitize_for_pdf(v) for v in values)
        pdf.multi_cell(0, 5, line, border="B")
        pdf.ln(.5)

    pdf.ln(2)
    pdf.section_title("Journal & Publisher Metadata")
    pdf.body(journal_info.replace("**", "").replace("\n\n", "\n"))

    pdf.section_title("Indexed Links & Sources")
    pdf.body(links.replace("**", ""))

    pdf.section_title("Institutional Disclaimer")
    pdf.body(
        "This verification document is auto-generated by cross-referencing submitted paper metadata "
        "against indexed academic registries including Crossref, DOAJ, DataCite, PubMed, OpenCitations "
        "and the ISSN Portal. A successful match indicates that matching metadata was found in the "
        "consulted registries. Formal publication, authorship, integrity and institutional compliance "
        "decisions remain subject to ORIC administrative policies."
    )

    return bytes(pdf.output())

# ============================================================
# --- INSTITUTIONAL UI LAYOUT ---
# ============================================================

st.markdown("""
<div class="inst-header">
    <div class="sub-caption">OFFICE OF RESEARCH, INNOVATION AND COMMERCIALIZATION (ORIC)</div>
    <h1>Research Paper Verification Portal</h1>
    <p>Cross-checks submitted paper metadata against Crossref, DOAJ, DataCite, PubMed, OpenCitations
    and the ISSN Portal, and flags submissions where the title itself cannot be confirmed - even if
    other details happen to line up.</p>
</div>
""", unsafe_allow_html=True)

if "results" not in st.session_state:
    st.session_state.results = None
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

for key in ["example_title", "example_journal", "example_doi", "example_volume", "example_year", "example_author"]:
    if key not in st.session_state:
        st.session_state[key] = ""

col_left, col_right = st.columns([11, 13], gap="medium")

with col_left:
    st.markdown("""
    <div class="panel-card">
        <div class="panel-header">Paper Submission Details</div>
    """, unsafe_allow_html=True)

    inp_title = st.text_area(
        "Paper Title *",
        value=st.session_state.get("example_title", ""),
        placeholder="Enter full article title...",
        height=75
    )

    inp_journal = st.text_input(
        "Journal / Venue Title *",
        value=st.session_state.get("example_journal", ""),
        placeholder="e.g., Nature Communications"
    )

    st.markdown('<div class="field-group-label">Digital &amp; ISSN identifiers</div>', unsafe_allow_html=True)

    inp_doi = st.text_input(
        "Digital Object Identifier (DOI)",
        value=st.session_state.get("example_doi", ""),
        placeholder="e.g., 10.1038/s41467-020-12345-6"
    )

    col_issn1, col_issn2 = st.columns(2)
    with col_issn1:
        inp_pissn = st.text_input("Print ISSN (p-ISSN)", placeholder="1234-5678")
    with col_issn2:
        inp_eissn = st.text_input("Online ISSN (e-ISSN)", placeholder="1234-5678")

    st.markdown('<div class="field-group-label">Volume &amp; publication metadata</div>', unsafe_allow_html=True)

    col_vol, col_iss = st.columns(2)
    with col_vol:
        inp_volume = st.text_input(
            "Volume",
            value=st.session_state.get("example_volume", ""),
            placeholder="e.g., 12"
        )
    with col_iss:
        inp_issue = st.text_input("Issue Number", placeholder="e.g., 4")

    col_yr, col_au = st.columns([1, 2])
    with col_yr:
        inp_year = st.text_input(
            "Year *",
            value=st.session_state.get("example_year", ""),
            placeholder="YYYY"
        )
    with col_au:
        inp_author = st.text_input(
            "Lead / Corresponding Author",
            value=st.session_state.get("example_author", ""),
            placeholder="e.g., J. Smith"
        )

    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
    with col_btn1:
        btn_verify = st.button("Run Audit Check", type="primary", use_container_width=True)
    with col_btn2:
        btn_example = st.button("Load Sample", use_container_width=True)
    with col_btn3:
        btn_clear = st.button("Clear", use_container_width=True)

    st.markdown("""
    <div class="ledger-note">
        <strong>Note on verification:</strong> the title is checked independently of every other
        field. A paper cannot be marked Verified - or even Partial Match - on the strength of a
        matching year, volume, or journal alone; the submitted title itself must be found in at
        least one registry.
    </div>
    </div>
    """, unsafe_allow_html=True)

    if btn_example:
        st.session_state.example_title = "Attention Is All You Need"
        st.session_state.example_journal = "Advances in Neural Information Processing Systems"
        st.session_state.example_doi = "10.5555/3295222.3295349"
        st.session_state.example_volume = "30"
        st.session_state.example_year = "2017"
        st.session_state.example_author = "Ashish Vaswani"
        st.rerun()

    if btn_clear:
        st.session_state.results = None
        st.session_state.pdf_bytes = None
        for key in ["example_title", "example_journal", "example_doi", "example_volume", "example_year", "example_author"]:
            st.session_state[key] = ""
        st.rerun()

with col_right:
    st.markdown("""
    <div class="panel-card">
        <div class="panel-header">Verification Audit Results</div>
    """, unsafe_allow_html=True)

    if btn_verify:
        if not inp_title and not inp_doi:
            st.error("Missing required input: Please specify at least a Paper Title or DOI.")
        else:
            results = verify_paper_v3(
                inp_title, inp_journal, inp_doi,
                inp_pissn, inp_eissn, inp_volume,
                inp_issue, inp_year, inp_author
            )
            st.session_state.results = results

    if st.session_state.results:
        (overall_status, confidence, df, journal_info_text, links_text,
         open_url, api_coverage, api_results, rationale, doi_title_conflict,
         primary_record) = st.session_state.results

        status_config = {
            STATUS_VERIFIED: "#2e8b74",
            STATUS_PARTIAL: "#b06000",
            STATUS_SUSPICIOUS: "#6b1d24",
            STATUS_NOT_FOUND: "#52606d"
        }
        seal_color = status_config.get(overall_status, "#52606d")

        chips_html = "".join([f'<span class="registry-chip">{api}</span>' for api in api_coverage]) or \
            '<span class="registry-chip">none returned a match</span>'
        st.markdown(f"""
        <div style="margin-bottom: 12px; font-size: 0.82rem; color: #3d4852;">
            <strong>Indexed registries consulted:</strong><br/>{chips_html}
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="seal-wrap" style="--seal-color: {seal_color};">
            <div class="seal-box">{overall_status.upper()}</div>
            <div class="seal-meta">
                <div class="conf-line">Verification confidence: <span class="conf-value">{confidence}%</span></div>
                <div class="rationale">{rationale}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if doi_title_conflict:
            st.markdown(f"""
            <div class="ledger-note conflict">
                DOI / title conflict: the DOI resolves to a registered publication whose title
                does not match the submitted title. Treat this submission as suspect until the
                discrepancy is explained.
            </div>
            """, unsafe_allow_html=True)
        elif confidence >= 90 and overall_status == STATUS_VERIFIED:
            st.markdown("""
            <div class="ledger-note consensus">
                High multi-registry consensus: the bibliographic metadata submitted matches
                indexed records across independent academic repositories.
            </div>
            """, unsafe_allow_html=True)

        if primary_record:
            match_note = (
                f" &middot; title match {primary_record['title_match_score']}%"
                if primary_record.get("title_match_score") is not None else ""
            )
            authors_line = primary_record.get("authors") or "Not listed"
            journal_line = primary_record.get("journal") or "Not listed"
            year_line = primary_record.get("year") or "Not listed"
            vol_iss = ", ".join(filter(None, [
                f"Vol. {primary_record['volume']}" if primary_record.get("volume") else "",
                f"Issue {primary_record['issue']}" if primary_record.get("issue") else "",
            ])) or "Not listed"
            doi_line = f'<span class="id-code">{primary_record["doi"]}</span>' if primary_record.get("doi") else "Not listed"
            issn_line = ", ".join(filter(None, [primary_record.get("pissn", ""), primary_record.get("eissn", "")])) or "Not listed"

            st.markdown(f"""
            <div class="panel-header" style="font-size:1rem; margin-top: 4px;">
                Registry-Discovered Record
                <span style="font-family:'IBM Plex Sans',sans-serif; font-weight:400; font-size:0.75rem; color:#6b1d24; text-transform:none; letter-spacing:0;">
                    &nbsp;&mdash; via {primary_record.get('source','')}{match_note}
                </span>
            </div>
            <div style="font-size:0.88rem; line-height:1.7; color:#2c3e50;">
                <strong>Title:</strong> {primary_record.get('title') or 'Not listed'}<br/>
                <strong>Authors:</strong> {authors_line}<br/>
                <strong>Journal:</strong> {journal_line}<br/>
                <strong>Year:</strong> {year_line} &nbsp;&middot;&nbsp; <strong>{vol_iss}</strong><br/>
                <strong>DOI:</strong> {doi_line}<br/>
                <strong>ISSN:</strong> {issn_line}
            </div>
            <div class="ledger-note" style="margin-top:12px;">
                This is what the registries hold on file for the best-matching record - not
                limited to the fields you submitted. Compare it against the table below to see
                which of your submitted claims specifically matched or didn't.
            </div>
            """, unsafe_allow_html=True)

        st.markdown("##### Bibliographic Field Comparison")
        st.caption("Each field is checked independently. A field the registries could not confirm is marked \"Not Found\" - it does not borrow confidence from fields that did match.")
        st.dataframe(
            df,
            column_config={
                "Field": st.column_config.TextColumn("Field Name", width="medium"),
                "Submitted Data": st.column_config.TextColumn("Submitted", width="large"),
                "Registry Match": st.column_config.TextColumn("Registry Record", width="large"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Score": st.column_config.TextColumn("Match %", width="small"),
                "Sources": st.column_config.TextColumn("Matched In", width="medium"),
            },
            use_container_width=True,
            hide_index=True
        )

        col_j, col_l = st.columns(2)
        with col_j:
            st.markdown("**Journal & Publisher Metadata**")
            st.markdown(journal_info_text)

        with col_l:
            st.markdown("**Indexed Links & Sources**")
            st.markdown(links_text)

        st.markdown("<hr style='margin: 16px 0; border: 0; border-top: 1px solid #d8dee6;'/>", unsafe_allow_html=True)

        with st.expander("Inspect raw registry responses"):
            for api_name, data in api_results.items():
                st.caption(f"Registry: {api_name}")
                st.json(data)

        col_a, col_b = st.columns(2)
        with col_a:
            if open_url:
                st.link_button("View Article via Resolver", open_url, use_container_width=True)

        with col_b:
            if st.button("Create Verification PDF", use_container_width=True):
                try:
                    submitted_meta = {
                        "title": inp_title,
                        "journal": inp_journal,
                        "doi": inp_doi,
                        "pissn": inp_pissn,
                        "eissn": inp_eissn,
                        "volume": inp_volume,
                        "issue": inp_issue,
                        "year": inp_year,
                        "author": inp_author,
                    }
                    with st.spinner("Preparing official ORIC audit report..."):
                        st.session_state.pdf_bytes = generate_pdf(
                            overall_status, confidence, df, journal_info_text,
                            links_text, api_coverage, rationale,
                            submitted=submitted_meta,
                            primary_record=primary_record,
                            doi_title_conflict=doi_title_conflict
                        )
                    st.success("PDF report is ready.")
                except Exception as e:
                    st.session_state.pdf_bytes = None
                    st.error(f"PDF generation failed: {e}")

        if st.session_state.pdf_bytes:
            st.download_button(
                label="Download Official Verification Report",
                data=st.session_state.pdf_bytes,
                file_name=f"ORIC_Verification_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
    else:
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px; color:#66736D; background: #F1F6F2; border: 1px dashed #b9c2bb;">
            <div style="font-size: 0.95rem; font-family: 'Source Serif 4', Georgia, serif; color:#3F6B59;">
                Awaiting Paper Metadata
            </div>
            <div style="font-size: 0.82rem; margin-top: 6px;">
                Enter details on the left panel and click <strong>Run Audit Check</strong> to initiate cross-verification.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align:center; color:#66736D; font-size:0.78rem; margin-top: 30px;">
    Office of Research, Innovation and Commercialization (ORIC) &middot; Official Verification Portal<br>
    Connected Registries: Crossref &middot; DOAJ &middot; DataCite &middot; PubMed &middot; OpenCitations &middot; ISSN Portal
</div>
""", unsafe_allow_html=True)
