import os
import zipfile
import urllib.request
import streamlit as st
import streamlit.components.v1 as components
import chromadb
from chromadb.utils import embedding_functions

# --- AUTOMATISK NEDLADDNING AV DATABAS FRÅN DROPBOX (FÖR MOLNET) ---
DB_DIR = "./urplay_chroma_db"
ZIP_FILE = "urplay_chroma_db.zip"
DB_DOWNLOAD_URL = "https://www.dropbox.com/scl/fi/7yisqlz86rzb1cmj0h3sr/urplay_chroma_db.zip?rlkey=ama039tkcv8ej8tq7dnxauq6i&dl=1"

if not os.path.exists(DB_DIR):
    st.info("🚀 Första uppstart i molnet: Laddar ner och packar upp UR Play-databasen (125 MB) från Dropbox... Detta kan ta en liten stund.")
    
    urllib.request.urlretrieve(DB_DOWNLOAD_URL, ZIP_FILE)
    
    with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
        zip_ref.extractall(".")
        
    if os.path.exists(ZIP_FILE):
        os.remove(ZIP_FILE)
    
    st.success("Databasen är klar! Startar sökgränssnittet...")
    st.rerun()
# -----------------------------------------------------------------

# Sidkonfiguration
st.set_page_config(
    page_title="UR Play AI Search",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# JavaScript för att tvinga bort webbläsarens autocomplete-rutor på alla textfält
st.markdown("""
<script>
    const observer = new MutationObserver(() => {
        document.querySelectorAll('input[type="text"]').forEach(input => {
            input.setAttribute('autocomplete', 'off');
            input.setAttribute('autocorrect', 'off');
            input.setAttribute('autocapitalize', 'off');
            input.setAttribute('spellcheck', 'false');
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# Custom CSS för Streamlit-gränssnittet
st.markdown("""
<style>
    .stApp {
        background-color: #06080d;
        color: #e6edf3;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
        pointer-events: none;
    }
    
    header[data-testid="stHeader"] * {
        pointer-events: auto;
    }

    .brand-header {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 12px;
        padding: 3rem 1rem 1.5rem 1rem;
        margin-bottom: 0.5rem;
    }

    .ur-logo-row {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .ur-logo {
        background: linear-gradient(135deg, #0055aa 0%, #003d7a 100%);
        color: #ffffff;
        font-weight: 900;
        font-size: 3rem;
        padding: 8px 26px;
        border-radius: 14px;
        letter-spacing: -0.05em;
        box-shadow: 0 10px 30px rgba(0, 85, 170, 0.55), inset 0 1px 1px rgba(255, 255, 255, 0.4);
    }

    .ai-badge-title {
        font-size: 3.5rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        background: linear-gradient(90deg, #ffffff 0%, #a78bfa 35%, #60a5fa 70%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 10px 35px rgba(167, 139, 250, 0.25);
    }

    .header-subtitle {
        color: #8b949e;
        font-size: 1.15rem;
        font-weight: 400;
        margin-top: -6px;
    }

    .button-container {
        display: flex;
        justify-content: center;
        gap: 12px;
        max-width: 600px;
        margin: 0 auto 1.5rem auto;
    }

    div.stButton > button {
        background-color: rgba(255, 255, 255, 0.04) !important;
        color: #98a6b5 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 30px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.65rem 1.6rem !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
    }

    div.stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.12) !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.35) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0055aa 0%, #1f6feb 100%) !important;
        color: #ffffff !important;
        border: 1px solid #58a6ff !important;
        box-shadow: 0 0 20px rgba(31, 111, 235, 0.5) !important;
    }

    .stTextInput input {
        background-color: #0d111a !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 24px !important;
        padding: 16px 24px !important;
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        text-align: center !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6) !important;
        transition: all 0.4s ease !important;
    }

    .stTextInput input:focus {
        border-color: #a78bfa !important;
        box-shadow: 0 0 25px rgba(167, 139, 250, 0.4) !important;
        background-color: #111622 !important;
    }

    div[data-testid="stSidebar"] {
        background-color: #0d111a;
        border-right: 1px solid #1f2430;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_db():
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    client = chromadb.PersistentClient(path="./urplay_chroma_db")
    return client.get_collection(name="urplay_programs", embedding_function=ef)

# Session states (ökade initiala träffar till 18 för ett mer generöst flöde)
if "kind_type" not in st.session_state:
    st.session_state.kind_type = "Båda"

if "visible_count" not in st.session_state:
    st.session_state.visible_count = 18

if "search_query" not in st.session_state:
    st.session_state.search_query = "matematik på teckenspråk"

# Hämta söksträng från URL om den finns vid start
query_params = st.query_params
if "q" in query_params:
    st.session_state.search_query = query_params["q"]

# Header
st.markdown("""
<div class="brand-header">
    <div class="ur-logo-row">
        <div class="ur-logo">UR</div>
        <div class="ai-badge-title">PLAY AI SEARCH</div>
    </div>
    <div class="header-subtitle">Semantisk AI-sökning bland 22 000+ serier och avsnitt</div>
</div>
""", unsafe_allow_html=True)

# Snabbknappar
st.markdown('<div class="button-container">', unsafe_allow_html=True)
btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])

