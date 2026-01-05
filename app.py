import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime
import json
import re
import requests

st.set_page_config(page_title="洋裁在庫ログ", layout="centered")
st.title("🧵 魔法の洋裁ログ (GAS連携版)")

# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbxf4m1KVwsaaVeUpdPvq4DRFwNOgGc89ha7F7lXaBKlNITZWDGyIpENVVfXZNcRj51m/exec"

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secretsに GEMINI_API_KEY が設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def get_working_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ["models/gemini-1.5-flash", "models/gemini-1.5-flash-latest"]:
            if target in available_models: return genai.GenerativeModel(target)
        return genai.GenerativeModel(available_models[0])
    except:
        return genai.GenerativeModel("models/gemini-1.5-flash")

model = get_working_model()

tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    method = st.radio("入力方法", ["テキスト貼り付け", "画像アップロード"])
    uploaded_files = st.file_uploader("写真アップロード", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True) if method == "画像アップロード" else None
    text_input = st.text_area("テキスト") if method == "テキスト貼り付け" else None

    if st.button("AI解析をスタート"):
        if (method == "テキスト貼り付け" and text_input) or (method == "画像アップロード" and uploaded_files):
            with st.spinner("解析中..."):
                try:
                    prompt = '統合してJSONで出力: {"name": "生地名", "material": "素材", "width": "幅", "length": 1.0, "total_price": 2000, "color": "色", "shop": "店名"}'
                    if method == "テキスト貼り付け":
                        response = model.generate_content(prompt + text_input)
                    else:
                        img_list = [Image.open(f) for f in uploaded_files]
                        response = model.generate_content([prompt] + img_list)
                    
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if json_match:
                        st.session_state.temp_data = json.loads(json_match.group())
                        st.success("解析完了！")
                    else:
                        st.error("解析結果からデータが見つかりませんでした。")
                except Exception as e:
                    st.error(f"解析失敗: {e}")

    if "temp_data" in st.session_state:
        st.divider()
        st.subheader("📝 データの確認・修正")
        d = st.session_state.temp_data
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("生地名", value=str(d.get("name", "")))
            material = st.text_input("素材", value=str(d.get("material", "")))
            color = st.text_input("色", value=str(d.get("color", "")))
            shop = st.text_input("購入店", value=str(d.get("shop", "")))
        with col2:
            width = st.text_input("幅", value=str(d.get("width", "")))
            try: l_val = float(d.get("length", 1.0))
            except: l_val = 1.0
            try: p_val = int(d.get("total_price", 0))
            except: p_val = 0
            
            length_m = st.number_input("数量(m)", value=l_val, step=0.1)
            total_price = st.number_input("合計価格", value=p_val, step=10)
            price_per_m = int(total_price / length_m) if length_m > 0 else 0
            st.metric("1m単価", f"{price_per_m}円")

        if st.button("スプレッドシートに保存"):
            try:
                payload = {
                    "date": str(datetime.date.today()),
                    "name": name,
                    "material": material,
                    "color": color,
                    "width": width,
                    "length": length_m,
                    "price": total_price,
                    "unit_price": price_per_m,
                    "shop": shop
                }
                response = requests.post(GAS_URL, data=json.dumps(payload))
                
                if response.status_code == 200:
                    st.success("保存成功！スプレッドシートを確認してください。")
                    st.balloons()
                    if "temp_data" in st.session_state:
                        del st.session_state.temp_data
                else:
                    st.error(f"保存失敗 (ステータスコード: {response.status_code})")
                    st.write("Googleからのメッセージ:", response.text)
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

with tab2:
    st.write("スプレッドシートを開いて在庫を確認してください。")
