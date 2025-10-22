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
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="Digital Twin Health Risk Analyzer", 
    layout="wide",
    page_icon="🧬",
    initial_sidebar_state="expanded"
)

st.title("🧬 Digital Twin Health Risk Analyzer")
st.markdown("""
**AI-powered health risk analysis** using your lab reports to create a digital health profile.
""")

# ----------------------------
# IMPROVED PDF EXTRACTION FUNCTIONS
# ----------------------------
def extract_text_from_pdf(file):
    """Extract text from PDF file - SIMPLIFIED VERSION"""
    try:
        # Reset file pointer
        file.seek(0)
        # Read file as bytes
        pdf_bytes = file.read()
        # Open PDF from bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        st.error(f"❌ Error reading PDF: {str(e)}")
        return ""

def debug_pdf_content(text, filename):
    """Show what's actually in the PDF for debugging"""
    with st.expander(f"🔍 DEBUG: Raw text from {filename}", expanded=False):
        st.text_area("Extracted Text", text[:5000] + "..." if len(text) > 5000 else text, height=300)

def extract_lab_values_robust(text, filename):
    """Robust lab value extraction that works with various PDF formats"""
    lab_data = {}
    
    # First, let's see what patterns we can find
    st.write(f"**Analyzing {filename}...**")
    
    # Common test patterns with flexible matching
    test_patterns = [
        # HbA1c patterns
        (r'HbA1c[\s:]*([\d.]+)', 'HbA1c'),
        (r'HBA1C[\s:]*([\d.]+)', 'HbA1c'),
        (r'HbA1c.*?([\d.]+)\s*%', 'HbA1c'),
        
        # Glucose patterns
        (r'Glucose[\s:]*([\d.]+)', 'Glucose'),
        (r'Glucose.*?Random[\s:]*([\d.]+)', 'Glucose'),
        (r'Random Glucose[\s:]*([\d.]+)', 'Glucose'),
        
        # Hemoglobin patterns
        (r'Hemoglobin[\s:]*([\d.]+)', 'Hb'),
        (r'Hb[\s:]*([\d.]+)', 'Hb'),
        (r'Hemoglobin.*?([\d.]+)\s*gm/dl', 'Hb'),
        
        # WBC patterns
        (r'WBC/TLC[\s:]*([\d.]+)', 'WBC'),
        (r'WBC[\s:]*([\d.]+)', 'WBC'),
        (r'White Blood Cell[\s:]*([\d.]+)', 'WBC'),
        
        # Platelet patterns
        (r'Platelet Count[\s:]*([\d.]+)', 'Platelet'),
        (r'Platelet[\s:]*([\d.]+)', 'Platelet'),
        (r'PLT[\s:]*([\d.]+)', 'Platelet'),
        
        # Liver function tests
        (r'SGPT - ALT[\s:]*([\d.]+)', 'ALT'),
        (r'ALT[\s:]*([\d.]+)', 'ALT'),
        (r'SGPT[\s:]*([\d.]+)', 'ALT'),
        (r'SGOT - AST[\s:]*([\d.]+)', 'AST'),
        (r'AST[\s:]*([\d.]+)', 'AST'),
        (r'SGOT[\s:]*([\d.]+)', 'AST'),
        
        # Other common tests
        (r'Creatinine[\s:]*([\d.]+)', 'Creatinine'),
        (r'Urea[\s:]*([\d.]+)', 'Urea'),
        (r'Bilirubin[\s:]*([\d.]+)', 'Bilirubin'),
        (r'Albumin[\s:]*([\d.]+)', 'Albumin'),
        (r'Calcium[\s:]*([\d.]+)', 'Calcium'),
        (r'ESR[\s:]*([\d.]+)', 'ESR'),
        (r'E\.S\.R\.[\s:]*([\d.]+)', 'ESR'),
    ]
    
    extracted_tests = []
    
    for pattern, test_name in test_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Take the first match
            value = matches[0]
            try:
                lab_data[test_name] = float(value)
                extracted_tests.append(test_name)
                st.success(f"✅ {test_name}: {value}")
            except ValueError:
                st.warning(f"⚠️ Could not convert {test_name} value: {value}")
    
    # Try to extract date
    date_patterns = [
        r'Received On\s*:\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'Reported On\s*:\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'Date\s*:\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                date_str = match.group(1)
                lab_data['Date'] = pd.to_datetime(date_str, format='%d/%m/%Y')
                st.success(f"✅ Date extracted: {date_str}")
                break
            except:
                continue
    
    # Extract patient info
    name_match = re.search(r'Name\s*:\s*([A-Z\s]+)', text)
    if name_match:
        lab_data['Patient_Name'] = name_match.group(1).strip()
    
    age_match = re.search(r'Age\s*:\s*(\d+)', text)
    if age_match:
        lab_data['Patient_Age'] = age_match.group(1)
    
    st.info(f"📊 Extracted {len(extracted_tests)} tests: {', '.join(extracted_tests)}")
    
    return lab_data

# ----------------------------
# SIMPLE RISK ASSESSMENT
# ----------------------------
def calculate_simple_risks(df):
    """Calculate basic health risks from lab data"""
    risks = {}
    
    if not df.empty:
        latest_data = df.iloc[-1]
        
        # Diabetes Risk
        if 'HbA1c' in latest_data and pd.notna(latest_data['HbA1c']):
            hba1c = latest_data['HbA1c']
            if hba1c > 6.5:
                risks['Diabetes'] = '🔴 High'
            elif hba1c > 5.7:
                risks['Diabetes'] = '🟠 Moderate'
            else:
                risks['Diabetes'] = '🟢 Low'
        
        # Liver Risk
        if 'ALT' in latest_data and pd.notna(latest_data['ALT']):
            alt = latest_data['ALT']
            if alt > 100:
                risks['Liver'] = '🔴 High'
            elif alt > 50:
                risks['Liver'] = '🟠 Moderate'
            else:
                risks['Liver'] = '🟢 Low'
        
        # Anemia Risk
        if 'Hb' in latest_data and pd.notna(latest_data['Hb']):
            hb = latest_data['Hb']
            if hb < 11:
                risks['Anemia'] = '🔴 High'
            elif hb < 13:
                risks['Anemia'] = '🟠 Moderate'
            else:
                risks['Anemia'] = '🟢 Low'
    
    return risks

# ----------------------------
# STREAMLIT APP
# ----------------------------
st.header("👤 Patient Information")

col1, col2, col3 = st.columns(3)
with col1:
    age = st.number_input("Age", 0, 120, 34)
    weight = st.number_input("Weight (kg)", 10, 200, 70)
with col2:
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    height = st.number_input("Height (cm)", 50, 250, 170)
with col3:
    if height > 0:
        bmi = round(weight / ((height/100) ** 2), 2)
        bmi_category = "Obese" if bmi >= 30 else "Overweight" if bmi >= 25 else "Normal" if bmi >= 18.5 else "Underweight"
        st.metric("BMI", f"{bmi} ({bmi_category})")
    else:
        bmi = 0
        st.metric("BMI", "Invalid height")

# Family History
st.subheader("🏥 Family History")
fam_col1, fam_col2 = st.columns(2)
with fam_col1:
    family_diabetes = st.checkbox("Diabetes in family")
    family_heart = st.checkbox("Heart disease in family")
with fam_col2:
    family_cancer = st.checkbox("Cancer in family")
    smoking = st.checkbox("Smoking history")

# ----------------------------
# PDF UPLOAD AND PROCESSING
# ----------------------------
st.header("📁 Upload Lab Reports")

uploaded_files = st.file_uploader(
    "Choose PDF lab reports", 
    type="pdf", 
    accept_multiple_files=True,
    help="Upload your lab reports in PDF format"
)

# Initialize session state
if 'df_all' not in st.session_state:
    st.session_state.df_all = pd.DataFrame()

# Debug option
debug_mode = st.checkbox("Enable debug mode (show raw PDF text)")

if uploaded_files:
    st.success(f"📄 {len(uploaded_files)} file(s) uploaded successfully!")
    
    if st.button("🚀 Extract Data from PDFs", type="primary"):
        all_extracted_data = []
        
        for file in uploaded_files:
            st.markdown(f"---")
            st.subheader(f"Processing: {file.name}")
            
            # Extract text from PDF
            with st.spinner("Reading PDF..."):
                text = extract_text_from_pdf(file)
            
            if text:
                if debug_mode:
                    debug_pdf_content(text, file.name)
                
                # Extract lab values
                with st.spinner("Extracting lab values..."):
                    lab_data = extract_lab_values_robust(text, file.name)
                
                if lab_data:
                    lab_data['Filename'] = file.name
                    all_extracted_data.append(lab_data)
                    st.success(f"✅ Successfully extracted data from {file.name}")
                else:
                    st.error(f"❌ No lab data could be extracted from {file.name}")
            else:
                st.error(f"❌ Could not read PDF: {file.name}")
        
        # Create DataFrame
        if all_extracted_data:
            st.session_state.df_all = pd.DataFrame(all_extracted_data)
            
            # Process dates
            if 'Date' in st.session_state.df_all.columns:
                st.session_state.df_all['Date'] = pd.to_datetime(
                    st.session_state.df_all['Date'], errors='coerce'
                )
                # Remove invalid dates
                st.session_state.df_all = st.session_state.df_all[st.session_state.df_all['Date'].notna()]
                if not st.session_state.df_all.empty:
                    st.session_state.df_all = st.session_state.df_all.sort_values('Date').reset_index(drop=True)

# ----------------------------
# DISPLAY RESULTS
# ----------------------------
if not st.session_state.df_all.empty:
    df = st.session_state.df_all
    
    st.header("📊 Extracted Lab Data")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    
    test_columns = [col for col in df.columns if col not in ['Date', 'Filename', 'Patient_Name', 'Patient_Age']]
    col2.metric("Tests Extracted", len(test_columns))
    
    if 'Date' in df.columns:
        date_range = f"{df['Date'].min().strftime('%d/%m/%Y')} to {df['Date'].max().strftime('%d/%m/%Y')}"
    else:
        date_range = "N/A"
    col3.metric("Date Range", date_range)
    
    # Display the data
    st.dataframe(df, use_container_width=True)
    
    # Show which tests were successfully extracted
    st.subheader("🎯 Successfully Extracted Tests")
    extracted_tests = [col for col in test_columns if not df[col].isna().all()]
    st.write(f"Found data for: {', '.join(extracted_tests)}")
    
    # Basic Risk Assessment
    st.header("🩺 Health Risk Assessment")
    
    risks = calculate_simple_risks(df)
    
    if risks:
        risk_col1, risk_col2, risk_col3 = st.columns(3)
        
        risk_columns = [risk_col1, risk_col2, risk_col3]
        for i, (condition, risk_level) in enumerate(risks.items()):
            with risk_columns[i % 3]:
                st.metric(f"{condition} Risk", risk_level)
    else:
        st.info("No risk assessment available - insufficient lab data")
    
    # Trend Analysis (if multiple reports)
    if len(df) > 1 and 'Date' in df.columns:
        st.header("📈 Trend Analysis")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in numeric_cols[:6]:  # Show first 6 numeric columns
            if col != 'Patient_Age' and df[col].notna().sum() > 1:
                fig = px.line(df, x='Date', y=col, title=f'{col} Trend', markers=True)
                st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations
    st.header("💡 Recommendations")
    
    recommendations = []
    
    if 'Diabetes' in risks and risks['Diabetes'] in ['🔴 High', '🟠 Moderate']:
        recommendations.extend([
            "🩺 **Monitor HbA1c every 3-6 months**",
            "🥗 **Consult nutritionist for diabetic diet**",
            "🏃 **Regular exercise (30 mins, 5 days/week)**"
        ])
    
    if 'Liver' in risks and risks['Liver'] in ['🔴 High', '🟠 Moderate']:
        recommendations.extend([
            "🔍 **Consider liver function tests**",
            "🚫 **Reduce alcohol consumption**",
            "💊 **Avoid hepatotoxic medications**"
        ])
    
    if not recommendations:
        recommendations.append("🎉 **Continue routine health monitoring**")
    
    for rec in recommendations:
        st.write(rec)
    
    # Export Data
    st.header("📤 Export Data")
    
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
    st.info("👆 Upload PDF lab reports and click 'Extract Data from PDFs' to begin analysis")

# ----------------------------
# TROUBLESHOOTING SECTION
# ----------------------------
with st.expander("🔧 Troubleshooting Guide"):
    st.markdown("""
    **If data extraction isn't working:**
    
    1. **Enable Debug Mode**: Check the box above to see raw PDF text
    2. **PDF Format**: Ensure PDF is text-based (not scanned images)
    3. **Common Tests**: The system looks for:
       - HbA1c, Glucose, Hb, WBC, Platelet, ALT, AST, Creatinine, etc.
    4. **Date Format**: Looks for dates like "11/08/2025"
    
    **Supported Lab Tests:**
    - Diabetes: HbA1c, Glucose
    - Blood Count: Hb, WBC, Platelet, ESR
    - Liver: ALT, AST, Bilirubin, Albumin
    - Kidney: Creatinine, Urea
    - Other: Calcium, Cholesterol
    
    **If still not working**, the PDF might be image-based. Consider OCR tools.
    """)

# ----------------------------
# FOOTER
# ----------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center'><em>Digital Twin Health Analyzer • For educational purposes • Consult doctors for medical decisions</em></div>",
    unsafe_allow_html=True
)
