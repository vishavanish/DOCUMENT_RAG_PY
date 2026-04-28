import streamlit as st
import requests
import json
import pandas as pd

# Configure Streamlit
st.set_page_config(
    page_title="News Collection + RAG System",
    page_icon="📰",
    layout="wide"
)

# API Base URL
API_BASE = "http://localhost:5001"

def main():
    st.title("📰 News Collection + RAG System")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["News Articles", "RAG System", "News Authenticity", "System Status"])
    
    if page == "News Articles":
        news_page()
    elif page == "RAG System":
        rag_page()
    elif page == "News Authenticity":
        authenticity_page()
    elif page == "System Status":
        status_page()

def news_page():
    st.header("📰 News Articles")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Fetch Latest News"):
            with st.spinner("Fetching news..."):
                try:
                    response = requests.get(f"{API_BASE}/fetch-news")
                    if response.status_code == 200:
                        st.success("News fetch initiated!")
                        st.json(response.json())
                    else:
                        st.error(f"Error: {response.status_code}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
    
    with col2:
        if st.button("Refresh Articles"):
            load_articles()

def load_articles():
    try:
        response = requests.get(f"{API_BASE}/articles")
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            if articles:
                st.subheader(f"Latest {len(articles)} Articles")
                
                for article in articles:
                    with st.expander(f"📄 {article['title'][:100]}..."):
                        st.write(f"**Source:** {article['source_name']}")
                        st.write(f"**Published:** {article['published_at']}")
                        st.write(f"**Description:** {article['description']}")
                        st.write(f"**URL:** {article['url']}")
            else:
                st.info("No articles found. Try fetching news first.")
        else:
            st.error("Failed to load articles")
    except Exception as e:
        st.error(f"Error loading articles: {e}")

def rag_page():
    st.header("🤖 RAG System - Document Q&A")
    
    # Document Upload
    st.subheader("📄 Upload PDF Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file and st.button("Upload & Index"):
        with st.spinner("Processing document..."):
            try:
                files = {"file": uploaded_file}
                response = requests.post(f"{API_BASE}/upload", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    st.success("Document uploaded successfully!")
                    st.json(result)
                    st.session_state.doc_id = result.get('document_id')
                else:
                    st.error(f"Upload failed: {response.json()}")
            except Exception as e:
                st.error(f"Upload error: {e}")
    
    # Document List
    st.subheader("📚 Available Documents")
    if st.button("Refresh Documents"):
        load_documents()
    
    # Query Interface
    st.subheader("❓ Ask Questions")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        doc_id = st.text_input("Document ID", value=st.session_state.get('doc_id', ''))
        question = st.text_area("Your Question", placeholder="What is this document about?")
    
    with col2:
        k = st.slider("Number of chunks to retrieve", 1, 10, 3)
    
    if st.button("Ask Question") and doc_id and question:
        with st.spinner("Generating answer..."):
            try:
                payload = {
                    "document_id": doc_id,
                    "question": question,
                    "k": k
                }
                
                response = requests.post(
                    f"{API_BASE}/query",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(payload)
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.subheader("🎯 Answer")
                    st.write(result.get('answer', 'No answer generated'))
                    
                    st.subheader("📖 Sources")
                    sources = result.get('sources', [])
                    for i, source in enumerate(sources, 1):
                        with st.expander(f"Source {i} (Score: {source.get('score', 0):.3f})"):
                            st.write(source.get('text', ''))
                else:
                    st.error(f"Query failed: {response.json()}")
            except Exception as e:
                st.error(f"Query error: {e}")

def load_documents():
    try:
        response = requests.get(f"{API_BASE}/documents")
        if response.status_code == 200:
            data = response.json()
            documents = data.get('documents', [])
            
            if documents:
                df = pd.DataFrame(documents)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No documents uploaded yet.")
        else:
            st.error("Failed to load documents")
    except Exception as e:
        st.error(f"Error loading documents: {e}")

def authenticity_page():
    st.header("🔍 News Authenticity Check (Module 3)")
    
    st.subheader("📰 Check News Authenticity")
    
    news_title = st.text_input("News Title (Optional)", placeholder="Enter news headline...")
    news_text = st.text_area("News Content", placeholder="Paste the news article content here...", height=200)
    
    if st.button("Check Authenticity") and news_text:
        with st.spinner("Analyzing news authenticity..."):
            try:
                payload = {
                    "news_text": news_text,
                    "news_title": news_title
                }
                
                response = requests.post(
                    f"{API_BASE}/check-authenticity",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(payload)
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    status = result.get('status', 'UNKNOWN')
                    confidence = result.get('confidence', 0)
                    
                    if status == "VERIFIED REAL":
                        st.success(f"🟢 **Status: {status}**")
                    elif status == "LIKELY REAL":
                        st.info(f"🔵 **Status: {status}**")
                    elif status == "UNVERIFIED":
                        st.warning(f"🟡 **Status: {status}**")
                    else:
                        st.error(f"🔴 **Status: {status}**")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Confidence", f"{confidence}%")
                    with col2:
                        st.metric("Similar Articles", result.get('similar_count', 0))
                    with col3:
                        st.metric("Avg Trust Score", f"{result.get('average_trust_score', 0):.2f}")
                    
                    st.subheader("📋 Analysis")
                    st.write(f"**Reason:** {result.get('reason', 'No explanation available')}")
                    
                    evidence = result.get('evidence', {})
                    if evidence.get('supporting_sources'):
                        st.subheader("📰 Supporting Sources")
                        for source in evidence['supporting_sources']:
                            st.write(f"• {source}")
                    
                    with st.expander("🔧 Technical Details"):
                        st.json(result)
                        
                else:
                    st.error(f"Analysis failed: {response.json()}")
                    
            except Exception as e:
                st.error(f"Error during analysis: {e}")

def status_page():
    st.header("⚙️ System Status")
    
    # API Health Check
    st.subheader("🔍 API Health Check")
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            st.success("✅ Flask API is running")
            st.json(response.json())
        else:
            st.error("❌ Flask API error")
    except Exception as e:
        st.error(f"❌ Flask API not accessible: {e}")
    
    # Database Status
    st.subheader("🗄️ Database Status")
    if st.button("Initialize Database"):
        try:
            response = requests.get(f"{API_BASE}/init-db")
            if response.status_code == 200:
                st.success("✅ Database initialized")
                st.json(response.json())
            else:
                st.error("❌ Database initialization failed")
        except Exception as e:
            st.error(f"❌ Database error: {e}")
    
    # System Info
    st.subheader("📊 System Information")
    st.info("""
    **Modules:**
    - Module 1: News Collection (Celery + Redis)
    - Module 2: RAG System (PDF Q&A with Google Gemini)
    - Module 3: News Authenticity Decision
    
    **Endpoints:**
    - `/` - Health check
    - `/articles` - View news articles
    - `/fetch-news` - Trigger news collection
    - `/upload` - Upload PDF documents
    - `/query` - Query documents
    - `/documents` - List documents
    - `/check-authenticity` - Check news authenticity
    """)

if __name__ == "__main__":
    if 'doc_id' not in st.session_state:
        st.session_state.doc_id = ''
    main()