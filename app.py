import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Digital Twin Health Risk Analyzer", layout="wide")
st.title("🧬 Digital Twin Health Risk Analyzer (Cancer + Diabetes)")
st.markdown("""
This prototype evaluates **Diabetes** and **Cancer (Pancreatic / Colorectal)** risk  
based on clinical patterns in blood biomarkers and patient profile.
""")

# ============================================================
# 1️⃣ DIGITAL TWIN PROFILE
# ============================================================
st.header("🧍 Create Your Digital Twin")

col1, col2, col3 = st.columns(3)
with col1:
    age = st.number_input("Age (years)", 10, 100, 40)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
with col2:
    height = st.number_input("Height (cm)", 100, 210, 170)
    weight = st.number_input("Weight (kg)", 30, 150, 70)
with col3:
    location = st.text_input("Location / City", "Delhi")
    lifestyle = st.selectbox("Lifestyle", ["Sedentary", "Moderate", "Active"])

bmi = round(weight / ((height / 100) ** 2), 2)
st.metric("Your BMI", bmi)
if bmi >= 25:
    st.warning("Overweight – associated with higher Diabetes & Cancer risk.")
elif bmi < 18.5:
    st.info("Underweight – monitor nutritional status.")
else:
    st.success("Healthy BMI range.")

# ============================================================
# 2️⃣ SYMPTOMS
# ============================================================
st.header("🩺 Symptom Checker")
symptoms = st.multiselect(
    "Select symptoms you are experiencing:",
    [
        "Fatigue", "Unexplained weight loss", "Abdominal pain", "Frequent urination",
        "Loss of appetite", "Blood in stool", "Dark urine", "Cough or chest pain",
        "Slow wound healing", "Vision changes", "Persistent fever"
    ]
)
if len(symptoms) > 0:
    st.info(f"Detected {len(symptoms)} key symptom(s) linked to metabolic or oncologic risk.")

# ============================================================
# 3️⃣ BLOOD DATA INPUT
# ============================================================
st.header("🧪 Enter Blood Test Data")
st.markdown("Enter at least 2 test results (Date, HbA1c, Glucose, Hb, Platelet, WBC, ESR, ALT, AST, Calcium):")

example_data = """2025-08-01, 6.0, 110, 13.8, 220, 6.5, 20, 32, 28, 9.2
2025-10-01, 6.9, 130, 12.6, 265, 8.5, 40, 46, 39, 10.3"""

user_input = st.text_area("Paste your data (comma-separated)", example_data)

try:
    df = pd.read_csv(pd.io.common.StringIO(user_input), header=None)
    df.columns = ["Date", "HbA1c", "Glucose", "Hb", "Platelet", "WBC", "ESR", "ALT", "AST", "Calcium"]
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")
    st.success("✅ Data loaded successfully!")
except Exception as e:
    st.error("❌ Please enter valid comma-separated data.")
    df = None

# ============================================================
# 4️⃣ TREND VISUALIZATION
# ============================================================
if df is not None and len(df) >= 2:
    st.header("📊 Biomarker Trends Over Time")

    for col in df.columns[1:]:
        fig = px.line(df, x="Date", y=col, markers=True, title=f"{col} Trend")
        st.plotly_chart(fig, use_container_width=True)

    # Calculate change (delta)
    last = df.iloc[-1]
    prev = df.iloc[-2]
    change = last - prev

    # ============================================================
    # DIABETES RISK LOGIC
    # ============================================================
    if last["HbA1c"] > 6.5 or last["Glucose"] > 130:
        diabetes_risk = "🔴 High"
    elif last["HbA1c"] > 5.7:
        diabetes_risk = "🟠 Moderate"
    else:
        diabetes_risk = "🟢 Low"

    # ============================================================
    # CANCER RISK LOGIC (Based on Trends + NICE Guidelines)
    # ============================================================
    pancreatic_score = 0
    colorectal_score = 0

    # --- Pancreatic Cancer Indicators ---
    if change["HbA1c"] > 0: pancreatic_score += 1
    if change["Platelet"] > 0: pancreatic_score += 1
    if change["ALT"] > 0 or change["AST"] > 0: pancreatic_score += 1
    if change["WBC"] > 0: pancreatic_score += 1
    if change["ESR"] > 0: pancreatic_score += 1
    if change["Calcium"] > 0: pancreatic_score += 1
    if change["Hb"] < 0: pancreatic_score += 1

    # --- Colorectal Cancer Indicators ---
    if last["Hb"] < (13 if gender == "Male" else 12): colorectal_score += 2  # NICE anemia rule
    if change["Hb"] < 0: colorectal_score += 1
    if change["Platelet"] > 0: colorectal_score += 1
    if change["ESR"] > 0: colorectal_score += 1
    if change["WBC"] > 0: colorectal_score += 1
    if change["Calcium"] > 0: colorectal_score += 1

    # --- ESR logic ---
    if last["ESR"] > 100:
        pancreatic_score += 2
        colorectal_score += 2

    # Qualitative risk
    def risk_label(score):
        if score >= 6: return "🔴 High"
        elif score >= 3: return "🟠 Moderate"
        else: return "🟢 Low"

    pancreatic_risk = risk_label(pancreatic_score)
    colorectal_risk = risk_label(colorectal_score)

    # ============================================================
    # 5️⃣ RESULTS SUMMARY
    # ============================================================
    st.header("🧩 Digital Twin Risk Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Diabetes Risk", diabetes_risk)
    col2.metric("Pancreatic Cancer Risk", pancreatic_risk)
    col3.metric("Colorectal Cancer Risk", colorectal_risk)

    # ============================================================
    # 6️⃣ ORGAN IMPACT MAP
    # ============================================================
    st.header("🧠 Organ Impact Visualization")

    organ_df = pd.DataFrame({
        "Organ": ["Pancreas", "Liver", "Kidney", "Colon", "Heart", "Blood", "Lungs"],
        "Diabetes_Risk": [0.95, 0.7, 0.8, 0.3, 0.6, 0.2, 0.25],
        "Cancer_Risk": [0.8, 0.65, 0.4, 0.85, 0.5, 0.7, 0.9],
    })
    organ_df["Combined_Risk"] = (
        0.6 * organ_df["Diabetes_Risk"] + 0.4 * organ_df["Cancer_Risk"]
    )

    fig = px.bar(
        organ_df,
        x="Organ",
        y="Combined_Risk",
        color="Combined_Risk",
        color_continuous_scale="Reds",
        title="Organ Systems Potentially Affected"
    )
    st.plotly_chart(fig, use_container_width=True)

    # ============================================================
    # 7️⃣ INTERPRETATION
    # ============================================================
    st.subheader("🧠 Clinical Interpretation Summary")
    st.markdown(f"""
    - **HbA1c** rising trend → Insulin resistance & Pancreatic stress  
    - **Declining Hemoglobin (<13/12)** → Anaemia; colorectal cancer flag  
    - **↑ Platelets, ↑ ESR, ↑ WBC** → Inflammatory activity & potential cancer progression  
    - **↑ ALT/AST** → Liver stress or metastasis link  
    - **↑ Calcium** → Possible multiple myeloma or paraneoplastic process  
    - **ESR > 100 mm/hr** → Red flag for malignancy if persistent  
    """)

else:
    st.warning("Please provide at least 2 valid test entries to perform trend analysis.")

st.info("""
**References:**  
- NICE Clinical Guidelines: Colorectal Cancer (NG12)  
- Edgren 2010, Giannakeas 2022, Koshiaris 2018 (Blood trends before cancer diagnosis)  
- ESR as inflammation marker linked to chronic disease progression  
""")
