"""
Japan Menu Translator & Ordering Assistant
Streamlit + Gemini AI

Usage:
1. Deploy to Streamlit Cloud
2. Open the URL
3. Upload menu photo
4. Translate and order
"""

import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import json
import re

# Page config
st.set_page_config(
    page_title="Japan Menu Translator",
    page_icon="fork_and_knife",
    layout="centered"
)

st.title("Japan Menu Translator")
st.markdown("---")

# API Key input
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    st.markdown("Get your key at [Google AI Studio](https://aistudio.google.com/app/apikey)")
    st.markdown("---")
    st.markdown("""
    **How to use:**
    1. Enter API Key
    2. Upload menu photo
    3. Click Translate
    4. Select items
    5. View total
    """)

if not api_key:
    st.info("Please enter your Gemini API Key in the sidebar")
    st.stop()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"API Key error: {e}")
    st.stop()

if 'menu' not in st.session_state:
    st.session_state['menu'] = []
if 'order' not in st.session_state:
    st.session_state['order'] = {}

# Upload
st.subheader("Step 1: Upload Menu")
col1, col2 = st.columns(2)
with col1:
    img_file = st.file_uploader("Upload photo", type=['jpg', 'png', 'jpeg', 'webp'])
with col2:
    camera_img = st.camera_input("Or take photo")

img = img_file or camera_img

if img:
    image = Image.open(img)
    st.image(image, caption="Uploaded menu", use_column_width=True)

    st.markdown("---")
    st.subheader("Step 2: AI Translation")
    
    if st.button("Translate", type="primary", use_container_width=True):
        with st.spinner("Translating..."):
            try:
                prompt = """Analyze this Japanese restaurant menu image. Extract all menu items.

Return JSON format:
{
  "restaurant_name": "restaurant name if identifiable",
  "items": [
    {"number": 1, "name_jp": "Japanese name", "name_tw": "Traditional Chinese translation", "price": number, "category": "category"}
  ]
}

Notes:
1. price is a number (JPY)
2. category options: main, ramen, udon, fried, BBQ, sushi, dessert, drink, alcohol, other
3. Output JSON only"""

                response = model.generate_content([prompt, image])
                response_text = response.text.strip()
                
                json_str = re.sub(r'^```json\s*', '', response_text)
                json_str = re.sub(r'^```\s*', '', json_str)
                json_str = re.sub(r'\s*```$', '', json_str)
                
                menu_data = json.loads(json_str)
                st.session_state['menu'] = menu_data.get('items', [])
                
                if menu_data.get('restaurant_name'):
                    st.success(f"Restaurant: {menu_data['restaurant_name']}")
                else:
                    st.success("Translation complete!")
                    
            except json.JSONDecodeError as e:
                st.error(f"JSON parse error: {e}")
                st.text("Raw response: " + response_text[:500])
            except Exception as e:
                st.error(f"Translation error: {e}")

# Order interface
if st.session_state['menu']:
    st.markdown("---")
    st.subheader("Step 3: Select Items")
    
    categories = {}
    for item in st.session_state['menu']:
        cat = item.get('category', 'Other')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    if 'quantities' not in st.session_state:
        st.session_state['quantities'] = {item['number']: 0 for item in st.session_state['menu']}
    
    for cat, items in categories.items():
        with st.expander(f"{cat} ({len(items)} items)", expanded=True):
            for item in items:
                num = item['number']
                name_tw = item.get('name_tw', '')
                name_jp = item.get('name_jp', '')
                price = item.get('price', 0)
                
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                
                with col1:
                    checked = st.checkbox(
                        f"{name_tw}",
                        value=st.session_state['quantities'][num] > 0,
                        key=f"item_{num}"
                    )
                    if name_jp != name_tw:
                        st.caption(f"   {name_jp}")
                
                with col2:
                    st.text(f"瞼{price:,}")
                
                with col3:
                    qty = st.number_input(
                        "Qty",
                        min_value=0,
                        max_value=10,
                        value=st.session_state['quantities'][num],
                        key=f"qty_{num}",
                        label_visibility="collapsed"
                    )
                    st.session_state['quantities'][num] = qty
                
                with col4:
                    if checked and qty > 0:
                        st.markdown(f"**瞼{price * qty:,}**")
    
    st.markdown("---")
    st.subheader("Step 4: Checkout")
    
    total_jpy = 0
    total_items = 0
    ordered_items = []
    
    for item in st.session_state['menu']:
        num = item['number']
        qty = st.session_state['quantities'][num]
        if qty > 0:
            price = item.get('price', 0)
            total_jpy += price * qty
            total_items += qty
            ordered_items.append({
                'name': item.get('name_tw', ''),
                'jp': item.get('name_jp', ''),
                'price': price,
                'qty': qty,
                'subtotal': price * qty
            })
    
    if ordered_items:
        for item in ordered_items:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.text(f"[OK] {item['name']} x {item['qty']}")
            with col2:
                st.text(f"瞼{item['price']:,}")
            with col3:
                st.markdown(f"**瞼{item['subtotal']:,}**")
        
        st.markdown("---")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### Total: {total_items} items")
        with col2:
            st.markdown(f"### JPY 瞼{total_jpy:,}")
        
        rate = st.number_input(
            "Exchange rate (JPY to TWD)",
            min_value=0.0,
            max_value=1.0,
            value=0.21,
            step=0.01,
            format="%.2f"
        )
        
        total_ntd = int(total_jpy * rate)
        st.success(f"Approx TWD NT$ {total_ntd:,}")
        
        if st.button("Clear Order"):
            st.session_state['quantities'] = {item['number']: 0 for item in st.session_state['menu']}
            st.rerun()
    else:
        st.info("Select items above")

st.markdown("---")
st.markdown("Powered by Streamlit & Gemini AI")
