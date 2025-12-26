import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="洋裁在庫ログ", layout="centered")
st.title("🧵 魔法の洋裁ログ (自動修正版)")

# APIキーの読み込み
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secretsに 'GEMINI_API_KEY' が設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- モデルを自動で選ぶ関数 ---
def get_available_model():
    # 試したいモデル候補のリスト
    candidates = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro']
    
    available_models = []
    try:
        # 実際に使えるモデルを一覧取得
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # 候補の中から最初に見つかったものを使う
        for cand in candidates:
            # list_modelsの結果は 'models/gemini-1.5-flash' のような形式
            full_name = f"models/{cand}"
            if full_name in available_models:
                return genai.GenerativeModel(full_name)
        
        # 候補になければ、一番最初にある生成可能モデルを返す
        if available_models:
            return genai.GenerativeModel(available_models[0])
    except:
        pass
    
    # 万が一リストが取れなかったら、標準的なものをとりあえず返す
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_available_model()

# 現在どのモデルが選ばれているか、こっそり表示（デバッグ用）
# st.write(f"使用中モデル: {model.model_name}")

tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    method = st.radio("入力方法を選択", ["テキスト貼り付け", "画像アップロード"])

    if method == "テキスト貼り付け":
        text_input = st.text_area("商品説明を貼り付けてください", height=200)
        if st.button("AIで解析する") and text_input:
            with st.spinner("解析中..."):
                try:
                    # --- ご指定のプロンプトに差し替えました ---
                    prompt = f"""
                    以下のテキストから生地情報を抽出し、指定のルールで計算して整理してください。

                    【計算ルール】:
                    1. 「数量」と「販売単位（50cmなど）」を掛け合わせて【合計の長さ】を出す。
                    2. 「表示価格」と「数量」を掛け合わせて【購入合計価格】を出す。
                    3. 購入合計価格と合計の長さから【1mあたりの価格】を算出する。
                       （例：50cmで869円なら、1mあたり1,738円）

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
                    st.success("解析できました！")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"解析エラー: {e}")
                    st.info("APIキーを [Google AI Studio](https://aistudio.google.com/app/apikey) で作り直して、Secretsに貼り直してみてください。")

    else:
        uploaded_files = st.file_uploader("写真を選択", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if st.button("画像から情報を抽出") and uploaded_files:
            with st.spinner("画像を解析中..."):
                try:
                    img = Image.open(uploaded_files[0])
                    prompt = "この画像から生地情報を抽出してください。"
                    response = model.generate_content([prompt, img])
                    st.success("読み取り成功！")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"画像解析エラー: {e}")

with tab2:
    st.info("解析に成功したら、スプレッドシートへの保存機能を追加しましょう！")
