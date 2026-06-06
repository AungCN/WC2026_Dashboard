"""
pages/news_feed.py
───────────────────
News Feed page — latest World Cup 2026 articles from NewsAPI.
Cached for 15 minutes so we don't exhaust the free tier (100 req/day).
"""

import streamlit as st
from utils.api_client import get_news


def render():
    st.title("📰 World Cup 2026 News")
    st.caption("Updates every 15 minutes · Powered by NewsAPI")

    # ── Search filter ──────────────────────────────────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "Search topic",
            value="World Cup 2026",
            placeholder="e.g. Brazil squad, Mbappe injury…",
        )
    with col2:
        count = st.selectbox("Articles", [10, 20, 30], index=1)

    articles = get_news(query=query, page_size=count)

    if not articles:
        st.warning("No articles found. Try a different search term or check your NewsAPI key.")
        return

    st.markdown(f"Found **{len(articles)}** articles.")
    st.divider()

    # ── Article cards ─────────────────────────────────────────────────────────
    for article in articles:
        _render_article(article)


def _render_article(article: dict):
    """Render one news article as an image + text card."""
    col_img, col_text = st.columns([1, 3])

    with col_img:
        img_url = article.get("urlToImage")
        if img_url:
            try:
                st.image(img_url, use_container_width=True)
            except Exception:
                st.markdown("🖼️")

    with col_text:
        title       = article.get("title", "No title")
        description = article.get("description", "")
        url         = article.get("url", "#")
        source      = article.get("source", {}).get("name", "Unknown source")
        published   = article.get("publishedAt", "")[:10]

        st.markdown(f"**[{title}]({url})**")
        if description:
            # Show first 200 characters only — avoid copyright issues
            st.caption(description[:200] + ("…" if len(description) > 200 else ""))
        st.caption(f"📰 {source} · {published}")

    st.divider()