with btn_col1:
    if st.button("📁 Enbart Program", use_container_width=True, type="primary" if st.session_state.kind_type == "Program" else "secondary"):
        st.session_state.kind_type = "Program"
        st.session_state.visible_count = 18
        st.rerun()

with btn_col2:
    if st.button("📺 Enbart Avsnitt", use_container_width=True, type="primary" if st.session_state.kind_type == "Avsnitt" else "secondary"):
        st.session_state.kind_type = "Avsnitt"
        st.session_state.visible_count = 18
        st.rerun()

with btn_col3:
    if st.button("🎬 Båda", use_container_width=True, type="primary" if st.session_state.kind_type == "Båda" else "secondary"):
        st.session_state.kind_type = "Båda"
        st.session_state.visible_count = 18
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Centrerat sökfält utan helsidesomladdning
col_space1, col_search, col_space2 = st.columns([1, 2, 1])
with col_search:
    query = st.text_input(
        "Sökfält",
        value=st.session_state.search_query,
        placeholder="🔍 Sök vad du vill titta på...",
        label_visibility="collapsed"
    )

if query != st.session_state.search_query:
    st.session_state.search_query = query
    st.query_params["q"] = query

with st.sidebar:
    st.markdown("### 🎛️ Inställningar")
    only_sign_language = st.checkbox("🤟 Enbart teckenspråk / TAKK", value=False)

