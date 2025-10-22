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
    page_icon="🧬"
)

st.title("🧬 Digital Twin Health Risk Analyzer")
st.markdown("""
Create your **Digital Twin**, upload lab reports, analyze trends, and get **comprehensive health risk assessment**.
""")

# ----------------------------
# FIXED PDF TEXT EXTRACTION FUNCTION
# ----------------------------
def extract_text_from_pdf(file):
    """Extract text from PDF file with proper file handling"""
    try:
        # Save the file to a temporary bytes object
        file_bytes = file.getvalue()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        st.error(f"Error reading PDF {file.name}: {str(e)}")
        return ""

# Alternative PDF extraction function (if PyMuPDF continues to have issues)
def extract_text_from_pdf_alternative(file):
    """Alternative PDF extraction using different approach"""
    try:
        # Reset file pointer
        file.seek(0)
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        st.error(f"Alternative method also failed for {file.name}: {str(e)}")
        return ""

# ----------------------------
# ENHANCED LAB VALUE EXTRACTION
# ----------------------------
def extract_lab_values_advanced(text, tests):
    """Extract lab values using multiple pattern matching"""
    lab_data = {}
    
    # Enhanced patterns for common tests
    patterns = {
        'HbA1c': [r'HbA1c[:\s]*([\d.,]+)\s*%', r'A1c[:\s]*([\d.,]+)', r'Glycated[:\s]*([\d.,]+)'],
        'Glucose': [r'Glucose[:\s]*([\d.,]+)', r'Blood.Sugar[:\s]*([\d.,]+)', r'FBS[:\s]*([\d.,]+)'],
        'Hb': [r'Hemoglobin[:\s]*([\d.,]+)', r'Hb[:\s]*([\d.,]+)', r'HGB[:\s]*([\d.,]+)'],
        'WBC': [r'WBC[:\s]*([\d.,]+)', r'White.Blood[:\s]*([\d.,]+)', r'Leukocyte[:\s]*([\d.,]+)'],
        'Platelet': [r'Platelet[:\s]*([\d.,]+)', r'PLT[:\s]*([\d.,]+)'],
        'ALT': [r'ALT[:\s]*([\d.,]+)', r'SGPT[:\s]*([\d.,]+)'],
        'AST': [r'AST[:\s]*([\d.,]+)', r'SGOT[:\s]*([\d.,]+)'],
        'PSA': [r'PSA[:\s]*([\d.,]+)', r'Prostate.Specific[:\s]*([\d.,]+)'],
        'Creatinine': [r'Creatinine[:\s]*([\d.,]+)', r'CREAT[:\s]*([\d.,]+)'],
        'Cholesterol': [r'Cholesterol[:\s]*([\d.,]+)', r'CHOL[:\s]*([\d.,]+)'],
    }
    
    for test in tests:
        value_found = None
        
        # Try multiple patterns for known tests
        if test in patterns:
            for pattern in patterns[test]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value_found = match.group(1).replace(",", "").strip()
                    break
        else:
            # Default pattern for other tests
            pattern = rf"{test}[:\s]*([\d.,]+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_found = match.group(1).replace(",", "").strip()
        
        # Convert to float if possible
        if value_found:
            try:
                lab_data[test] = float(value_found)
            except ValueError:
                lab_data[test] = value_found
    
    # Extract date from text
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        r'Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Report.Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                date_str = match.group(1)
                lab_data['Date'] = pd.to_datetime(date_str, errors='coerce')
                if pd.notna(lab_data['Date']):
                    break
            except:
                continue
    
    return lab_data

# ----------------------------
# SIDEBAR FOR SETTINGS
# ----------------------------
with st.sidebar:
    st.header("⚙️ Analysis Settings")
    risk_sensitivity = st.slider("Risk Sensitivity", 1, 10, 7)
    show_genetic_insights = st.checkbox("Show Genetic Insights", True)
    
    st.header("🎯 Target Conditions")
    diabetes_analysis = st.checkbox("Diabetes Analysis", True)
    cancer_analysis = st.checkbox("Cancer Risk Analysis", True)
    cardiovascular_analysis = st.checkbox("Cardiovascular Analysis", False)
    
    st.markdown("---")
    st.info("""
    **Instructions:**
    1. Create digital twin profile
    2. Select lab tests to extract
    3. Upload PDF lab reports
    4. View analysis and risks
    """)

