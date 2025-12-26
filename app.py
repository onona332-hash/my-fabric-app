import streamlit as st
import google.generativeai as genai
from PIL import Image
import gspread
from google.oauth2.service_account import Credentials
import datetime
import json
import re
import pandas as pd

st.set_page_config(page_title="洋裁在庫ログ", layout="centered")
st.title("🧵 魔法の洋裁ログ (全項目修正版)")

# --- 設定 ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/あなたのシートID/edit"

if "GEMINI_API_KEY" not in st.secrets or "SERVICE_ACCOUNT_JSON" not in st.secrets:
    st.error("Secretsの設定が不足しています。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def get_spreadsheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = json.loads(st.secrets["SERVICE_ACCOUNT_JSON"])
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_url(SPREADSHEET_URL).sheet1

def get_working_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ["models/gemini-1.5-flash", "models/gemini-1.5-flash-latest", "models/gemini-pro"]:
            if target in available_models:
                return genai.GenerativeModel(target)
        return genai.GenerativeModel(available_models[0])
    except:
        return genai.GenerativeModel("models/gemini-1.5-flash")

model = get_working_model()

# --- メイン機能 ---
tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    method = st.radio("入力方法", ["テキスト貼り付け", "画像アップロード"])
    
    if method == "テキスト貼り付け":
        text_input = st.text_area("商品説明などのテキスト")
        uploaded_files = None
    else:
        uploaded_files = st.file_uploader("写真をアップロード", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        text_input = None

    if st.button("AI解析をスタート"):
        if (method == "テキスト貼り付け" and text_input) or (method == "画像アップロード" and uploaded_files):
            with st.spinner("解析中..."):
                try:
                    prompt = """
                    提供された情報を統合して1つの生地データとしてJSONで出力してください。
                    {"name": "生地名", "material": "素材", "width": "幅", "length": 1.0, "total_price": 2000, "color": "色", "shop": "店名"}
                    ※数値はすべて半角数字。長さはメートル(m)単位。
                    """
                    if method == "テキスト貼り付け":
                        response = model.generate_content(prompt + "\n対象:" + text_input)
                    else:
                        img_list = [Image.open(f) for f in uploaded_files]
                        response = model.generate_content([prompt] + img_list)
                    
                    json_match = re.search(r'\{.*\}
