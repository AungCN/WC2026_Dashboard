"""
pages/news_feed.py
───────────────────
News page — free RSS feeds, no API key required.
Sources: BBC Sport, The Guardian, ESPN, Goal.com, Google News WC 2026.
Falls back to demo articles if feeds are unreachable.
"""
import streamlit as st
from utils.api_client import get_news

def render():
    st.title("📰 World Cup 2026 News")
    st.caption("Free RSS feeds · BBC · Guardian · ESPN · Goal.com · No API key needed")

    col1, col2 = st.columns([3,1])
    with col1:
        search = st.text_input("Filter articles", placeholder="e.g. Argentina, Mbappe…")
    with col2:
        count = st.selectbox("Show", [10, 20, 30], index=1)

    with st.spinner("Loading news…"):
        articles = get_news(max_items=count)

    if search:
        articles = [a for a in articles
                    if search.lower() in (a["title"]+a["description"]).lower()]

    if not articles:
        st.info("No articles found. Try a different search term.")
        return

    st.caption(f"{len(articles)} articles")
    st.divider()

    for article in articles:
        col_text, col_meta = st.columns([5,1])
        with col_text:
            title = article.get("title","")
            url   = article.get("url","#")
            desc  = article.get("description","")
            st.markdown(f"**[{title}]({url})**")
            if desc:
                st.caption(desc[:220] + ("…" if len(desc) > 220 else ""))
        with col_meta:
            source = article.get("source",{}).get("name","")
            pub    = article.get("publishedAt","")[:10]
            st.caption(f"📰 {source}")
            st.caption(f"📅 {pub}")
        st.divider()
