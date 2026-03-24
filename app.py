"""
?交???蝧餉陌??擗??雿輻 Streamlit + Gemini AI

雿輻?寞?嚗?1. ?函蔡??Streamlit Cloud
2. ?冽?璈??餉??蝬脣?
3. ????唾???4. 蝧餉陌 ??暺? ??憿舐內蝮賡?憿?"""

import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import json
import re

# ?閮剖?
st.set_page_config(
    page_title="?? ?交?蝧餉陌暺?",
    page_icon="??",
    layout="centered"
)

# 璅?
st.title("?? ?交???蝧餉陌??擗??)
st.markdown("---")

# API Key 頛詨嚗?典??嚗?with st.sidebar:
    st.header("?? 閮剖?")
    api_key = st.text_input("頛詨 Gemini API Key", type="password")
    st.markdown("? 瘝? Key嚗?敺?[Gemini API](https://aistudio.google.com/app/apikey)")
    st.markdown("---")
    st.markdown("""
    **雿輻隤芣?嚗?*
    1. 頛詨 API Key
    2. ????唾???    3. 暺?蝧餉陌
    4. ?豢?擗?
    5. ?亦?蝮賡?憿?    """)

# 銝餌?撘?if not api_key:
    st.info("?? 隢??典椰?渲撓?交??Gemini API Key")
    st.image("https://i.imgur.com/JpL1uT5.png", width=300)
    st.stop()

# 閮剖? Gemini
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"API Key 閮剖?憭望?嚗e}")
    st.stop()

# ????session state
if 'menu' not in st.session_state:
    st.session_state['menu'] = []
if 'order' not in st.session_state:
    st.session_state['order'] = {}

# 1. 銝/?
st.subheader("? 甇仿?銝嚗??唾???)
col1, col2 = st.columns(2)
with col1:
    img_file = st.file_uploader("銝??抒?", type=['jpg', 'png', 'jpeg', 'webp'])
with col2:
    camera_img = st.camera_input("???找???)

img = img_file or camera_img

if img:
    image = Image.open(img)
    st.image(image, caption="撌脖??喟??", use_column_width=True)

    # 2. 蝧餉陌??
    st.markdown("---")
    st.subheader("?? 甇仿?鈭?AI 蝧餉陌")
    
    if st.button("?? ??蝧餉陌", type="primary", use_container_width=True):
        with st.spinner("AI 甇?蝧餉陌銝哨?隢???.."):
            try:
                prompt = """雿銝??璆剔??交??蝧餉陌?拇???隞敦???撐?交擗輒?????
隢誑 JSON ?澆?????暺?閮?
```json
{
  "restaurant_name": "摨?嚗??颲刻恕嚗?,
  "items": [
    {"number": 1, "name_jp": "?交??迂", "name_tw": "蝜?銝剜?蝧餉陌", "price": 蝝摮撟??? "category": "??"}
  ]
}
```

瘜冽?嚗?1. price ?舀摮??駁??蝑泵??
2. 憒??臬?擗?撠賡??圾銝餉???
3. 憒??寞?舐????像???雿?4. category ?舫嚗蜓憌?暻萸?樴熊??押??ˊ?詻?暺ㄡ??憿隞?5. ?芾撓??JSON嚗?閬隞?摮?""

                response = model.generate_content([prompt, image])
                response_text = response.text.strip()
                
                # 皜? JSON
                json_str = re.sub(r'^```json\s*', '', response_text)
                json_str = re.sub(r'^```\s*', '', json_str)
                json_str = re.sub(r'\s*```$', '', json_str)
                
                menu_data = json.loads(json_str)
                st.session_state['menu'] = menu_data.get('items', [])
                
                if menu_data.get('restaurant_name'):
                    st.success(f"?儭?颲刻??堆?{menu_data['restaurant_name']}")
                else:
                    st.success("??蝧餉陌摰?嚗?)
                    
            except json.JSONDecodeError as e:
                st.error(f"JSON 閫??憭望?嚗e}")
                st.text("????嚗? + response_text[:500])
            except Exception as e:
                st.error(f"蝧餉陌憭望?嚗e}")

# 3. 暺?隞
if st.session_state['menu']:
    st.markdown("---")
    st.subheader("?儭?甇仿?銝??豢?擗?")
    
    # ??憿＊蝷?    categories = {}
    for item in st.session_state['menu']:
        cat = item.get('category', '?嗡?')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    # ??????    if 'quantities' not in st.session_state:
        st.session_state['quantities'] = {item['number']: 0 for item in st.session_state['menu']}
    
    # 憿舐內擗?
    for cat, items in categories.items():
        with st.expander(f"?? {cat}嚗len(items)}??", expanded=True):
            for item in items:
                num = item['number']
                name_tw = item.get('name_tw', '')
                name_jp = item.get('name_jp', '')
                price = item.get('price', 0)
                
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                
                with col1:
                    checkbox_key = f"item_{num}"
                    checked = st.checkbox(
                        f"{name_tw}",
                        value=st.session_state['quantities'][num] > 0,
                        key=checkbox_key
                    )
                    if name_jp != name_tw:
                        st.caption(f"   {name_jp}")
                
                with col2:
                    st.text(f"瞼{price:,}")
                
                with col3:
                    qty = st.number_input(
                        "?賊?",
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
    
    # 4. 蝯?
    st.markdown("---")
    st.subheader("? 甇仿???蝯?")
    
    # 閮?蝮賡?憿?    total_jpy = 0
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
        # 憿舐內閮?敦
        for item in ordered_items:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.text(f"??{item['name']} x {item['qty']}")
            with col2:
                st.text(f"瞼{item['price']:,}")
            with col3:
                st.markdown(f"**瞼{item['subtotal']:,}**")
        
        st.markdown("---")
        
        # 蝮質?
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### ??{total_items} ??)
        with col2:
            st.markdown(f"### ? 瞼{total_jpy:,}")
        
        # ?啣馳隡啗?
        rate = st.number_input(
            "?舐?嚗撟???啣馳嚗?,
            min_value=0.0,
            max_value=1.0,
            value=0.21,
            step=0.01,
            format="%.2f",
            help="?桀?蝝?0.20-0.22"
        )
        
        total_ntd = int(total_jpy * rate)
        st.success(f"?? 蝝?NT$ {total_ntd:,}")
        
        # 皜??
        if st.button("??儭?皜閮", type="secondary"):
            st.session_state['quantities'] = {item['number']: 0 for item in st.session_state['menu']}
            st.rerun()
    else:
        st.info("?? 隢銝?豢??刻???暺?)

# 摨
st.markdown("---")
st.markdown("Made with ?歹? for ?交?? | 雿輻 Gemini AI 蝧餉陌")
