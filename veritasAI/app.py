import sys
import streamlit as st
from citation_service import process_citation_form
from text_pipeline import run_text_pipeline
from pdf_pipeline import verify_pdf_references

st.set_page_config(layout="wide", page_title="VeritasAI")

# ---------------- PAGE STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "landing"

# ---------------- GLOBAL CSS ----------------
st.markdown("""
<style>
    .stApp {
        background: #06070a;
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }
    /* Hero section */
    .hero {
        text-align: center;
        padding-top: 80px;
    }
    .hero h1 {
        font-size: 80px;
        font-weight: 800;
        margin-bottom: 0;
        color: #ffffff;
    }
    .hero h2 {
        font-size: 48px;
        font-weight: 600;
        margin-top: 0;
        color: #ffffff;
    }
    .accent {
        color: #00e5a0;
    }
    .hero p {
        color: #d1d5db; /* lighter gray for better readability */
        font-size: 20px;
        max-width: 600px;
        margin: 20px auto;
        line-height: 1.6;
    }
    .beta-badge {
        display: inline-block;
        background: #1e2028;
        color: #00e5a0;
        padding: 8px 20px;
        border-radius: 40px;
        font-size: 16px;
        font-weight: 600;
        border: 1px solid #30363d;
        margin-top: 20px;
    }
    .metric-card {
        background: #111318;
        padding: 30px;
        border-radius: 12px;
        border: 1px solid #1e2028;
        text-align: center;
    }
    .metric-card h3 {
        font-size: 48px;
        margin: 0;
        color: #00e5a0;
        font-weight: 700;
    }
    .metric-card p {
        color: #d1d5db;
        margin: 0;
        font-size: 18px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .layer-card {
        background: #111318;
        padding: 30px;
        border-radius: 12px;
        border: 1px solid #1e2028;
        height: 100%;
    }
    .layer-card h4 {
        color: #00e5a0;
        font-size: 24px;
        margin-top: 0;
        font-weight: 600;
    }
    .layer-card p {
        color: #d1d5db;
        font-size: 16px;
        line-height: 1.6;
    }
    /* Tool page inputs */
    .stTextInput > div > div > input, .stTextArea textarea {
        background: #161820;
        color: white;
        border-radius: 8px;
        border: 1px solid #30363d;
        font-size: 16px;
    }
    /* Ensure placeholder text is visible */
    .stTextInput > div > div > input::placeholder,
    .stTextArea textarea::placeholder {
        color: #9ca3af !important;  /* Light gray - visible on dark background */
        opacity: 1;  /* Override any fading */
    }

    /* Style buttons for better contrast */
    .stButton > button {
        background-color: #00e5a0 !important;
        color: #06070a !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-size: 16px !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #00cc8f !important;
        color: #000000 !important;
        box-shadow: 0 2px 8px rgba(0,229,160,0.3);
    }
    .stButton > button:focus {
        outline: 2px solid #00e5a0;
        outline-offset: 2px;
    }

    /* Text area background and text */
    .stTextArea textarea {
        background: #161820;
        color: white;
        border: 1px solid #30363d;
    }
    .stTextInput > div > div > input::placeholder, .stTextArea textarea::placeholder {
        color: #9ca3af;
    }
    /* Report placeholder */
    .report-placeholder {
        background: #111318;
        border: 1px solid #1e2028;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        color: #d1d5db;
        font-size: 18px;
    }
    /* Improve readability of markdown text */
    .stMarkdown p, .stMarkdown li {
        color: #e5e7eb;
        font-size: 16px;
        line-height: 1.6;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #ffffff;
    }
    /* Style for JSON output */
    .stJson {
        background-color: #1e1e2a;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #2d2d3a;
    }
    .stJson pre {
        color: #f8f8f2; /* light text on dark background */
        font-size: 14px;
    }
    /* Expander styling */
    .streamlit-expanderHeader {
        color: #ffffff !important;
        font-weight: 600;
        background-color: #1a1c24;
        border-radius: 8px;
    }
    .streamlit-expanderContent {
        background-color: #111318;
        border: 1px solid #2d2d3a;
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 20px;
    }
    /* Success/Warning/Error boxes */
    .stAlert {
        border-radius: 8px;
        font-weight: 500;
    }
    /* Caption text */
    .stCaption {
        color: #9ca3af;
        font-size: 14px;
    }
    /* Links */
    a {
        color: #00e5a0;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- LANDING PAGE ----------------
if st.session_state.page == "landing":

    # Hero
    st.markdown("""
    <div class="hero">
        <h1>Veritas<span class="accent">AI</span></h1>
        <h2>Truth in the <span class="accent">Age of AI</span></h2>
        <p>Verify AI-generated research citations in seconds. VeritasAI cross-references papers across 7+ academic APIs and flags hallucinated sources before they spread.</p>
    </div>
    """, unsafe_allow_html=True)

    # Beta badge
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div style="text-align: center;"><span class="beta-badge">BETA V1.8</span></div>', unsafe_allow_html=True)

    # Start button
    colA, colB, colC = st.columns([2, 1, 2])
    with colB:
        if st.button("⚡ Start Verifying", use_container_width=True):
            st.session_state.page = "tool"
            st.rerun()

    # Metrics
    st.markdown('<div class="metric-row">', unsafe_allow_html=True)
    mcol1, mcol2, mcol3 = st.columns(3)
    with mcol1:
        st.markdown("""
        <div class="metric-card">
            <h3>3</h3>
            <p>ACADEMIC APIS</p>
        </div>
        """, unsafe_allow_html=True)
    with mcol2:
        st.markdown("""
        <div class="metric-card">
            <h3>92%</h3>
            <p>DETECTION RATE</p>
        </div>
        """, unsafe_allow_html=True)
    with mcol3:
        st.markdown("""
        <div class="metric-card">
            <h3>&lt;5s</h3>
            <p>AVG. VERIFY TIME</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # How It Works
    st.markdown('<div class="how-it-works"><h2>Three layers of verification</h2>', unsafe_allow_html=True)
    hcol1, hcol2, hcol3 = st.columns(3)

    with hcol1:
        st.markdown("""
        <div class="layer-card">
            <h4>01 Local Database Check</h4>
            <p>Instantly searches our curated local database of IEEE Xplore and arXiv papers using FAISS vector similarity and SBERT embeddings.</p>
        </div>
        """, unsafe_allow_html=True)

    with hcol2:
        st.markdown("""
        <div class="layer-card">
            <h4>02 External API Verification</h4>
            <p>Cross-references with Semantic Scholar, CrossRef, OpenAI, arXiv, Elsevier, NASA ADS, and Library of Congress using fuzzy title matching.</p>
        </div>
        """, unsafe_allow_html=True)

    with hcol3:
        st.markdown("""
        <div class="layer-card">
            <h4>03 Link & URL Validation</h4>
            <p>Checks if the citation link is reachable, detects 404 errors, scrapes page content to confirm it matches the cited paper title.</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- TOOL PAGE ----------------
elif st.session_state.page == "tool":

    # Header with back button
    header_left, header_mid, header_right = st.columns([1, 3, 1])
    with header_left:
        if st.button("⬅ Back"):
            st.session_state.page = "landing"
            st.rerun()
    with header_mid:
        st.markdown('<div class="tool-header"><h3>Veritas<span class="accent">AI</span></h3></div>', unsafe_allow_html=True)

    st.write("")

    # Main two-column layout
    col1, col2 = st.columns([1, 1])

    # ---------- LEFT PANEL (Input) ----------
    with col1:
        st.subheader("Citation Verifier")

        title = st.text_input(
            "Paper Title",
            placeholder="e.g. Attention Is All You Need"
        )

        url = st.text_input(
            "Source URL",
            placeholder="e.g. https://arxiv.org/abs/1706.03762"
        )

        st.markdown("**OR PASTE FULL AI OUTPUT**")
        ai_text = st.text_area(
            "",
            height=200,
            placeholder="Paste the full response from ChatGPT, Claude, Gemini etc. — we'll extract paper titles and URLs automatically."
        )

        verify = st.button("Check Authenticity", use_container_width=True)

    # ---------- RIGHT PANEL (Report) ----------
    with col2:
        st.subheader("Analysis Report")

        # Helper function to display a single verification result
        def display_verification(verification, title, url):
            """Render a detailed verification result."""
            status = verification.get("final_status")
            orig = verification.get("original_verification", {})
            alternatives = verification.get("verified_alternatives", [])

            # Status icon and message
            if status == "VALID_CITATION":
                st.success("✅ **Authentic** – This citation exists and matches the source.")
            elif status == "HALLUCINATED_CITATION":
                st.warning("⚠️ **Hallucinated** – The citation could not be verified.")
            elif status == "HALLUCINATED_WITH_ALTERNATIVES":
                st.info("🔍 **Hallucinated, but we found real alternatives** – The given paper does not exist, but these similar papers do:")
            else:
                st.error("❌ **Error** – Could not verify this citation.")

            # Show input details
            st.markdown(f"**Title:** {title}")
            if url:
                st.markdown(f"**URL:** {url}")

            # Original verification details (if any)
            if orig:
                with st.expander("Verification details"):
                    st.json(orig)

            # Show alternatives if present
            if alternatives:
                st.markdown("---")
                st.markdown("### 📚 Real papers you might be looking for:")
                for alt in alternatives:
                    alt_title = alt.get("title", "Unknown")
                    alt_url = alt.get("url", "#")
                    method = alt.get("verification_method", "")
                    st.markdown(f"- **[{alt_title}]({alt_url})**  \n  *{method}*")

            # Raw JSON for debugging (optional, can be hidden)
            with st.expander("Full response (JSON)"):
                st.json(verification)

        if not verify:
            st.markdown("""
            <div class="report-placeholder">
                Results will appear here after verification<br>
                Enter a paper title and URL on the left, then click <strong>Check Authenticity</strong>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Determine which input to use
            if ai_text.strip():
                # Full AI output mode
                with st.spinner("Extracting and verifying citations..."):
                    results = run_text_pipeline(ai_text)
                if not results:
                    st.warning("No citations found in the provided text.")
                else:
                    st.success(f"Found {len(results)} citation(s)")
                    for idx, res in enumerate(results, 1):
                        title_disp = res.get("title", "Unknown title")
                        url_disp = res.get("url", "")
                        verification = res.get("verification", {})
                        with st.expander(f"{idx}. {title_disp[:60]}..."):
                            display_verification(verification, title_disp, url_disp)
            else:
                # Single citation mode
                if not title and not url:
                    st.warning("Please enter a paper title and URL, or paste full AI output.")
                else:
                    with st.spinner("Verifying citation..."):
                        result = process_citation_form(title, url)
                    display_verification(result, title, url)