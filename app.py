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
# ご自身のスプレッドシートのURLを貼り付けてください
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
                    
                    # 正規表現でJSON部分を抽出
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if json_match:
                        st.session_state.temp_data = json.loads(json_match.group())
                        st.success("解析完了！内容を自由に変更してください。")
                    else:
                        st.error("データの抽出に失敗しました。")
                except Exception as e:
                    st.error(f"解析失敗: {e}")
        else:
            st.warning("内容を入力するか、写真をアップロードしてください。")

    # --- 全項目修正エリア ---
    if "temp_data" in st.session_state:
        st.divider()
        st.subheader("📝 データの修正")
        
        d = st.session_state.temp_data
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("生地名", value=str(d.get("name", "")))
            material = st.text_input("素材", value=str(d.get("material", "")))
            color = st.text_input("色", value=str(d.get("color", "")))
            shop = st.text_input("購入店", value=str(d.get("shop", "")))
        
        with col2:
            width = st.text_input("生地幅", value=str(d.get("width", "")))
            # 数値変換エラーを防ぐための処理
            try:
                l_val = float(d.get("length", 1.0))
            except:
                l_val = 1.0
            try:
                p_val = int(d.get("total_price", 0))
            except:
                p_val = 0
                
            length_m = st.number_input("購入数量 (m)", value=l_val, step=0.1)
            total_price = st.number_input("合計価格 (円)", value=p_val, step=10)
            
            price_per_m = int(total_price / length_m) if length_m > 0 else 0
            st.metric("計算された1m単価", f"{price_per_m} 円")

        if st.button("この内容で確定して保存"):
            try:
                sheet = get_spreadsheet()
                row = [
                    str(datetime.date.today()), 
                    name, 
                    material,
                    color,
                    width, 
                    length_m, 
                    total_price, 
                    price_per_m, 
                    shop
                ]
                sheet.append_row(row)
                st.success("スプレッドシートへの保存に成功しました！")
                st.balloons()
                del st.session_state.temp_data 
            except Exception as e:
                st.error(f"保存エラー: {e}")

with tab2:
    st.write(f"[スプレッドシートを開く]({SPREADSHEET_URL})")
