import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Digital Twin Health Risk Analyzer", layout="wide")
st.title("🧬 Digital Twin Health Risk Analyzer (Diabetes + Cancer)")
st.markdown("""
This prototype evaluates **Diabetes** and **Cancer** risk based on blood biomarkers, symptoms, weight trends, and patient profile, linking to **likely genes** involved.
""")

# -------------------------------------------------
# SECTION 1: USER PROFILE
# -------------------------------------------------
st.header("1️⃣ Create Your Digital Twin Profile")

col1, col2, col3 = st.columns(3)
age = col1.number_input("Age", 1, 100, 45)
gender = col2.selectbox("Gender", ["Male", "Female", "Other"])
height = col3.number_input("Height (cm)", 100, 220, 170)

col4, col5, col6 = st.columns(3)
weight_current = col4.number_input("Current Weight (kg)", 20, 300, 70)
location = col5.text_input("Location", "Mumbai")
activity = col6.selectbox("Activity Level", ["Low", "Moderate", "High"])

bmi = round(weight_current / ((height / 100) ** 2), 2)
st.metric("Your BMI", bmi)

# -------------------------------------------------
# SECTION 2: SYMPTOMS INPUT
# -------------------------------------------------
st.header("2️⃣ Enter Your Symptoms")

diabetes_symptoms = st.multiselect("Select Diabetes-related symptoms", [
    "Frequent urination (polyuria)",
    "Excessive thirst (polydipsia)",
    "Fatigue",
    "Blurred vision",
    "Unexplained weight loss",
    "Slow healing of wounds",
    "Frequent infections",
])

cancer_symptoms = st.multiselect("Select Cancer-related symptoms", [
    "Abdominal pain",
    "Weight loss",
    "Fatigue",
    "Jaundice",
    "Blood in stool",
    "Constipation/Diarrhea",
    "Difficulty urinating",
    "Pelvic pain"
])

# -------------------------------------------------
# SECTION 3: BLOOD TEST + WEIGHT INPUT
# -------------------------------------------------
st.header("3️⃣ Enter Blood Test Data Over Time")

st.markdown("""
Enter at least **2 test results** to analyze trends.  
Each entry includes: Date, Weight, HbA1c, Glucose, Hb, Platelet, WBC, ESR, ALT, AST, Calcium, PSA
""")

# --- Textbox for bulk input ---
raw_data = st.text_area(
    "📋 Paste your data here (comma-separated, each line = one test record)",
    value="2025-09-01,70,6.1,120,13.8,180000,6.2,12,30,28,9.2,2.0\n2025-10-01,69,6.8,140,12.9,210000,7.8,20,45,40,10.1,3.1",
    height=150
)

data_list = []
for line in raw_data.strip().split("\n"):
    parts = [p.strip() for p in line.split(",")]
    if len(parts) == 12:
        try:
            data_list.append({
                "Date": pd.to_datetime(parts[0]),
                "Weight": float(parts[1]),
                "HbA1c": float(parts[2]),
                "Glucose": float(parts[3]),
                "Hb": float(parts[4]),
                "Platelet": float(parts[5]),
                "WBC": float(parts[6]),
                "ESR": float(parts[7]),
                "ALT": float(parts[8]),
                "AST": float(parts[9]),
                "Calcium": float(parts[10]),
                "PSA": float(parts[11]),
            })
        except:
            st.warning(f"⚠️ Invalid entry skipped: {line}")

data_df = pd.DataFrame(data_list)

# --- Manual entry form ---
st.markdown("### ➕ Add New Test Entry")
with st.form("manual_entry"):
    c1, c2, c3 = st.columns(3)
    date = c1.date_input("Date", datetime.today())
    weight = c2.number_input("Weight (kg)", 10, 300, 70)
    hba1c = c3.number_input("HbA1c (%)", 0.0, 100.0, 6.0, step=0.1)

    c4, c5, c6 = st.columns(3)
    glucose = c4.number_input("Glucose (mg/dL)", 0, 1000, 120)
    hb = c5.number_input("Hemoglobin (g/dL)", 0.0, 30.0, 13.0)
    platelet = c6.number_input("Platelet (per µL)", 0, 2000000, 200000)

    c7, c8, c9 = st.columns(3)
    wbc = c7.number_input("WBC (×10⁹/L)", 0.0, 100.0, 7.0)
    esr = c8.number_input("ESR (mm/hr)", 0.0, 200.0, 10.0)
    alt = c9.number_input("ALT (U/L)", 0.0, 500.0, 30.0)

    ast = st.number_input("AST (U/L)", 0.0, 500.0, 28.0)
    calcium = st.number_input("Calcium (mg/dL)", 0.0, 20.0, 9.5)
    psa = st.number_input("PSA (ng/mL)", 0.0, 1000.0, 2.0)

    submit = st.form_submit_button("Add Entry")

if submit:
    new_row = {
        "Date": pd.to_datetime(date),
        "Weight": weight,
        "HbA1c": hba1c,
        "Glucose": glucose,
        "Hb": hb,
        "Platelet": platelet,
        "WBC": wbc,
        "ESR": esr,
        "ALT": alt,
        "AST": ast,
        "Calcium": calcium,
        "PSA": psa
    }
    data_df = pd.concat([data_df, pd.DataFrame([new_row])], ignore_index=True)

if not data_df.empty:
    data_df = data_df.sort_values("Date")
    st.dataframe(data_df)
else:
    st.warning("Please add at least 2 test records for analysis.")

