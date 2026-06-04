import streamlit as st
from PIL import Image
import numpy as np
import pandas as pd
from datetime import datetime
import os
import io

# =========================
# НАСТРОЙКИ ПРИЛОЖЕНИЯ
# =========================

LOG_FILE = "calculations_log.csv"

st.set_page_config(
    page_title="Калькулятор вышивки",
    layout="centered"
)

st.title("Калькулятор вышивки")

# =========================
# ИНСТРУКЦИЯ
# =========================

with st.expander("Инструкция по пользованию"):
    st.markdown("""
1. Загрузите макет вышивки (PNG, JPG, JPEG)

2. Укажите фактический размер вышивки в сантиметрах

3. Выберите тип вышивки:
• Стандартная — обычная вышивка  
• Мелкий текст и тонкие линии — детали менее 3 мм  
• Плотное заполнение — плашки и заливки  
• Шеврон — нашивки с рамкой  
• 3D — объемная вышивка  

4. Проверьте результат:
• прогноз стежков  
• время производства  
• стоимость  

Важно: расчет предварительный.
""")

# =========================
# ВВОД ДАННЫХ
# =========================

uploaded = st.file_uploader(
    "Загрузить макет",
    type=["png", "jpg", "jpeg"]
)

col1, col2 = st.columns(2)

with col1:
    width_cm = st.number_input(
        "Ширина (см)",
        min_value=0.5,
        value=10.0
    )

with col2:
    height_cm = st.number_input(
        "Высота (см)",
        min_value=0.5,
        value=10.0
    )

price_per_1000 = st.number_input(
    "Цена за 1000 стежков",
    value=45
)

st.subheader("Тип вышивки")

emb_type = st.selectbox(
    "Тип вышивки",
    [
        "Стандартная",
        "Мелкий текст и тонкие линии",
        "Плотное заполнение",
        "3D"
    ]
)

st.info("""
Стандартная — обычная вышивка  
Мелкий текст и тонкие линии — детали <3 мм  
Плотное заполнение — плашки и заливки  
3D — объемная вышивка  
""")

# =========================
# СОХРАНЕНИЕ ИСТОРИИ
# =========================

def save_calculation(data):
    df_new = pd.DataFrame([data])

    if os.path.exists(LOG_FILE):
        try:
            df_old = pd.read_csv(LOG_FILE)
            df = pd.concat([df_old, df_new], ignore_index=True)
        except:
            df = df_new
    else:
        df = df_new

    df.to_csv(LOG_FILE, index=False)

if "last_saved" not in st.session_state:
    st.session_state.last_saved = None

# =========================
# РАСЧЕТ
# =========================

if uploaded:

    image = Image.open(uploaded)
    st.image(image, width=300)

    image_rgba = image.convert("RGBA")
    arr = np.array(image_rgba)

    alpha = arr[:, :, 3]

    filled = np.sum(alpha > 10)
    total = alpha.size

    fill_percent = filled / total

    area = width_cm * height_cm
    real_area = area * fill_percent

    base_density = 250

    if emb_type == "Плотное заполнение":
        base_density = 360
    elif emb_type == "3D":
        base_density = 480

    base_stitches = real_area * base_density

    if emb_type == "Мелкий текст и тонкие линии":
        base_stitches *= 1.2

    stitches = base_stitches

    min_st = stitches * 0.95
    max_st = stitches * 1.05

    prep_time = 5
    machine_time = stitches / 529
    total_time = prep_time + machine_time

    price = (stitches / 1000) * price_per_1000

    # =========================
    # АВТОСОХРАНЕНИЕ
    # =========================

    current_hash = f"{uploaded.name}_{stitches}_{total_time}"

    if st.session_state.last_saved != current_hash:

        save_calculation({
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "emb_type": emb_type,
            "width_cm": width_cm,
            "height_cm": height_cm,
            "fill_percent": round(fill_percent * 100, 2),
            "stitches": int(stitches),
            "time_min": round(total_time, 2),
            "price": round(price, 2)
        })

        st.session_state.last_saved = current_hash

    # =========================
    # РЕЗУЛЬТАТЫ
    # =========================

    st.subheader("Результат")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Стежки",
            f"{int(stitches):,}".replace(",", " ")
        )

    with col2:
        st.metric(
            "Время (мин)",
            f"{total_time:.1f}"
        )

    with col3:
        st.metric(
            "Стоимость",
            f"{price:.0f} ₽"
        )

    st.success(
        f"Прогноз стежков: {int(min_st)} – {int(max_st)}"
    )

    st.write(
        f"Заполненность: {fill_percent*100:.1f}%"
    )

    st.write(
        f"Фактическая площадь: {real_area:.1f} см²"
    )

    # =========================
    # ИСТОРИЯ
    # =========================

    st.subheader("История расчетов")

    if os.path.exists(LOG_FILE):

        df = pd.read_csv(LOG_FILE)

        # =========================
        # ПРЕПОДГОТОВКА ДАТЫ
        # =========================
        df["datetime"] = pd.to_datetime(df["datetime"])
    
        # =========================
        # ФИЛЬТР 1: ТИП ВЫШИВКИ
        # =========================
        emb_filter = st.selectbox(
            "Фильтр по типу вышивки",
            ["Все"] + sorted(df["emb_type"].unique())
        )

        if emb_filter != "Все":
            df = df[df["emb_type"] == emb_filter]

        # =========================
        # ФИЛЬТР 2: ДИАПАЗОН ДАТ
        # =========================
        min_date = df["datetime"].min().date()
        max_date = df["datetime"].max().date()

        date_range = st.date_input(
            "Фильтр по датам",
            value=(min_date, max_date)
        )

        if len(date_range) == 2:
            start_date, end_date = date_range

            df = df[
                (df["datetime"].dt.date >= start_date) &
                (df["datetime"].dt.date <= end_date)
            ]

        # =========================
        # ОГРАНИЧЕНИЕ ВЫВОДА
        # =========================
        df = df.sort_values("datetime", ascending=False).head(50)

        st.dataframe(df)

        # =========================
        # ЭКСПОРТ
        # =========================

        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="history")

        st.download_button(
            label="Скачать историю (Excel)",
            data=buffer.getvalue(),
            file_name="embroidery_history.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.write("Пока нет расчетов")