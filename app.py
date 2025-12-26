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
st.title("🧵 魔法の洋裁ログ (まとめ解析版)")

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
        uploaded_files = st.file_uploader("写真をアップロード（同じ生地の複数枚もOK）", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        text_input = None

    if st.button("AI解析をスタート"):
        if (method == "テキスト貼り付け" and text_input) or (method == "画像アップロード" and uploaded_files):
            with st.spinner("解析中..."):
                try:
                    # ★AIへの命令を「1つの生地としてまとめる」ように強化
                    prompt = """
                    提供されたすべての情報（テキストまたは複数の画像）を確認し、
                    それらが『1つの同じ生地』に関するものであるとして、情報を統合して1つのJSON形式で出力してください。
                    
                    出力項目:
                    {"name": "生地名", "material": "素材", "width": "幅", "length": 100, "total_price": 2000, "price_per_m": 2000, "shop": "店名"}
                    
                    ※数値は半角数字のみ。解説は一切不要です。
                    """
                    
                    if method == "テキスト貼り付け":
                        response = model.generate_content(prompt + "\n対象テキスト:" + text_input)
                    else:
                        # ★すべての画像を1つのリストにしてAIに一気に送る
                        img_list = [Image.open(f) for f in uploaded_files]
                        response = model.generate_content([prompt] + img_list)
                    
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if json_match:
                        result_data = json.loads(json_match.group())
                        st.session_state.single_result = result_data # 1つの結果として保存
                        st.success("解析完了！情報を1つにまとめました。")
                        
                        # 見やすい表で表示
                        df = pd.DataFrame([result_data])
                        df.columns = ["生地名", "素材", "幅", "長さ(cm)", "合計価格", "1m単価", "店名"]
                        st.table(df)
                    else:
                        st.error("データの抽出に失敗しました。")
                except Exception as e:
                    st.error(f"解析失敗: {e}")
        else:
            st.warning("内容を入力するか、写真をアップロードしてください。")

    # 保存機能
    if "single_result" in st.session_state:
        if st.button("スプレッドシートに保存"):
            try:
                sheet = get_spreadsheet()
                d = st.session_state.single_result
                row = [
                    str(datetime.date.today()), 
                    d.get("name",""), d.get("material",""), d.get("width",""), 
                    d.get("length",0), d.get("total_price",0), d.get("price_per_m",0), d.get("shop","")
                ]
                sheet.append_row(row)
                st.success("スプレッドシートに保存しました！")
                st.balloons()
                del st.session_state.single_result
            except Exception as e:
                st.error(f"保存エラー: {e}")

with tab2:
    st.write(f"[スプレッドシートを開く]({SPREADSHEET_URL})")
