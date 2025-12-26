import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="洋裁在庫ログ", layout="centered")
st.title("🧵 魔法の洋裁ログ")

# APIキー設定
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secretsにキーが設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 動くモデルを自動で探す関数 ---
def get_working_model():
    candidates = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro']
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    for cand in candidates:
        full_name = f"models/{cand}"
        if full_name in available_models:
            return genai.GenerativeModel(full_name)
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_working_model()

tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    method = st.radio("入力方法を選択", ["テキスト貼り付け", "画像アップロード"])

    if method == "テキスト貼り付け":
        text_input = st.text_area("商品説明を貼り付けてください", height=200)
        if st.button("AIで解析する") and text_input:
            with st.spinner("計算中..."):
                try:
                    # 1m単価の計算ルールを指示
                    prompt = f"""
                    以下のテキストから生地情報を抽出し、整理してください。
                    
                    【計算ルール】:
                    1. 「数量」と「販売単位（50cmなど）」から【合計の長さ】を算出。
                    2. 「表示価格」と「数量」から【購入合計価格】を算出。
                    3. 合計価格と合計の長さから【1mあたりの価格】を算出。
                    
                    出力形式：
                    【生地名】: 
                    【素材】: 
                    【生地幅】: 
                    【購入合計の長さ】: ●cm
                    【購入合計価格】: ●円
                    【1mあたりの価格】: ●円/m
                    【ショップ名】:
                    
                    テキスト:
                    {text_input}
                    """
                    response = model.generate_content(prompt)
                    st.success("解析完了！")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

    else:
        uploaded_files = st.file_uploader("写真を選択", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if st.button("画像から解析") and uploaded_files:
            with st.spinner("画像を解析中..."):
                try:
                    img = Image.open(uploaded_files[0])
                    prompt = "生地名、素材、幅、購入価格、そして【1mあたりの価格】を計算して抽出してください。"
                    response = model.generate_content([prompt, img])
                    st.success("解析成功！")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"画像解析エラー: {e}")

with tab2:
    st.info("これが動いたら、次はいよいよスプレッドシート保存です！")
