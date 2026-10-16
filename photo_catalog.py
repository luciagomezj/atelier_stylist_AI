"""Image resolver for ATELIER AI. Uses local photos or approved remote URLs."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')

def image_for(item):
    """Return a Streamlit-compatible image source, or None."""
    item_id = str(int(item['id']))
    for folder in ('photos', 'images'):
        for ext in EXTENSIONS:
            path = ROOT / folder / f'{item_id}{ext}'
            if path.is_file():
                return str(path)
    raw = item.get('image_url', '')
    if pd.notna(raw):
        url = str(raw).strip()
        if url.startswith(('https://', 'http://')):
            return url
    return None

def show_fashion_card(item):
    import streamlit as st
    image = image_for(item)
    if image:
        st.image(image, use_container_width=True)
    else:
        st.markdown('📷 *Photo coming soon*')
    st.markdown(f"**{item['name']}**")
    st.caption(f"{str(item['color']).title()} · {str(item['category']).title()}")
    st.markdown(f"**€{float(item['price']):.2f}**")
    link = item.get('product_url', '')
    if pd.notna(link) and str(link).strip().startswith(('https://', 'http://')):
        st.link_button('View product ↗', str(link).strip(), use_container_width=True)
