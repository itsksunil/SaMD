import streamlit as st
import pandas as pd
import plotly.express as px
import fitz  # PyMuPDF
import re
from datetime import datetime

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="Digital Twin Health Risk Analyzer", layout="wide")
st.title("🧬 Digital Twin Health Risk Analyzer (SAMD Prototype)")
st.markdown("""
Create your **Digital Twin**, upload lab reports, add manual data, analyze trends, and get **Diabetes & Cancer risk assessment**.
""")

# ----------------------------
# 1️⃣ Digital Twin Profile
# ----------------------------
st.header("1️⃣ Create Your Digital Twin")
col1, col2, col3 = st.columns(3)
age = col1.number_input("Age", 0, 120, 45)
gender = col2.selectbox("Gender", ["Male", "Female", "Other"])
height = col3.number_input("Height (cm)", 50, 250, 170)

col4, col5, col6 = st.columns(3)
weight = col4.number_input("Weight (kg)", 10, 200, 70)
location = col5.text_input("Location", "Mumbai")
activity = col6.selectbox("Activity Level", ["Low", "Moderate", "High"])

bmi = round(weight / ((height / 100) ** 2), 2)
st.metric("Your BMI", bmi)

# ----------------------------
# 2️⃣ Lab Test Selection
# ----------------------------
all_tests = ["HbA1c", "Glucose", "Hb", "Platelet", "WBC", "ESR",
             "ALT", "AST", "Calcium", "PSA", "Weight", "Date",
             "TSH", "T3", "T4", "Neutrophils", "Lymphocytes", "Monocytes"]

selected_tests = st.multiselect(
    "Select lab tests to extract from PDF",
    all_tests,
    default=["HbA1c","Glucose","Hb","Platelet","WBC","ESR","ALT","AST","Calcium","PSA","Weight","Date"]
)

# ----------------------------
# 3️⃣ Upload PDF Lab Reports
# ----------------------------
uploaded_files = st.file_uploader(
    "Upload lab reports (PDF) - multiple allowed", 
    type="pdf", 
    accept_multiple_files=True
)

# ----------------------------
# PDF TEXT EXTRACTION FUNCTION
# ----------------------------
def extract_text_from_pdf(file):
    doc = fitz.open(file)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# ----------------------------
# DYNAMIC LAB VALUE EXTRACTION
# ----------------------------
def extract_lab_values_dynamic(text, tests):
    lab_data = {}
    for test in tests:
        pattern = rf"{test}[:\s]*([\d.,]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(",", "")
            try:
                lab_data[test] = float(value)
            except:
                lab_data[test] = value
    return lab_data

# ----------------------------
# 4️⃣ Initialize DataFrame
# ----------------------------
df_all = pd.DataFrame()

# Process PDFs
if uploaded_files:
    for file in uploaded_files:
        text = extract_text_from_pdf(file)
        data = extract_lab_values_dynamic(text, selected_tests)
        df_all = pd.concat([df_all, pd.DataFrame([data])], ignore_index=True)

# ----------------------------
# 5️⃣ Manual Data Entry
# ----------------------------
st.header("📋 Manual Lab Data Entry (Optional)")
with st.form("manual_entry_form"):
    col1, col2, col3 = st.columns(3)
    manual_date = col1.date_input("Date", datetime.today())
    manual_hba1c = col2.text_input("HbA1c", "")
    manual_glucose = col3.text_input("Glucose", "")

    col4, col5, col6 = st.columns(3)
    manual_hb = col4.text_input("Hb", "")
    manual_platelet = col5.text_input("Platelet", "")
    manual_wbc = col6.text_input("WBC", "")

    col7, col8, col9 = st.columns(3)
    manual_esr = col7.text_input("ESR", "")
    manual_alt = col8.text_input("ALT", "")
    manual_ast = col9.text_input("AST", "")

    col10, col11 = st.columns(2)
    manual_calcium = col10.text_input("Calcium", "")
    manual_weight = col11.text_input("Weight", "")

    submit_button = st.form_submit_button("Add Manual Entry")

# Append manual data to df_all
manual_data = {}
if submit_button:
    manual_data["Date"] = pd.to_datetime(manual_date)
    if manual_hba1c: manual_data["HbA1c"] = float(manual_hba1c)
    if manual_glucose: manual_data["Glucose"] = float(manual_glucose)
    if manual_hb: manual_data["Hb"] = float(manual_hb)
    if manual_platelet: manual_data["Platelet"] = float(manual_platelet)
    if manual_wbc: manual_data["WBC"] = float(manual_wbc)
    if manual_esr: manual_data["ESR"] = float(manual_esr)
    if manual_alt: manual_data["ALT"] = float(manual_alt)
    if manual_ast: manual_data["AST"] = float(manual_ast)
    if manual_calcium: manual_data["Calcium"] = float(manual_calcium)
    if manual_weight: manual_data["Weight"] = float(manual_weight)

    if df_all.empty:
        df_all = pd.DataFrame([manual_data])
    else:
        df_all = pd.concat([df_all, pd.DataFrame([manual_data])], ignore_index=True)

    if "Date" in df_all.columns:
        df_all = df_all.sort_values("Date")
    st.success("Manual entry added successfully!")