# -------------------------------------------------
# SECTION 4: TREND ANALYSIS + RISK
# -------------------------------------------------
if len(data_df) >= 2:
    df = data_df.copy()
    df = df.sort_values("Date")
    last = df.iloc[-1]
    prev = df.iloc[-2]
    change = last - prev

    # --------------------------
    # Diabetes Risk
    # --------------------------
    if last["HbA1c"] > 6.5 or last["Glucose"] > 130:
        diabetes_risk = "🔴 High"
    elif last["HbA1c"] > 5.7:
        diabetes_risk = "🟠 Moderate"
    else:
        diabetes_risk = "🟢 Low"

    # Weight trend
    if change["Weight"] < -2:
        weight_trend = "⚠️ Rapid weight loss"
    elif change["Weight"] > 2:
        weight_trend = "⚠️ Rapid weight gain"
    else:
        weight_trend = "Stable"

    # Diabetes Type Prediction
    diabetes_type = "Unknown"
    if age < 25 and bmi < 25 and "Frequent urination (polyuria)" in diabetes_symptoms:
        diabetes_type = "T1D"
    elif age >= 25 and bmi >= 25:
        diabetes_type = "T2D"
    if "Gestational diabetes" in diabetes_symptoms:
        diabetes_type = "GDM"
    if len(diabetes_symptoms) > 0 and age < 25:
        diabetes_type = "MODY"

    # Diabetes Gene Mapping
    diabetes_genes = {
        "T1D": ["HLA-DQA1", "HLA-DQB1", "HLA-DRB1", "CTLA4", "IL2RA", "PTPN22", "INS"],
        "T2D": ["TCF7L2", "PPARG", "KCNJ11", "ABCC8", "LCAT", "APOE", "FTO", "IRS1", "IRS2", "WFS1", "HNF1A", "HNF4A"],
        "GDM": ["MTNR1B", "CDKAL1", "IRS1"],
        "MODY": ["HNF4A", "HNF1A", "HNF1B"]
    }
    predicted_genes = diabetes_genes.get(diabetes_type, [])

    # --------------------------
    # Cancer Risk
    # --------------------------
    pancreatic_score = 0
    colorectal_score = 0

    if change["HbA1c"] > 0: pancreatic_score += 1
    if change["Platelet"] > 0: pancreatic_score += 1
    if change["ALT"] > 0 or change["AST"] > 0: pancreatic_score += 1
    if change["WBC"] > 0: pancreatic_score += 1
    if change["ESR"] > 0: pancreatic_score += 1
    if change["Calcium"] > 0: pancreatic_score += 1
    if change["Hb"] < 0: pancreatic_score += 1

    if change["Hb"] < 0: colorectal_score += 1
    if change["Platelet"] > 0: colorectal_score += 1
    if change["WBC"] > 0: colorectal_score += 1
    if change["ESR"] > 0: colorectal_score += 1
    if change["Calcium"] > 0: colorectal_score += 1

    def risk_label(score):
        if score >= 5: return "🔴 High"
        elif score >= 3: return "🟠 Moderate"
        else: return "🟢 Low"

    pancreatic_risk = risk_label(pancreatic_score)
    colorectal_risk = risk_label(colorectal_score)

    # Cancer Gene Mapping
    cancer_gene_map = {
        "Pancreatic": ["KRAS", "TP53", "CDKN2A", "SMAD4", "BRCA2"],
        "Colorectal": ["APC", "TP53", "KRAS", "PIK3CA", "MLH1"],
        "Prostate": ["BRCA2", "TP53", "PTEN", "AR", "HOXB13"],
        "Liver": ["TP53", "CTNNB1", "AXIN1", "TERT"]
    }

    cancer_genes = []
    if pancreatic_risk != "🟢 Low": cancer_genes += cancer_gene_map["Pancreatic"]
    if colorectal_risk != "🟢 Low": cancer_genes += cancer_gene_map["Colorectal"]
    if last.get("PSA",0) > 4: cancer_genes += cancer_gene_map["Prostate"]
    if last.get("ALT",0) > 60 or last.get("AST",0) > 60: cancer_genes += cancer_gene_map["Liver"]
    cancer_genes = list(set(cancer_genes))

    # -------------------------------------------------
    # TREND CHARTS
    # -------------------------------------------------
    st.header("4️⃣ Trend Visualization")
    numeric_cols = df.select_dtypes(include=np.number).columns
    for col in numeric_cols:
        fig = px.line(df, x="Date", y=col, title=f"{col} Trend Over Time", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------
    # SUMMARY METRICS
    # -------------------------------------------------
    st.header("5️⃣ Risk Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Diabetes Risk", diabetes_risk)
    col2.metric("Weight Trend", weight_trend)
    col3.metric("BMI", bmi)

    st.subheader("Predicted Type of Diabetes")
    st.write(diabetes_type)

    st.subheader("🧬 Genes Likely Involved in Diabetes")
    st.write(", ".join(predicted_genes) if predicted_genes else "No specific gene prediction")

    st.subheader("🧬 Genes Likely Involved in Cancer")
    st.write(", ".join(cancer_genes) if cancer_genes else "No specific gene prediction")

    st.subheader("📊 Interpretation Summary")
    st.markdown(f"""
    **Activity Level:** {activity}  
    **Diabetes trend:** {diabetes_risk}  
    **Pancreatic Cancer trend:** {pancreatic_risk}  
    **Colorectal Cancer trend:** {colorectal_risk}  
    """)
else:
    st.warning("Please enter at least 2 blood test records to perform trend analysis.")