if query:
    try:
        collection = load_db()
        query_lower = query.lower()
        
        # Speciella språkhanteringar för att inte drunkna i enbart språkkategorin (t.ex. "matematik på finska")
        language_mappings = {
            "finska": ["finska", "suomi"],
            "finskt": ["finska", "suomi"],
            "meänkieli": ["meänkieli"],
            "samiska": ["samiska", "nordsamiska"],
            "romani": ["romani"],
            "jiddisch": ["jiddisch"]
        }
        
        active_language_terms = []
        for lang_key, terms in language_mappings.items():
            if lang_key in query_lower:
                active_language_terms.extend(terms)

        sign_terms = ["teckenspråk", "teckenspråkstolkad", "takk", "tecken som stöd"]
        is_sign_search = any(term in query_lower for term in sign_terms) or only_sign_language

        # Om sökningen är typ "ämne + på + språk", se till att söktexten fokuserar på kärnämnet
        if active_language_terms and not is_sign_search:
            clean_query = query_lower
            for lang_key in language_mappings.keys():
                clean_query = clean_query.replace(lang_key, "")
            clean_query = clean_query.replace("på", "").replace("i", "").strip()
            # Om rensningen lämnar kvar något bra (t.ex. "matematik"), prioritera det men behåll språkvikten
            search_text = clean_query if len(clean_query) > 2 else query
        elif is_sign_search:
            clean_query = query_lower
            for term in sign_terms:
                clean_query = clean_query.replace(term, "")
            clean_query = clean_query.replace("på", "").strip()
            search_text = clean_query if clean_query else query
        else:
            search_text = query

        # Höjt hämtningsfönster från 300 till 600 för att få bredare träffunderlag
        fetch_limit = 600
        results = collection.query(query_texts=[search_text], n_results=fetch_limit)

        all_matching_results = []
        query_words = [w.lower() for w in search_text.split() if len(w) > 2]
        
        if results and "ids" in results and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                meta = results["metadatas"][0][i]
                doc = results["documents"][0][i]
                dist = results["distances"][0][i]
                base_match_pct = round(max(0, (1 - dist) * 100), 1)
                
                title_lower = str(meta.get("title", "")).lower()
                series_lower = str(meta.get("series_title", "")).lower()
                doc_lower = str(doc).lower()
                combined_text = f"{title_lower} {series_lower} {doc_lower}"
                
                # Filterkontroll för teckenspråk
                is_sign_item = meta.get("is_sign_language") or any(t in combined_text for t in sign_terms)
                if is_sign_search and not is_sign_item and not only_sign_language:
                    continue

                # Filterkontroll för språk om användaren söker specifikt på språk (t.ex. finska)
                if active_language_terms:
                    has_lang = any(l_term in combined_text for l_term in active_language_terms)
                    # Om sökningen gällde ett ämne på ett språk, kräv inte hundraprocentig exakt match i språkkoden om ämnet är klockrent,
                    # men ge dem en ordentlig boost om språket matchar, och undvik helt orelaterat brus.
                    if not has_lang and not any(qw in combined_text for qw in query_words):
                        continue

                # Smart sökordsboost
                boost = 0
                for qw in query_words:
                    if qw in title_lower:
                        boost += 35
                    elif qw in series_lower:
                        boost += 25
                    elif qw in doc_lower:
                        boost += 8

                # Om språket matchar vid en språksökning, ge extra kärleksboost
                if active_language_terms and any(l_term in combined_text for l_term in active_language_terms):
                    boost += 20

                # Om sökordet innehåller specifika ämnen som "saga/sagor", straffa om det inte ens nämns i texten
                if any(w in query_lower for w in ["saga", "sagor", "berättelse"]):
                    if not any(w in combined_text for w in ["saga", "sagor", "berättelse"]):
                        base_match_pct *= 0.2
                
                match_pct = min(100.0, base_match_pct + boost)
                
                kind_str = str(meta.get("kind", "")).lower()
                url_str = str(meta.get("url", "")).lower()
                
                is_episode = (kind_str == "avsnitt") or ("/program/" in url_str) or bool(meta.get("series_title"))
                
                if st.session_state.kind_type == "Program" and is_episode:
                    continue
                if st.session_state.kind_type == "Avsnitt" and not is_episode:
                    continue
                    
                all_matching_results.append({
                    "meta": meta,
                    "doc": doc,
                    "match_pct": match_pct,
                    "is_episode": is_episode,
                    "is_sign": is_sign_item
                })
                
        # Sortera efter matchningsprocent
        all_matching_results.sort(key=lambda x: x["match_pct"], reverse=True)
                
        visible_items = all_matching_results[:st.session_state.visible_count]
        
        st.markdown(f"##### Visar {len(visible_items)} av {len(all_matching_results)} träffar ({st.session_state.kind_type})")
        
        if not visible_items:
            st.info(f"Inga resultat hittades för '{st.session_state.kind_type}'. Prova att klicka på 'Båda' eller bredda sökordet.")

        cards_html_list = []
        for item in visible_items:
            meta = item["meta"]
            doc = item["doc"]
            match_pct = item["match_pct"]
            is_episode = item["is_episode"]
            is_sign = item["is_sign"]
            
            raw_id = str(meta.get("id", ""))
            numeric_id = raw_id.split("-")[0] if "-" in raw_id else raw_id
            
            image_url = f"https://assets.ur.se/id/{numeric_id}/images/1_xl.jpg" if numeric_id else ""
            
            badges = ""
            if is_episode:
                badges += '<span class="badge badge-episode">📺 AVSNITT</span>'
            else:
                badges += '<span class="badge badge-program">📁 SERIE / PROGRAM</span>'
            
            if is_sign:
                badges += '<span class="badge badge-sign">🤟 TECKEN / TAKK</span>'
            
            series_html = f'<div class="series-name">Del av: {meta["series_title"]}</div>' if meta.get("series_title") else '<div class="series-name">&nbsp;</div>'
            image_html = f'<div class="card-image-container"><img src="{image_url}" class="card-image" alt="{meta["title"]}" onerror="this.parentNode.style.display=\'none\';"></div>' if image_url else ""

            card_single = (
                f'<div class="media-card">'
                f'<div>'
                f'{image_html}'
                f'<div class="badge-bar">{badges}</div>'
                f'<div class="card-title">{meta["title"]}</div>'
                f'{series_html}'
                f'<div class="card-desc">{doc}</div>'
                f'</div>'
                f'<div>'
                f'<div class="relevance-box">'
                f'<span style="font-size:0.8rem; color:#8b949e;">AI Matchning</span>'
                f'<span class="relevance-score">⚡ {match_pct}%</span>'
                f'</div>'
                f'<a href="{meta["url"]}" target="_blank" class="play-button">▶ Titta på UR Play</a>'
                f'</div>'
                f'</div>'
            )
            cards_html_list.append(card_single)

        component_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }}
            body {{
                background-color: transparent;
                color: #e6edf3;
                padding: 10px 5px 30px 5px;
            }}
            .cards-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 24px;
            }}
            @media (max-width: 992px) {{
                .cards-grid {{
                    grid-template-columns: repeat(1, 1fr);
                }}
            }}
            .media-card {{
                background: #10141d;
                border: 1px solid #1f2430;
                border-radius: 16px;
                padding: 18px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                transition: opacity 0.3s ease, filter 0.3s ease, background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
                box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
                opacity: 1;
                filter: brightness(100%);
            }}
            .cards-grid:hover .media-card {{
                opacity: 0.5;
                filter: brightness(70%);
            }}
            .cards-grid .media-card:hover {{
                opacity: 1 !important;
                filter: brightness(108%) !important;
                border-color: rgba(88, 166, 255, 0.4);
                background: #131926;
                box-shadow: 0 12px 30px rgba(0, 0, 0, 0.6), 0 0 20px rgba(88, 166, 255, 0.15);
            }}
            .card-image-container {{
                width: 100%;
                height: 220px;
                border-radius: 12px;
                margin-bottom: 24px;
                background: transparent;
                perspective: 1000px;
            }}
            .card-image {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                border-radius: 12px;
                display: block;
                will-change: transform;
                transition: transform 0.1s ease-out;
                -webkit-box-reflect: below 0px linear-gradient(to bottom, rgba(255,255,255,0.25) 0%, rgba(255,255,255,0) 70%);
            }}
            .badge-bar {{
                display: flex;
                gap: 6px;
                margin-bottom: 10px;
                margin-top: 10px;
                flex-wrap: wrap;
            }}
            .badge {{
                font-size: 0.7rem;
                font-weight: 700;
                text-transform: uppercase;
                padding: 4px 10px;
                border-radius: 20px;
                letter-spacing: 0.04em;
            }}
            .badge-episode {{
                background: rgba(96, 165, 250, 0.15);
                color: #60a5fa;
                border: 1px solid rgba(96, 165, 250, 0.3);
            }}
            .badge-program {{
                background: rgba(52, 211, 153, 0.15);
                color: #34d399;
                border: 1px solid rgba(52, 211, 153, 0.3);
            }}
            .badge-sign {{
                background: rgba(251, 191, 36, 0.15);
                color: #fbbf24;
                border: 1px solid rgba(251, 191, 36, 0.3);
            }}
            .card-title {{
                font-size: 1.25rem;
                font-weight: 700;
                color: #f0f6fc;
                margin-bottom: 4px;
                line-height: 1.3;
            }}
            .series-name {{
                color: #8b949e;
                font-size: 0.88rem;
                font-weight: 500;
                margin-bottom: 12px;
            }}
            .card-desc {{
                color: #8b949e;
                font-size: 0.9rem;
                line-height: 1.45;
                margin-bottom: 16px;
                display: -webkit-box;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }}
            .relevance-box {{
                background: rgba(255, 255, 255, 0.03);
                border-radius: 8px;
                padding: 8px 12px;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            .relevance-score {{
                font-size: 0.85rem;
                font-weight: 700;
                color: #58a6ff;
            }}
            .play-button {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                width: 100%;
                background: linear-gradient(90deg, #0055aa 0%, #1f6feb 100%);
                color: #ffffff !important;
                font-weight: 600;
                font-size: 0.95rem;
                padding: 11px 16px;
                border-radius: 8px;
                text-decoration: none !important;
                transition: all 0.2s ease;
            }}
            .play-button:hover {{
                background: linear-gradient(90deg, #1f6feb 100%, #388bfd 100%);
                transform: scale(1.02);
            }}
        </style>
        </head>
        <body>
            <div class="cards-grid">
                {"".join(cards_html_list)}
            </div>

            <script>
                document.querySelectorAll('.card-image-container').forEach(container => {{
                    const img = container.querySelector('.card-image');
                    if (!img) return;

                    container.addEventListener('mousemove', (e) => {{
                        const rect = container.getBoundingClientRect();
                        const x = e.clientX - rect.left;
                        const y = e.clientY - rect.top;
                        
                        const centerX = rect.width / 2;
                        const centerY = rect.height / 2;

                        const rotateX = -((y - centerY) / centerY) * 8;
                        const rotateY = ((x - centerX) / centerX) * 8;

                        img.style.transform = `scale(1.04) rotateX(${{rotateX}}deg) rotateY(${{rotateY}}deg)`;
                        img.style.transition = 'transform 0.05s ease-out';
                    }});

                    container.addEventListener('mouseleave', () => {{
                        img.style.transform = 'scale(1) rotateX(0deg) rotateY(0deg)';
                        img.style.transition = 'transform 0.5s ease';
                    }});
                }});
            </script>
        </body>
        </html>
        """

        rows = (len(visible_items) + 2) // 3
        calculated_height = max(600, rows * 560 + 40)
        
        components.html(component_html, height=calculated_height, scrolling=False)

        if len(visible_items) < len(all_matching_results):
            st.write("")
            load_col1, load_col2, load_col3 = st.columns([2, 2, 2])
            with load_col2:
                if st.button("➕ Visa fler resultat", use_container_width=True):
                    st.session_state.visible_count += 18
                    st.rerun()

    except Exception as e:
        st.error(f"Ett fel uppstod vid sökningen: {e}")