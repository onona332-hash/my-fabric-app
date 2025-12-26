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
st.title("🧵 魔法の洋裁ログ (複数解析版)")

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
        # ★複数選択(accept_multiple_files=True)を有効化
        uploaded_files = st.file_uploader("写真を1枚以上選んでください", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        text_input = None

    if st.button("AI解析をスタート"):
        results = []
        inputs = []
        
        # 入力データの整理
        if method == "テキスト貼り付け" and text_input:
            inputs = [("text", text_input)]
        elif method == "画像アップロード" and uploaded_files:
            inputs = [("image", f) for f in uploaded_files]
        
        if not inputs:
            st.warning("内容を入力するか、写真をアップロードしてください。")
        else:
            with st.spinner(f"{len(inputs)}件のデータを解析中..."):
                prompt = """
                以下の情報を抽出し、必ずJSON形式のみで出力してください。
                {"name": "生地名", "material": "素材", "width": "幅", "length": 100, "total_price": 2000, "price_per_m": 2000, "shop": "店名"}
                ※数値は半角数字のみ、解説不要。
                """
                for type, content in inputs:
                    try:
                        if type == "text":
                            response = model.generate_content(prompt + "\n対象:" + content)
                        else:
                            img = Image.open(content)
                            response = model.generate_content([prompt, img])
                        
                        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                        if json_match:
                            results.append(json.loads(json_match.group()))
                    except Exception as e:
                        st.error(f"解析失敗: {e}")

            if results:
                st.success(f"{len(results)}件の解析が完了しました！")
                # ★「コード」ではなく「表」として表示
                df = pd.DataFrame(results)
                df.columns = ["生地名", "素材", "幅", "長さ(cm)", "合計価格", "1m単価", "店名"]
                st.table(df) # 綺麗な表で表示
                st.session_state.results = results

    # 保存機能
    if "results" in st.session_state:
        if st.button("全てスプレッドシートに保存"):
            try:
                sheet = get_spreadsheet()
                today = str(datetime.date.today())
                for d in st.session_state.results:
                    row = [today, d.get("name",""), d.get("material",""), d.get("width",""), 
                           d.get("length",0), d.get("total_price",0), d.get("price_per_m",0), d.get("shop","")]
                    sheet.append_row(row)
                st.success("全て保存しました！")
                st.balloons()
                del st.session_state.results # 重複保存防止
            except Exception as e:
                st.error(f"保存エラー: {e}")

with tab2:
    st.write(f"[スプレッドシートを開く]({SPREADSHEET_URL})")
