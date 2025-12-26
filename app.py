import streamlit as st
import google.generativeai as genai
from PIL import Image
import gspread
from google.oauth2.service_account import Credentials
import datetime
import json
import re

st.set_page_config(page_title="洋裁在庫ログ", layout="centered")
st.title("🧵 魔法の洋裁ログ (連携版)")

# --- 設定 ---
# ご自身のスプレッドシートのURLを貼り付けてください
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/あなたのシートID/edit"

# 1. Secretsの読み込み
if "GEMINI_API_KEY" not in st.secrets or "SERVICE_ACCOUNT_JSON" not in st.secrets:
    st.error("Secretsの設定が不足しています。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 2. スプレッドシート接続用の関数
def get_spreadsheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = json.loads(st.secrets["SERVICE_ACCOUNT_JSON"])
    # 接続テスト用（保存時に鍵が必要な場合は別途修正します）
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_url(SPREADSHEET_URL).sheet1

# 3. モデル選択
model = genai.GenerativeModel('gemini-1.5-flash')

tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    method = st.radio("入力方法", ["テキスト貼り付け", "画像アップロード"])
    text_input = st.text_area("内容") if method == "テキスト貼り付け" else None
    uploaded_file = st.file_uploader("写真", type=['png', 'jpg', 'jpeg']) if method == "画像アップロード" else None

    if st.button("AI解析"):
        if (method == "テキスト貼り付け" and text_input) or (method == "画像アップロード" and uploaded_file):
            with st.spinner("解析中..."):
                try:
                    prompt = """
                    以下の情報を抽出し、必ずJSON形式のみで出力してください。余計な解説は不要です。
                    {"name": "生地名", "material": "素材", "width": "幅", "length": 100, "total_price": 2000, "price_per_m": 2000, "shop": "店名"}
                    
                    ※数量と単位(50cm等)から合計長(cm)を出し、単価と数量から合計価格を出し、1mあたりの価格も計算してください。
                    """
                    
                    if method == "テキスト貼り付け":
                        response = model.generate_content(prompt + "\n解析対象:" + text_input)
                    else:
                        img = Image.open(uploaded_file)
                        response = model.generate_content([prompt, img])
                    
                    # --- エラー回避の処理 ---
                    if response and response.text:
                        # 記号などを取り除いてJSON部分だけを抜き出す
                        json_str = re.search(r'\{.*\}', response.text, re.DOTALL)
                        if json_str:
                            st.session_state.data = json.loads(json_str.group())
                            st.success("解析完了！")
                            st.write(st.session_state.data)
                        else:
                            st.error("AIの回答からデータが見つかりませんでした。もう一度お試しください。")
                            st.write("AIの回答:", response.text)
                    
                except Exception as e:
                    st.error(f"解析エラーが発生しました: {e}")
        else:
            st.warning("内容を入力するか、写真をアップロードしてください。")

    # 保存ボタン
    if "data" in st.session_state:
        if st.button("スプレッドシートに保存"):
            try:
                sheet = get_spreadsheet()
                d = st.session_state.data
                row = [
                    str(datetime.date.today()), 
                    d.get("name", ""), 
                    d.get("material", ""), 
                    d.get("width", ""), 
                    d.get("length", 0), 
                    d.get("total_price", 0), 
                    d.get("price_per_m", 0), 
                    d.get("shop", "")
                ]
                sheet.append_row(row)
                st.success("スプレッドシートに保存しました！")
                st.balloons()
            except Exception as e:
                st.error(f"保存エラー: {e}")
                st.info("※サービスアカウントの権限設定や、Secretsの鍵情報が不足している可能性があります。")

with tab2:
    st.write(f"[スプレッドシートを開く]({SPREADSHEET_URL})")