# ----------------------------
# 6️⃣ Display Data
# ----------------------------
if not df_all.empty:
    st.subheader("Merged Lab Data")
    st.dataframe(df_all)

    # ----------------------------
    # Trend Visualization
    # ----------------------------
    st.subheader("Trend Visualization")
    numeric_cols = df_all.select_dtypes(include='number').columns
    for col in numeric_cols:
        fig = px.line(
            df_all, 
            x="Date" if "Date" in df_all.columns else df_all.index,
            y=col, 
            title=f"{col} Trend", 
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

    # Increase/Decrease Alerts
    if len(df_all) >= 2:
        last = df_all.iloc[-1]
        prev = df_all.iloc[-2]
        st.subheader("Increase/Decrease Alerts (Last Entry vs Previous)")
        alerts = {}
        for col in numeric_cols:
            delta = last[col] - prev[col]
            if delta > 0:
                alerts[col] = f"⬆ Increased by {delta}"
            elif delta < 0:
                alerts[col] = f"⬇ Decreased by {abs(delta)}"
            else:
                alerts[col] = "No change"
        st.write(alerts)

    # ----------------------------
    # Diabetes Risk Scoring
    # ----------------------------
    st.subheader("Diabetes Risk Assessment")
    diabetes_risk = "Unknown"
    if "HbA1c" in df_all.columns and "Glucose" in df_all.columns:
        last_hba1c = df_all["HbA1c"].iloc[-1]
        last_glucose = df_all["Glucose"].iloc[-1]
        if last_hba1c > 6.5 or last_glucose > 130:
            diabetes_risk = "🔴 High"
        elif last_hba1c > 5.7:
            diabetes_risk = "🟠 Moderate"
        else:
            diabetes_risk = "🟢 Low"
    st.metric("Diabetes Risk", diabetes_risk)

    # ----------------------------
    # Cancer Risk Scoring
    # ----------------------------
    st.subheader("Cancer Risk Assessment")
    pancreatic_risk_score = 0
    colorectal_risk_score = 0
    if len(df_all) >= 2:
        last = df_all.iloc[-1]
        prev = df_all.iloc[-2]
        change = last - prev

        # Pancreatic Cancer Indicators
        if "HbA1c" in change.index and change["HbA1c"] > 0: pancreatic_risk_score += 1
        if "Platelet" in change.index and change["Platelet"] > 0: pancreatic_risk_score += 1
        if ("ALT" in change.index and change["ALT"] > 0) or ("AST" in change.index and change["AST"] > 0): pancreatic_risk_score += 1
        if ("WBC" in change.index and change["WBC"] > 0) or ("Monocytes" in change.index and "Monocytes" in df_all.columns and change["Monocytes"] > 0): pancreatic_risk_score += 1
        if "Calcium" in change.index and change["Calcium"] > 0: pancreatic_risk_score += 1
        if "Hb" in change.index and change["Hb"] < 0: pancreatic_risk_score += 1

        # Colorectal Cancer Indicators
        if "Hb" in change.index and change["Hb"] < 0: colorectal_risk_score += 1
        if "Platelet" in change.index and change["Platelet"] > 0: colorectal_risk_score += 1
        if "WBC" in change.index and change["WBC"] > 0: colorectal_risk_score += 1
        if "Calcium" in change.index and change["Calcium"] > 0: colorectal_risk_score += 1

    def get_risk_label(score):
        if score >= 5: return "🔴 High"
        elif score >= 3: return "🟠 Moderate"
        else: return "🟢 Low"

    pancreatic_risk = get_risk_label(pancreatic_risk_score)
    colorectal_risk = get_risk_label(colorectal_risk_score)

    st.metric("Pancreatic Cancer Risk", pancreatic_risk)
    st.metric("Colorectal Cancer Risk", colorectal_risk)

    # ----------------------------
    # Excel Download
    # ----------------------------
    st.subheader("📥 Download Data")
    df_to_download = df_all.copy()
    df_to_download["Date"] = df_to_download["Date"].astype(str)
    st.download_button(
        label="Download as Excel",
        data=df_to_download.to_excel(index=False, engine='openpyxl'),
        file_name="digital_twin_lab_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Upload PDF lab reports or add manual entries to analyze trends.")
