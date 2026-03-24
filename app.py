"""
日本旅遊菜單翻譯與點餐助手
使用 Streamlit + Gemini AI

使用方法：
1. 部署到 Streamlit Cloud
2. 在手機/電腦開啟網址
3. 拍照或上傳菜單
4. 翻譯 → 點餐 → 顯示總金額
"""

import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import json
import re

# 頁面設定
st.set_page_config(
    page_title="Japan Menu Translator",
    page_icon="fork_and_knife",
    layout="centered"
)

# 標題
st.title("Japan Menu Translator")
st.markdown("---")

# API Key 輸入（放在側邊欄）
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    st.markdown("💡 沒有 Key？取得 [Gemini API](https://aistudio.google.com/app/apikey)")
    st.markdown("---")
    st.markdown("""
    **使用說明：**
    1. 輸入 API Key
    2. 拍照或上傳菜單
    3. 點擊翻譯
    4. 選擇餐點
    5. 查看總金額
    """)

# 主程式
if not api_key:
    st.info("👈 請先在左側輸入您的 Gemini API Key")
    st.image("https://i.imgur.com/JpL1uT5.png", width=300)
    st.stop()

# 設定 Gemini
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"API Key 設定失敗：{e}")
    st.stop()

# 初始化 session state
if 'menu' not in st.session_state:
    st.session_state['menu'] = []
if 'order' not in st.session_state:
    st.session_state['order'] = {}

# 1. 上傳/拍照
st.subheader("📸 步驟一：上傳菜單")
col1, col2 = st.columns(2)
with col1:
    img_file = st.file_uploader("上傳菜單照片", type=['jpg', 'png', 'jpeg', 'webp'])
with col2:
    camera_img = st.camera_input("或拍照上傳")

img = img_file or camera_img

if img:
    image = Image.open(img)
    st.image(image, caption="已上傳的菜單", use_column_width=True)

    # 2. 翻譯按鈕
    st.markdown("---")
    st.subheader("🔄 步驟二：AI 翻譯")
    
    if st.button("🤖 開始翻譯", type="primary", use_container_width=True):
        with st.spinner("AI 正在翻譯中，請稍候..."):
            try:
                prompt = """你是一個專業的日本料理翻譯助手。請仔細分析這張日本餐廳菜單圖片。

請以 JSON 格式回傳所有餐點資訊：
```json
{
  "restaurant_name": "店名（如果可辨认）",
  "items": [
    {"number": 1, "name_jp": "日文名稱", "name_tw": "繁體中文翻譯", "price": 純數字日幣價格, "category": "分類"}
  ]
}
```

注意：
1. price 是數字（去除円、,等符號）
2. 如果是套餐，尽量拆解主要成分
3. 如果價格是範圍，取平均或最低值
4. category 可選：主食、拉麵、烏龍麵、炸物、燒肉、壽司、甜點、飲料、酒類、其他
5. 只輸出 JSON，不要其他文字"""

                response = model.generate_content([prompt, image])
                response_text = response.text.strip()
                
                # 清洗 JSON
                json_str = re.sub(r'^```json\s*', '', response_text)
                json_str = re.sub(r'^```\s*', '', json_str)
                json_str = re.sub(r'\s*```$', '', json_str)
                
                menu_data = json.loads(json_str)
                st.session_state['menu'] = menu_data.get('items', [])
                
                if menu_data.get('restaurant_name'):
                    st.success(f"🍽️ 辨識到：{menu_data['restaurant_name']}")
                else:
                    st.success("✅ 翻譯完成！")
                    
            except json.JSONDecodeError as e:
                st.error(f"JSON 解析失敗：{e}")
                st.text("原始回覆：" + response_text[:500])
            except Exception as e:
                st.error(f"翻譯失敗：{e}")

# 3. 點餐介面
if st.session_state['menu']:
    st.markdown("---")
    st.subheader("🍽️ 步驟三：選擇餐點")
    
    # 按分類顯示
    categories = {}
    for item in st.session_state['menu']:
        cat = item.get('category', '其他')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    # 初始化訂單
    if 'quantities' not in st.session_state:
        st.session_state['quantities'] = {item['number']: 0 for item in st.session_state['menu']}
    
    # 顯示餐點
    for cat, items in categories.items():
        with st.expander(f"📁 {cat}（{len(items)}項）", expanded=True):
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
                    st.text(f"¥{price:,}")
                
                with col3:
                    qty = st.number_input(
                        "數量",
                        min_value=0,
                        max_value=10,
                        value=st.session_state['quantities'][num],
                        key=f"qty_{num}",
                        label_visibility="collapsed"
                    )
                    st.session_state['quantities'][num] = qty
                
                with col4:
                    if checked and qty > 0:
                        st.markdown(f"**¥{price * qty:,}**")
    
    # 4. 結算
    st.markdown("---")
    st.subheader("💰 步驟四：結算")
    
    # 計算總金額
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
        # 顯示訂單明細
        for item in ordered_items:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.text(f"✅ {item['name']} x {item['qty']}")
            with col2:
                st.text(f"¥{item['price']:,}")
            with col3:
                st.markdown(f"**¥{item['subtotal']:,}**")
        
        st.markdown("---")
        
        # 總計
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### 共 {total_items} 項")
        with col2:
            st.markdown(f"### 💴 ¥{total_jpy:,}")
        
        # 台幣估計
        rate = st.number_input(
            "匯率（日幣兌台幣）",
            min_value=0.0,
            max_value=1.0,
            value=0.21,
            step=0.01,
            format="%.2f",
            help="目前約 0.20-0.22"
        )
        
        total_ntd = int(total_jpy * rate)
        st.success(f"🇹🇼 約 NT$ {total_ntd:,}")
        
        # 清除按鈕
        if st.button("🗑️ 清除訂單", type="secondary"):
            st.session_state['quantities'] = {item['number']: 0 for item in st.session_state['menu']}
            st.rerun()
    else:
        st.info("👆 請在上方選擇您要的餐點")

# 底部
st.markdown("---")
st.markdown("Made with ❤️ for 日本旅遊 | 使用 Gemini AI 翻譯")
