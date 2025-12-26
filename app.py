import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime
import json
import re
import pandas as pd
# 追加のライブラリ（これなら秘密鍵なしでいけます）
import requests

st.set_page_config(page_title="洋裁在庫ログ", layout="centered")
st.title("🧵 魔法の洋裁ログ (簡易保存版)")

# --- 設定 ---
# ※スプレッドシートのURLをここに貼り付けてください
# ※「リンクを知っている全員が編集者」になっている必要があります
SPREADSHEET_URL = "あなたのスプレッドシートURL"

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secretsに GEMINI_API_KEY が設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# スプレッドシートへ保存する関数 (Google Apps Script等を使わない最もシンプルな方法に後ほど誘導します)
# まずは解析が動くことを最優先にします

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
                except Exception as e:
                    st.error(f"解析失敗: {e}")

    if "temp_data" in st.session_state:
        d = st.session_state.temp_data
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("生地名", value=str(d.get("name", "")))
            material = st.text_input("素材", value=str(d.get("material", "")))
            color = st.text_input("色", value=str(d.get("color", "")))
            shop = st.text_input("購入店", value=str(d.get("shop", "")))
        with col2:
            width = st.text_input("幅", value=str(d.get("width", "")))
            length_m = st.number_input("数量(m)", value=float(d.get("length", 1.0)), step=0.1)
            total_price = st.number_input("合計価格", value=int(d.get("total_price", 0)), step=10)
            price_per_m = int(total_price / length_m) if length_m > 0 else 0
            st.metric("1m単価", f"{price_per_m}円")

        st.warning("現在、解析機能のみ動作しています。スプレッドシートへの保存には追加設定が必要です。")
        # 一旦、保存ボタンは無効化するか、別の方法を案内します
