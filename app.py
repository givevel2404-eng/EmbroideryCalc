import streamlit as st
from PIL import Image
import numpy as np

st.set_page_config(
    page_title="Калькулятор вышивки",
    layout="wide"
)

st.title("Калькулятор вышивки")

uploaded = st.file_uploader(
    "Загрузить макет",
    type=["png", "jpg", "jpeg"]
)

col1, col2 = st.columns(2)

with col1:

    width_cm = st.number_input(
        "Ширина (см)",
        min_value=1.0,
        value=10.0
    )

with col2:

    height_cm = st.number_input(
        "Высота (см)",
        min_value=1.0,
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
        "Шеврон",
        "3D"
    ]
)

st.info(
"""
Стандартная:
обычная вышивка без особенностей

Мелкий текст и тонкие линии:
детали <3 мм, небольшие надписи

Плотное заполнение:
плашки, большие заливки

Шеврон:
нашивки, плотная заливка + рамка

3D:
объемная вышивка
"""
)

if uploaded:

    image = Image.open(uploaded)

    st.image(
        image,
        width=300
    )

    image_rgba = image.convert("RGBA")

    arr = np.array(image_rgba)

    alpha = arr[:, :, 3]

    filled = np.sum(alpha > 10)

    total = alpha.size

    fill_percent = filled / total

    area = width_cm * height_cm

    real_area = area * fill_percent

    base_density = 300

    if emb_type == "Плотное заполнение":
        base_density = 360

    elif emb_type == "Шеврон":
        base_density = 420

    elif emb_type == "3D":
        base_density = 520

    stitches = real_area * base_density

    if emb_type == "Мелкий текст и тонкие линии":
        stitches *= 1.15

    min_st = stitches * 0.9
    max_st = stitches * 1.1

    prep_time = 5

    machine_time = stitches / 529

    total_time = prep_time + machine_time

    price = (
        stitches / 1000
    ) * price_per_1000

    st.subheader(
        "Результат"
    )

    st.write(
        f"Заполненность: {fill_percent*100:.1f}%"
    )

    st.write(
        f"Фактическая площадь: {real_area:.1f} см²"
    )

    st.write(
        f"Плотность: {base_density} ст/см²"
    )

    st.write(
        f"Прогноз стежков: {int(min_st)} – {int(max_st)}"
    )

    st.write(
        f"Прогноз времени: {total_time:.1f} мин"
    )

    st.write(
        f"Стоимость: {price:.0f}"
    )