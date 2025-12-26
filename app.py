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
model = genai.GenerativeModel('gemini-1.5-flash')

tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    method = st.radio("入力方法を選択", ["テキスト貼り付け", "画像アップロード"])

    if method == "テキスト貼り付け":
        text_input = st.text_area("商品説明を貼り付けてください", height=200)
        if st.button("AIで解析する") and text_input:
            with st.spinner("計算中..."):
                try:
                    # ここから下の行は必ず「半角スペース4つ」で下げています
                    prompt = f"""
                    以下のテキストから生地情報を抽出し、指定のルールで計算して整理してください。
                    
                    【計算ルール】:
                    1. 「数量」と「販売単位（50cmなど）」を掛け合わせて【合計の長さ】を出す。
                    2. 「表示価格」と「数量」を掛け合わせて【購入合計価格】を出す。
                    3. 購入合計価格と合計の長さから【1mあたりの価格】を算出する。
                    
                    出力形式：
                    【生地名】: 
                    【素材】: 
                    【生地幅】: 
                    【購入合計の長さ】: ●cm（数量●個分）
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
            if uploaded_files:
                with st.spinner("画像を解析中..."):
                    try:
                        img = Image.open(uploaded_files[0])
                        prompt = "画像から生地名、素材、幅、価格、そして【1mあたりの価格】を計算して抽出してください。"
                        response = model.generate_content([prompt, img])
                        st.success("解析成功！")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"画像解析エラー: {e}")
