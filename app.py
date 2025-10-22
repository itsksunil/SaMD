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
Create your **Digital Twin**, upload lab reports, analyze trends, and get **Diabetes & Cancer risk assessment**.
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
             "TSH", "T3", "T4", "Neutrophils", "Lymphocytes", "Monocytes"]  # Extendable

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
# 4️⃣ Process Uploaded PDFs
# ----------------------------
df_all = pd.DataFrame()
if uploaded_files:
    for file in uploaded_files:
        text = extract_text_from_pdf(file)
        data = extract_lab_values_dynamic(text, selected_tests)
        df_all = pd.concat([df_all, pd.DataFrame([data])], ignore_index=True)

    # Convert Date to datetime
    if "Date" in df_all.columns:
        df_all['Date'] = pd.to_datetime(df_all['Date'], errors='coerce')
        df_all = df_all.sort_values('Date')

    st.subheader("Extracted Lab Data")
    st.dataframe(df_all)

    # ----------------------------
    # 5️⃣ Trend Analysis
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
    # 6️⃣ Diabetes Risk Scoring
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
    # 7️⃣ Cancer Risk Scoring (Pancreatic + Colorectal)
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
        if ("WBC" in change.index and change["WBC"] > 0) or ("Monocytes" in change.index and change["Monocytes"] > 0): pancreatic_risk_score += 1
        if "Calcium" in change.index and change["Calcium"] > 0: pancreatic_risk_score += 1
        if "Hb" in change.index and change["Hb"] < 0: pancreatic_risk_score += 1

        # Colorectal Cancer Indicators
        if "Hb" in change.index and change["Hb"] < 0: colorectal_risk_score += 1
        if "Platelet" in change.index and change["Platelet"] > 0: colorectal_risk_score += 1
        if "WBC" in change.index and change["WBC"] > 0: colorectal_risk_score += 1
        if "Calcium" in change.index and change["Calcium"] > 0: colorectal_risk_score += 1

        # Risk labels
        def get_risk_label(score):
            if score >= 5: return "🔴 High"
            elif score >= 3: return "🟠 Moderate"
            else: return "🟢 Low"

        pancreatic_risk = get_risk_label(pancreatic_risk_score)
        colorectal_risk = get_risk_label(colorectal_risk_score)

        col1, col2 = st.columns(2)
        col1.metric("Pancreatic Cancer Risk", pancreatic_risk)
        col2.metric("Colorectal Cancer Risk", colorectal_risk)

    # ----------------------------
    # 8️⃣ Gene Association Mapping (Example)
    # ----------------------------
    st.subheader("Gene Associations (Example)")
    gene_associations = {
        "Type 1 Diabetes": ["HLA-DQA1", "HLA-DQB1", "HLA-DRB1", "CTLA4", "IL2RA", "PTPN22"],
        "Type 2 Diabetes": ["TCF7L2", "PPARG", "KCNJ11", "ABCC8", "LCAT", "APOE", "FTO", "IRS1", "IRS2"],
        "Pancreatic Cancer": ["KRAS", "TP53", "CDKN2A", "SMAD4"],
        "Colorectal Cancer": ["APC", "KRAS", "TP53", "MLH1", "MSH2"]
    }
    for condition, genes in gene_associations.items():
        st.markdown(f"**{condition}:** {', '.join(genes)}")

    # ----------------------------
    # 9️⃣ Excel Download
    # ----------------------------
    st.download_button(
        label="Download All Data as Excel",
        data=df_all.to_excel(index=False),
        file_name="digital_twin_lab_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Upload PDF lab reports to start analysis.")