# ----------------------------
# 1️⃣ DIGITAL TWIN PROFILE
# ----------------------------
st.header("👤 Create Your Digital Twin")

col1, col2, col3 = st.columns(3)
with col1:
    age = st.number_input("Age", 0, 120, 45, help="Enter your current age")
    weight = st.number_input("Weight (kg)", 10, 200, 70, help="Enter your weight in kilograms")
with col2:
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    height = st.number_input("Height (cm)", 50, 250, 170, help="Enter your height in centimeters")
with col3:
    location = st.text_input("Location", "Mumbai", help="Your city/location")
    activity = st.selectbox("Activity Level", ["Sedentary", "Light", "Moderate", "Active", "Very Active"])

# Family History
st.subheader("🏥 Family Medical History")
fam_col1, fam_col2, fam_col3 = st.columns(3)
with fam_col1:
    family_diabetes = st.checkbox("Diabetes")
    family_heart_disease = st.checkbox("Heart Disease")
with fam_col2:
    family_cancer = st.checkbox("Cancer")
    family_hypertension = st.checkbox("Hypertension")
with fam_col3:
    smoking = st.checkbox("Smoking History")
    alcohol = st.selectbox("Alcohol Consumption", ["Never", "Occasional", "Regular"])

# Calculate BMI
if height > 0:
    bmi = round(weight / ((height / 100) ** 2), 2)
    if bmi < 18.5:
        bmi_category = "Underweight"
    elif bmi < 25:
        bmi_category = "Normal"
    elif bmi < 30:
        bmi_category = "Overweight"
    else:
        bmi_category = "Obese"
else:
    bmi = 0
    bmi_category = "Invalid height"

# Display BMI
col1, col2, col3 = st.columns(3)
col1.metric("Your BMI", f"{bmi}")
col2.metric("BMI Category", bmi_category)
col3.metric("Status", "⚠️ Needs Attention" if bmi_category in ["Underweight", "Overweight", "Obese"] else "✅ Healthy")

# ----------------------------
# 2️⃣ LAB TEST SELECTION
# ----------------------------
st.header("🔬 Lab Test Configuration")

# Lab test categories
lab_categories = {
    "Diabetes Monitoring": ["HbA1c", "Glucose", "Insulin", "C-Peptide"],
    "Complete Blood Count": ["Hb", "WBC", "RBC", "Platelet", "Neutrophils", "Lymphocytes", "Monocytes"],
    "Liver Function": ["ALT", "AST", "ALP", "Bilirubin", "Albumin"],
    "Kidney Function": ["Creatinine", "BUN", "eGFR"],
    "Cancer Markers": ["PSA", "CA19-9", "CEA", "AFP"],
    "Thyroid Function": ["TSH", "T3", "T4"],
    "Lipid Profile": ["Cholesterol", "HDL", "LDL", "Triglycerides"],
    "Inflammation": ["ESR", "CRP"]
}

# Test selection interface
selected_tests = []
expander = st.expander("📋 Select Lab Tests by Category", expanded=True)

with expander:
    for category, tests in lab_categories.items():
        col1, col2 = st.columns([1, 3])
        with col1:
            category_selected = st.checkbox(f"{category}", value=True, key=f"cat_{category}")
        with col2:
            if category_selected:
                selected_tests.extend(tests)
                st.caption(f"Includes: {', '.join(tests)}")

# Custom tests
custom_tests = st.text_input("Add custom tests (comma-separated):", 
                           help="Add tests not in the list above")
if custom_tests:
    custom_list = [test.strip() for test in custom_tests.split(",") if test.strip()]
    selected_tests.extend(custom_list)

selected_tests = list(set(selected_tests))  # Remove duplicates

if selected_tests:
    st.success(f"✅ {len(selected_tests)} tests selected for extraction")

# ----------------------------
# 3️⃣ PDF UPLOAD AND PROCESSING
# ----------------------------
st.header("📁 Upload Lab Reports")

uploaded_files = st.file_uploader(
    "Choose PDF lab reports", 
    type="pdf", 
    accept_multiple_files=True,
    help="Upload multiple PDF lab reports for trend analysis"
)

