import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime
import json
import re
import requests
import io

st.set_page_config(page_title="洋裁在庫ログ", layout="centered")
st.title("🧵 魔法の洋裁ログ & 制作記録")

# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbytYJFd4jfex8gob7F9GxFhRXvCHdVOdVXovcP4YhuFDxmoaj7Irup6C7VoSJRycd6h/exec"

# 画像リサイズ関数 (起動とアップロードを速くする)
def resize_image(uploaded_file):
    img = Image.open(uploaded_file)
    # 最大幅800pxに縮小
    if img.width > 800:
        ratio = 800 / float(img.width)
        new_height = int(float(img.height) * ratio)
        img = img.resize((800, new_height), Image.LANCZOS)
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()

# API設定
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secretsに GEMINI_API_KEY が設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("models/gemini-1.5-flash")

tab1, tab2, tab3 = st.tabs(["生地登録", "在庫一覧", "制作記録"])

# --- Tab 1: 生地登録 (画像リサイズ対応) ---
with tab1:
    method = st.radio("入力方法", ["画像アップロード", "テキスト貼り付け"])
    
    if method == "画像アップロード":
        files = st.file_uploader("写真アップロード", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if files:
            # プレビュー表示
            st.image(files, width=150)
    else:
        text_input = st.text_area("テキストを入力")

    if st.button("AI解析をスタート"):
        with st.spinner("解析中..."):
            try:
                prompt = '統合してJSONで出力: {"name": "生地名", "material": "素材", "width": "幅", "length": 1.0, "total_price": 2000, "color": "色", "shop": "店名"}'
                if method == "テキスト貼り付け":
                    response = model.generate_content(prompt + text_input)
                else:
                    # リサイズしてからAIに送る
                    img_data = [Image.open(io.BytesIO(resize_image(f))) for f in files]
                    response = model.generate_content([prompt] + img_data)
                
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    st.session_state.temp_data = json.loads(json_match.group())
                    st.success("解析完了！")
                else: st.error("データが見つかりませんでした。")
            except Exception as e:
                st.error(f"解析失敗: {e}")

    # 保存フォーム（中略：以前と同じ内容をここに配置）
    if "temp_data" in st.session_state:
        # (ここには以前の修正・保存コードが入ります)
        st.write("確認して保存ボタンを押してください")
        # 保存ボタン内の処理でも `resize_image` を使って送るようにします

# --- Tab 3: 制作記録 (在庫連動) ---
with tab3:
    st.subheader("👗 完成品の記録")
    
    with st.form("record_form"):
        prod_name = st.text_input("何を作った？ (例: ティアードスカート)")
        pattern_name = st.text_input("使用した型紙 (例: 大人の日常着 P.10)")
        
        # 本来はスプレッドシートから読み込むのが理想ですが、まずは手入力
        used_fabric = st.text_input("使った生地の名前 (在庫一覧からコピー)")
        use_length = st.number_input("使用量 (m)", min_value=0.1, step=0.1)
        
        finished_photo = st.file_uploader("完成写真", type=['jpg', 'jpeg', 'png'])
        
        submitted = st.form_submit_button("制作を記録して在庫を減らす")
        
        if submitted:
            # ここでGASに「制作記録用」の信号を送る
            payload = {
                "type": "production", # 記録の種類を分ける
                "date": str(datetime.date.today()),
                "prod_name": prod_name,
                "pattern": pattern_name,
                "fabric": used_fabric,
                "use_length": use_length
            }
            res = requests.post(GAS_URL, data=json.dumps(payload))
            if res.status_code == 200:
                st.success(f"記録完了！{used_fabric} の在庫を {use_length}m 減らしました。")
                st.balloons()
