import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import fitz  # PyMuPDF
import re
from datetime import datetime
import numpy as np
from io import BytesIO

# ----------------------------
# PAGE CONFIG - FIXED FOR FULL VISIBILITY
# ----------------------------
st.set_page_config(
    page_title="Digital Twin Health Risk Analyzer", 
    layout="wide",
    page_icon="🧬",
    initial_sidebar_state="expanded"
)

# Custom CSS to ensure full page visibility
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stApp {
        max-width: 100%;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧬 Digital Twin Health Risk Analyzer")
st.markdown("""
Create your **Digital Twin**, upload lab reports, analyze trends, and get **comprehensive health risk assessment**.
""")

# ----------------------------
# FIXED PDF TEXT EXTRACTION
# ----------------------------
def extract_text_from_pdf(file):
    """Extract text from PDF file with proper file handling"""
    try:
        # Reset file pointer and read as bytes
        file.seek(0)
        file_bytes = file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        st.error(f"Error reading PDF {file.name}: {str(e)}")
        return ""

# ----------------------------
# SIMPLIFIED LAB VALUE EXTRACTION
# ----------------------------
def extract_lab_values_simple(text, tests):
    """Simple and robust lab value extraction"""
    lab_data = {}
    
    # Clean the text
    text = re.sub(r'\s+', ' ', text)
    
    # Test patterns - simple and direct
    test_patterns = {
        'HbA1c': r'HbA1c\s+([\d.]+)',
        'Glucose': r'Glucose.*?([\d.]+)\s*mg/dL',
        'Hb': r'Hemoglobin\s+([\d.]+)',
        'WBC': r'WBC/TLC\s+([\d.]+)',
        'Platelet': r'Platelet Count\s+([\d.]+)',
        'ALT': r'SGPT - ALT\s+([\d.]+)',
        'AST': r'SGOT - AST\s+([\d.]+)',
        'ESR': r'E\.S\.R\.\s+([\d.]+)',
        'Calcium': r'Serum Calcium\s+([\d.]+)',
        'Creatinine': r'Creatinine\s+([\d.]+)',
        'Urea': r'Urea\s+([\d.]+)',
        'Albumin': r'Albumin\s+([\d.]+)',
        'Bilirubin': r'Total Bilirubin\s+([\d.]+)',
        'ALP': r'Serum alkaline phosphatase - ALP\s+([\d.]+)',
    }
    
    for test in tests:
        if test in test_patterns:
            pattern = test_patterns[test]
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    lab_data[test] = value
                    st.success(f"✅ Extracted {test}: {value}")
                except ValueError:
                    st.warning(f"⚠️ Could not convert {test} value")
    
    # Extract date
    date_match = re.search(r'Received On\s*:\s*(\d{2}/\d{2}/\d{4})', text)
    if date_match:
        try:
            lab_data['Date'] = pd.to_datetime(date_match.group(1), format='%d/%m/%Y')
        except:
            pass
    
    return lab_data

# ----------------------------
# SIDEBAR
# ----------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    st.info("Upload PDF lab reports to get started!")
    
    st.markdown("---")
    st.header("📊 Test Selection")
    
    # Simple test selection
    common_tests = st.multiselect(
        "Select tests to extract:",
        ["HbA1c", "Glucose", "Hb", "WBC", "Platelet", "ALT", "AST", "ESR", "Calcium", "Creatinine"],
        default=["HbA1c", "Glucose", "Hb", "WBC", "Platelet", "ALT", "AST"]
    )

# ----------------------------
# MAIN CONTENT - SIMPLIFIED
# ----------------------------
st.header("👤 Patient Profile")

col1, col2, col3 = st.columns(3)
with col1:
    age = st.number_input("Age", 0, 120, 34)
    weight = st.number_input("Weight (kg)", 10, 200, 70)
with col2:
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    height = st.number_input("Height (cm)", 50, 250, 170)
with col3:
    bmi = round(weight / ((height/100) ** 2), 2) if height > 0 else 0
    st.metric("BMI", bmi)

st.header("📁 Upload Lab Reports")

uploaded_files = st.file_uploader(
    "Choose PDF lab reports", 
    type="pdf", 
    accept_multiple_files=True,
    help="Upload your lab reports in PDF format"
)

# Initialize session state for data persistence
if 'df_all' not in st.session_state:
    st.session_state.df_all = pd.DataFrame()

if uploaded_files:
    st.success(f"📄 {len(uploaded_files)} file(s) uploaded!")
    
    if st.button("🚀 Process PDF Files", type="primary"):
        progress_bar = st.progress(0)
        all_extracted_data = []
        
        for i, file in enumerate(uploaded_files):
            st.write(f"**Processing:** {file.name}")
            
            # Extract text
            text = extract_text_from_pdf(file)
            
            if text:
                # Show raw text in expander for debugging
                with st.expander(f"View extracted text from {file.name}"):
                    st.text(text[:2000] + "..." if len(text) > 2000 else text)
                
                # Extract lab values
                data = extract_lab_values_simple(text, common_tests)
                
                if data:
                    data['Filename'] = file.name
                    all_extracted_data.append(data)
                    st.success(f"✅ Successfully processed {file.name}")
                else:
                    st.error(f"❌ No data extracted from {file.name}")
            else:
                st.error(f"❌ Could not read {file.name}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        # Create DataFrame
        if all_extracted_data:
            st.session_state.df_all = pd.DataFrame(all_extracted_data)
            
            # Process dates
            if 'Date' in st.session_state.df_all.columns:
                st.session_state.df_all['Date'] = pd.to_datetime(
                    st.session_state.df_all['Date'], errors='coerce'
                )
                st.session_state.df_all = st.session_state.df_all.sort_values('Date').reset_index(drop=True)

# Display results if we have data
if not st.session_state.df_all.empty:
    st.header("📊 Extracted Lab Data")
    
    df = st.session_state.df_all
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Tests Extracted", len(df.columns) - 2)  # Exclude Filename and Date
    if 'Date' in df.columns:
        col3.metric("Date Range", f"{df['Date'].min().strftime('%d/%m/%Y')} to {df['Date'].max().strftime('%d/%m/%Y')}")
    
    # Display data
    st.dataframe(df, use_container_width=True)
    
    # Basic Analysis
    st.header("📈 Basic Analysis")
    
    # Get numeric columns (excluding Filename and Date)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if numeric_cols:
        # Show values for each test
        for test in numeric_cols:
            if test in df.columns and df[test].notna().any():
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    latest_value = df[test].dropna().iloc[-1] if not df[test].dropna().empty else None
                    if latest_value is not None:
                        st.metric(f"Latest {test}", f"{latest_value}")
                
                with col2:
                    # Simple trend indicator
                    if len(df[test].dropna()) > 1:
                        values = df[test].dropna()
                        if values.iloc[-1] > values.iloc[-2]:
                            st.info("📈 Increasing trend")
                        elif values.iloc[-1] < values.iloc[-2]:
                            st.info("📉 Decreasing trend")
                        else:
                            st.info("➡️ Stable")
        
        # Risk Assessment
        st.header("🩺 Health Risk Assessment")
        
        risk_col1, risk_col2, risk_col3 = st.columns(3)
        
        with risk_col1:
            # Diabetes Risk
            diabetes_risk = "Unknown"
            if 'HbA1c' in df.columns and not df['HbA1c'].isna().all():
                hba1c = df['HbA1c'].dropna().iloc[-1]
                if hba1c > 6.5:
                    diabetes_risk = "🔴 High"
                elif hba1c > 5.7:
                    diabetes_risk = "🟠 Moderate"
                else:
                    diabetes_risk = "🟢 Low"
                st.metric("Diabetes Risk", diabetes_risk)
        
        with risk_col2:
            # Liver Risk
            liver_risk = "🟢 Low"
            if 'ALT' in df.columns and not df['ALT'].isna().all():
                alt = df['ALT'].dropna().iloc[-1]
                if alt > 50:
                    liver_risk = "🔴 High" if alt > 100 else "🟠 Moderate"
                st.metric("Liver Health Risk", liver_risk)
        
        with risk_col3:
            # Anemia Risk
            anemia_risk = "🟢 Low"
            if 'Hb' in df.columns and not df['Hb'].isna().all():
                hb = df['Hb'].dropna().iloc[-1]
                if gender == "Male" and hb < 13:
                    anemia_risk = "🟠 Moderate"
                elif gender == "Female" and hb < 12:
                    anemia_risk = "🟠 Moderate"
                st.metric("Anemia Risk", anemia_risk)
        
        # Export functionality
        st.header("📤 Export Results")
        
        if st.button("Download Data as Excel"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Lab_Data')
            st.download_button(
                label="⬇️ Click to Download Excel File",
                data=output.getvalue(),
                file_name=f"lab_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.info("👆 Please upload PDF lab reports and click 'Process PDF Files' to get started.")

# ----------------------------
# FOOTER
# ----------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center'><em>Disclaimer: This tool is for educational purposes only. Consult healthcare professionals for medical decisions.</em></div>",
    unsafe_allow_html=True
)