df_all = pd.DataFrame()

if uploaded_files:
    st.success(f"📄 {len(uploaded_files)} file(s) uploaded successfully!")
    
    # Process files with progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_extracted_data = []
    successful_files = 0
    
    for i, file in enumerate(uploaded_files):
        status_text.text(f"Processing {file.name}... ({i+1}/{len(uploaded_files)})")
        
        try:
            # Extract text from PDF using the fixed function
            text = extract_text_from_pdf(file)
            
            if text and len(text.strip()) > 0:
                # Extract lab values
                data = extract_lab_values_advanced(text, selected_tests)
                if data:  # Only add if we extracted something
                    data['Filename'] = file.name
                    all_extracted_data.append(data)
                    successful_files += 1
                else:
                    st.warning(f"⚠️ No lab data found in {file.name}")
            else:
                st.warning(f"⚠️ No text extracted from {file.name} - may be scanned/image PDF")
                
        except Exception as e:
            st.error(f"❌ Error processing {file.name}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    status_text.text(f"✅ Processing complete! {successful_files}/{len(uploaded_files)} files successfully processed")
    
    # Create DataFrame if we have data
    if all_extracted_data:
        df_all = pd.DataFrame(all_extracted_data)
        
        # Process dates
        if 'Date' in df_all.columns:
            df_all['Date'] = pd.to_datetime(df_all['Date'], errors='coerce')
            # Remove rows with invalid dates
            df_all = df_all[df_all['Date'].notna()]
            if not df_all.empty:
                df_all = df_all.sort_values('Date').reset_index(drop=True)
                df_all['Days_Since_First'] = (df_all['Date'] - df_all['Date'].min()).dt.days
        
        # Display extracted data
        st.subheader("📊 Extracted Lab Data")
        
        if not df_all.empty:
            # Show summary
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Reports", len(df_all))
            extracted_tests = len([col for col in df_all.columns if col not in ['Date', 'Filename', 'Days_Since_First']])
            col2.metric("Tests Extracted", extracted_tests)
            
            if 'Date' in df_all.columns and not df_all['Date'].isna().all():
                date_range = f"{df_all['Date'].min().strftime('%Y-%m-%d')} to {df_all['Date'].max().strftime('%Y-%m-%d')}"
            else:
                date_range = "N/A"
            col3.metric("Date Range", date_range)
            
            # Display data table
            st.dataframe(df_all, use_container_width=True)
            
            # ----------------------------
            # 4️⃣ TREND ANALYSIS
            # ----------------------------
            if len(df_all) > 1:
                st.header("📈 Trend Analysis")
                
                # Get numeric columns for analysis
                numeric_cols = df_all.select_dtypes(include=[np.number]).columns.tolist()
                if 'Days_Since_First' in numeric_cols:
                    numeric_cols.remove('Days_Since_First')
                
                if numeric_cols:
                    # Statistical Summary
                    st.subheader("Statistical Summary")
                    summary_df = df_all[numeric_cols].describe()
                    st.dataframe(summary_df)
                    
                    # Individual Trends
                    for col in numeric_cols:
                        if df_all[col].notna().sum() > 1:  # Only plot if we have data
                            fig = go.Figure()
                            
                            # Main trend line
                            valid_data = df_all[df_all[col].notna()]
                            x_data = valid_data['Date'] if 'Date' in valid_data.columns else valid_data.index
                            
                            fig.add_trace(go.Scatter(
                                x=x_data,
                                y=valid_data[col],
                                mode='lines+markers',
                                name=col,
                                line=dict(width=3),
                                marker=dict(size=8)
                            ))
                            
                            fig.update_layout(
                                title=f"{col} Trend Over Time",
                                xaxis_title="Date" if 'Date' in df_all.columns else "Report Sequence",
                                yaxis_title=col,
                                hovermode='x unified',
                                height=400
                            )
                            st.plotly_chart(fig, use_container_width=True)
                
                # ----------------------------
                # 5️⃣ RISK ASSESSMENT
                # ----------------------------
                st.header("🩺 Health Risk Assessment")
                
                # Diabetes Risk Calculation
                def calculate_diabetes_risk(df, age, bmi, family_history):
                    risk_score = 0
                    
                    # Lab values
                    if "HbA1c" in df.columns:
                        last_valid = df["HbA1c"].dropna()
                        if len(last_valid) > 0:
                            last_hba1c = last_valid.iloc[-1]
                            if last_hba1c > 6.5: risk_score += 3
                            elif last_hba1c > 5.7: risk_score += 2
                            elif last_hba1c > 5.5: risk_score += 1
                    
                    if "Glucose" in df.columns:
                        last_valid = df["Glucose"].dropna()
                        if len(last_valid) > 0:
                            last_glucose = last_valid.iloc[-1]
                            if last_glucose > 126: risk_score += 2
                            elif last_glucose > 100: risk_score += 1
                    
                    # Demographic factors
                    if age > 45: risk_score += 1
                    if bmi >= 25: risk_score += 1
                    if family_history: risk_score += 2
                    if activity in ["Sedentary", "Light"]: risk_score += 1
                    
                    return min(risk_score, 10)
                
                # Display Risk Scores
                risk_col1, risk_col2, risk_col3 = st.columns(3)
                
                with risk_col1:
                    if diabetes_analysis:
                        diabetes_risk_score = calculate_diabetes_risk(df_all, age, bmi, family_diabetes)
                        if diabetes_risk_score >= 6:
                            diabetes_risk = "🔴 High"
                        elif diabetes_risk_score >= 3:
                            diabetes_risk = "🟠 Moderate"
                        else:
                            diabetes_risk = "🟢 Low"
                        
                        st.metric(
                            "Diabetes Risk", 
                            diabetes_risk,
                            f"Score: {diabetes_risk_score}/10"
                        )
                
                with risk_col2:
                    if cancer_analysis:
                        # Simplified cancer risk for demo
                        cancer_risk_score = 2 if family_cancer else 1
                        risk_level = "🟠 Moderate" if cancer_risk_score >= 2 else "🟢 Low"
                        st.metric("Cancer Risk", risk_level, "Family history based")
                
                with risk_col3:
                    cardiovascular_risk = "🟢 Low" if age < 50 and not family_heart_disease else "🟠 Moderate"
                    st.metric("Cardiovascular Risk", cardiovascular_risk)
                
                # ----------------------------
                # 6️⃣ RECOMMENDATIONS
                # ----------------------------
                st.header("💡 Clinical Recommendations")
                
                recommendations = []
                
                # Diabetes recommendations
                if diabetes_risk_score >= 3:
                    recommendations.extend([
                        "🩺 Consider oral glucose tolerance test",
                        "🥗 Focus on diet and exercise modifications",
                        "📊 Monitor blood glucose levels regularly"
                    ])
                
                # General health recommendations
                if bmi >= 25:
                    recommendations.append("⚖️ Weight management recommended")
                
                if activity in ["Sedentary", "Light"]:
                    recommendations.append("🏃 Increase physical activity to 150 mins/week")
                
                if smoking:
                    recommendations.append("🚭 Smoking cessation strongly recommended")
                
                # Display recommendations
                if recommendations:
                    for rec in recommendations:
                        st.write(f"• {rec}")
                else:
                    st.success("🎉 No immediate concerning trends detected. Continue with routine health monitoring!")
                
                # ----------------------------
                # 7️⃣ EXPORT FUNCTIONALITY
                # ----------------------------
                st.header("📤 Export Results")
                
                # Excel Export
                def convert_df_to_excel(df):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Lab_Data', index=False)
                    return output.getvalue()
                
                excel_data = convert_df_to_excel(df_all)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        label="📊 Download Excel Report",
                        data=excel_data,
                        file_name=f"digital_twin_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.warning("No valid data extracted from the uploaded files.")
    else:
        st.error("❌ No data could be extracted from any of the uploaded files.")

else:
    st.info("📁 Please upload PDF lab reports to begin analysis. You can upload multiple files for trend analysis.")

# ----------------------------
# FOOTER
# ----------------------------
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p><em>Disclaimer: This tool is for educational and research purposes only. Always consult healthcare professionals for medical decisions.</em></p>
    <p>Digital Twin Health Risk Analyzer • Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
