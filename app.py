import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime
import json
import re
import requests
import io

# --- ページ設定 ---
st.set_page_config(page_title="洋裁在庫ログ", layout="centered")
st.title("🧵 魔法の洋裁ログ (高機能版)")

# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbxGGNgjzjSG6kybCrqC-2yG29wH5BVVqPKKjMbpA8ZzdIV0HvoS_68k3-1TQ1lMDG1m/exec"

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secretsに GEMINI_API_KEY が設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 便利関数 ---

def get_working_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ["models/gemini-1.5-flash", "models/gemini-1.5-flash-latest"]:
            if target in available_models: return genai.GenerativeModel(target)
        return genai.GenerativeModel(available_models[0])
    except:
        return genai.GenerativeModel("models/gemini-1.5-flash")

model = get_working_model()

def resize_image(image_file, max_size=(800, 800)):
    """画像をリサイズしてバイトデータを返す（高速化＆節約用）"""
    img = Image.open(image_file)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img.thumbnail(max_size, Image.LANCZOS)
    return img

# --- タブ構成 ---
tab1, tab2, tab3 = st.tabs(["🆕 情報取得", "📦 在庫一覧", "👗 制作記録"])

# --- Tab 1: 情報取得（画像リサイズ対応） ---
with tab1:
    method = st.radio("入力方法", ["テキスト貼り付け", "画像アップロード"])
    uploaded_files = st.file_uploader("写真アップロード", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True) if method == "画像アップロード" else None
    text_input = st.text_area("テキスト") if method == "テキスト貼り付け" else None

    if st.button("AI解析をスタート"):
        if (method == "テキスト貼り付け" and text_input) or (method == "画像アップロード" and uploaded_files):
            with st.spinner("画像を最適化して解析中..."):
                try:
                    prompt = '統合してJSONで出力: {"name": "生地名", "material": "素材", "width": "幅", "length": 1.0, "total_price": 2000, "color": "色", "shop": "店名"}'
                    if method == "テキスト貼り付け":
                        response = model.generate_content(prompt + text_input)
                    else:
                        # ここでリサイズを実行（劇的に軽くなります）
                        img_list = [resize_image(f) for f in uploaded_files]
                        response = model.generate_content([prompt] + img_list)
                    
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if json_match:
                        st.session_state.temp_data = json.loads(json_match.group())
                        st.success("解析完了！")
                    else:
                        st.error("解析結果が見つかりませんでした。")
                except Exception as e:
                    st.error(f"解析失敗: {e}")

    if "temp_data" in st.session_state:
        st.divider()
        st.subheader("📝 データの確認・修正")
        d = st.session_state.temp_data
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("生地名", value=str(d.get("name", "")))
            material = st.text_input("素材", value=str(d.get("material", "")))
            color = st.text_input("色", value=str(d.get("color", "")))
            shop = st.text_input("購入店", value=str(d.get("shop", "")))
        with col2:
            width = st.text_input("幅", value=str(d.get("width", "")))
            l_val = float(d.get("length", 1.0)) if isinstance(d.get("length"), (int, float)) else 1.0
            p_val = int(d.get("total_price", 0)) if isinstance(d.get("total_price"), (int, float)) else 0
            
            length_m = st.number_input("数量(m)", value=l_val, step=0.1)
            total_price = st.number_input("合計価格", value=p_val, step=10)
            price_per_m = int(total_price / length_m) if length_m > 0 else 0
            st.metric("1m単価", f"{price_per_m}円")

        if st.button("スプレッドシートに保存"):
            try:
                payload = {
                    "action": "add_inventory",
                    "date": str(datetime.date.today()),
                    "name": name,
                    "material": material,
                    "color": color,
                    "width": width,
                    "length": length_m,
                    "price": total_price,
                    "unit_price": price_per_m,
                    "shop": shop
                }
                response = requests.post(GAS_URL, data=json.dumps(payload))
                if response.status_code == 200:
                    st.success("在庫を保存しました！")
                    st.balloons()
                    del st.session_state.temp_data
                else:
                    st.error(f"保存失敗: {response.status_code}")
            except Exception as e:
                st.error(f"エラー: {e}")

# --- Tab 2: 在庫一覧 ---
with tab2:
    st.write("スプレッドシートを開いて在庫を確認してください。")
    st.info("GAS側を更新すると、ここに一覧を表示できるようになります。")

# --- Tab 3: 制作記録 & 数計算 ---
with tab3:
    st.subheader("✂️ 制作の記録と在庫引き落とし")
    
    col_a, col_b = st.columns(2)
    with col_a:
        prod_name = st.text_input("作ったもの (例: タックスカート)")
        # 本来は在庫リストを取得して選ぶのが理想。一旦手入力。
        target_fabric = st.text_input("使用した生地の名前（在庫と一致させてください）")
    with col_b:
        used_length = st.number_input("使用量 (m)", min_value=0.0, step=0.1)
        prod_date = st.date_input("完成日", datetime.date.today())

    prod_img = st.file_uploader("完成写真の保存", type=['jpg', 'jpeg', 'png'])

    if st.button("制作を確定して在庫を減らす"):
        if prod_name and target_fabric and used_length > 0:
            with st.spinner("記録中..."):
                # 画像のリサイズ（完成品写真も軽量化）
                img_data = None
                if prod_img:
                    resized_img = resize_image(prod_img)
                    # 必要に応じて画像をGASに送るロジックをここに追加
                
                payload = {
                    "action": "log_production",
                    "date": str(prod_date),
                    "item_name": prod_name,
                    "fabric_name": target_fabric,
                    "used_length": used_length
                }
                
                try:
                    response = requests.post(GAS_URL, data=json.dumps(payload))
                    if response.status_code == 200:
                        st.success(f"『{prod_name}』を記録し、在庫を {used_length}m 差し引きました！")
                        # 簡易的な計算表示
                        st.metric("今回の消費量", f"{used_length} m")
                    else:
                        st.error("GAS側の更新が必要です。")
                except Exception as e:
                    st.error(f"接続エラー: {e}")
        else:
            st.warning("「作ったもの」「生地名」「使用量」を正しく入力してください。")
