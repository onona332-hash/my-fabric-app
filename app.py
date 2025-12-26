import streamlit as st
import google.generativeai as genai
from PIL import Image
import gspread
from google.oauth2.service_account import Credentials
import datetime
import json

st.set_page_config(page_title="洋裁在庫ログ", layout="centered")
st.title("🧵 魔法の洋裁ログ (連携版)")

# --- 設定 ---
# ご自身のスプレッドシートのURLを貼り付けてください
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/あなたのシートID/edit"

# 1. Secretsの読み込み（短縮版に対応）
if "GEMINI_API_KEY" not in st.secrets or "SERVICE_ACCOUNT_JSON" not in st.secrets:
    st.error("Secretsの設定が不足しています。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 2. スプレッドシート接続用の関数
def get_spreadsheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # 短縮版のJSON文字列を辞書に戻す
    creds_info = json.loads(st.secrets["SERVICE_ACCOUNT_JSON"])
    # 秘密鍵の欠落を補完（本来は完全なJSONが必要ですが、まずは接続テスト用）
    # ※もしエラーが出る場合は、接続専用の処理をさらに追加します
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_url(SPREADSHEET_URL).sheet1

# 3. モデル選択
model = genai.GenerativeModel('gemini-1.5-flash')

tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    method = st.radio("入力方法", ["テキスト貼り付け", "画像アップロード"])
    text_input = st.text_area("内容") if method == "テキスト貼り付け" else None
    uploaded_file = st.file_uploader("写真") if method == "画像アップロード" else None

    if st.button("AI解析"):
        with st.spinner("解析中..."):
            prompt = """
            以下の情報を抽出し、JSON形式で出力してください。
            {"name": "生地名", "material": "素材", "width": "幅", "length": 100, "total_price": 2000, "price_per_m": 2000, "shop": "店名"}
            """
            if method == "テキスト貼り付け" and text_input:
                response = model.generate_content(prompt + text_input)
            elif method == "画像アップロード" and uploaded_file:
                img = Image.open(uploaded_file)
                response = model.generate_content([prompt, img])
            
            res_text = response.text.replace("```json", "").replace("```", "").strip()
            st.session_state.data = json.loads(res_text)
            st.write("解析結果:", st.session_state.data)

    if "data" in st.session_state:
        if st.button("スプレッドシートに保存"):
            try:
                sheet = get_spreadsheet()
                d = st.session_state.data
                row = [str(datetime.date.today()), d["name"], d["material"], d["width"], d["length"], d["total_price"], d["price_per_m"], d["shop"]]
                sheet.append_row(row)
                st.success("保存完了！")
                st.balloons()
            except Exception as e:
                st.error(f"保存エラー: {e}")

with tab2:
    st.write(f"[スプレッドシートを開く]({SPREADSHEET_URL})")
