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
st.set_page_config(page_title="Digital Twin Health Risk Analyzer", layout="wide")
st.title("🧬 Digital Twin Health Risk Analyzer (SAMD Prototype)")
st.markdown("""
Create your **Digital Twin**, upload lab reports, analyze trends, and get **comprehensive health risk assessment**.
""")

# ----------------------------
# SIDEBAR FOR SETTINGS
# ----------------------------
with st.sidebar:
    st.header("⚙️ Analysis Settings")
    risk_sensitivity = st.slider("Risk Sensitivity", 1, 10, 7)
    show_genetic_insights = st.checkbox("Show Genetic Insights", True)
    enable_ai_predictions = st.checkbox("Enable AI Predictions", True)
    
    st.header("🎯 Target Conditions")
    diabetes_analysis = st.checkbox("Diabetes Analysis", True)
    cancer_analysis = st.checkbox("Cancer Risk Analysis", True)
    cardiovascular_analysis = st.checkbox("Cardiovascular Analysis", True)

# ----------------------------
# 1️⃣ Enhanced Digital Twin Profile
# ----------------------------
st.header("1️⃣ Create Your Digital Twin")

col1, col2, col3 = st.columns(3)
with col1:
    age = st.number_input("Age", 0, 120, 45)
    weight = st.number_input("Weight (kg)", 10, 200, 70)
with col2:
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    height = st.number_input("Height (cm)", 50, 250, 170)
with col3:
    location = st.text_input("Location", "Mumbai")
    activity = st.selectbox("Activity Level", ["Sedentary", "Light", "Moderate", "Active", "Very Active"])

# Family History
st.subheader("Family Medical History")
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

# Calculate BMI with classification
bmi = round(weight / ((height / 100) ** 2), 2)
if bmi < 18.5:
    bmi_category = "Underweight"
elif bmi < 25:
    bmi_category = "Normal"
elif bmi < 30:
    bmi_category = "Overweight"
else:
    bmi_category = "Obese"

col1, col2, col3 = st.columns(3)
col1.metric("Your BMI", f"{bmi} ({bmi_category})")
col2.metric("BMI Status", bmi_category)

# ----------------------------
# Enhanced Lab Test Configuration
# ----------------------------
lab_categories = {
    "Diabetes": ["HbA1c", "Glucose", "Insulin", "C-Peptide"],
    "Complete Blood Count": ["Hb", "WBC", "RBC", "Platelet", "Neutrophils", "Lymphocytes", "Monocytes"],
    "Liver Function": ["ALT", "AST", "ALP", "Bilirubin", "Albumin"],
    "Kidney Function": ["Creatinine", "BUN", "eGFR"],
    "Cancer Markers": ["PSA", "CA19-9", "CEA", "AFP"],
    "Thyroid": ["TSH", "T3", "T4"],
    "Lipids": ["Cholesterol", "HDL", "LDL", "Triglycerides"],
    "Other": ["Calcium", "Vitamin D", "ESR", "CRP"]
}

expander = st.expander("🔬 Select Lab Tests by Category")
selected_tests = []
for category, tests in lab_categories.items():
    with expander:
        category_selected = st.checkbox(f"{category} ({len(tests)} tests)", value=True)
        if category_selected:
            selected_tests.extend(tests)

# Add custom tests
custom_tests = st.text_input("Add custom tests (comma-separated):")
if custom_tests:
    custom_list = [test.strip() for test in custom_tests.split(",")]
    selected_tests.extend(custom_list)

selected_tests = list(set(selected_tests))  # Remove duplicates

# ----------------------------
# Enhanced PDF Processing
# ----------------------------
def extract_lab_values_advanced(text, tests):
    lab_data = {}
    patterns = {
        'HbA1c': [r'HbA1c[:\s]*([\d.,]+)', r'A1c[:\s]*([\d.,]+)', r'Glycated[:\s]*([\d.,]+)'],
        'Glucose': [r'Glucose[:\s]*([\d.,]+)', r'Blood.Sugar[:\s]*([\d.,]+)'],
        'Hb': [r'Hemoglobin[:\s]*([\d.,]+)', r'Hb[:\s]*([\d.,]+)'],
        # Add more pattern variations for each test
    }
    
    for test in tests:
        value_found = None
        # Try multiple patterns
        if test in patterns:
            for pattern in patterns[test]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value_found = match.group(1).replace(",", "")
                    break
        else:
            # Default pattern
            pattern = rf"{test}[:\s]*([\d.,]+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_found = match.group(1).replace(",", "")
        
        if value_found:
            try:
                lab_data[test] = float(value_found)
            except:
                lab_data[test] = value_found
                
    return lab_data

# ----------------------------
# Upload and Process PDFs
# ----------------------------
uploaded_files = st.file_uploader(
    "Upload lab reports (PDF) - multiple allowed", 
    type="pdf", 
    accept_multiple_files=True
)

df_all = pd.DataFrame()
if uploaded_files:
    progress_bar = st.progress(0)
    for i, file in enumerate(uploaded_files):
        text = extract_text_from_pdf(file)
        data = extract_lab_values_advanced(text, selected_tests)
        
        # Extract date from PDF text
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}))'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    data['Date'] = pd.to_datetime(match.group(1), errors='coerce')
                    break
                except:
                    continue
        
        df_all = pd.concat([df_all, pd.DataFrame([data])], ignore_index=True)
        progress_bar.progress((i + 1) / len(uploaded_files))

    # Date processing
    if "Date" in df_all.columns:
        df_all['Date'] = pd.to_datetime(df_all['Date'], errors='coerce')
        df_all = df_all.sort_values('Date').reset_index(drop=True)
        df_all['Days_Since_First'] = (df_all['Date'] - df_all['Date'].min()).dt.days

    st.subheader("📊 Extracted Lab Data")
    st.dataframe(df_all.style.format(precision=2))

    # ----------------------------
    # Enhanced Trend Analysis
    # ----------------------------
    if len(df_all) > 1:
        st.header("📈 Advanced Trend Analysis")
        
        # Statistical Summary
        numeric_cols = df_all.select_dtypes(include='number').columns
        st.subheader("Statistical Summary")
        summary_df = df_all[numeric_cols].describe()
        st.dataframe(summary_df)
        
        # Correlation Analysis
        if len(numeric_cols) > 1:
            st.subheader("Correlation Heatmap")
            corr_matrix = df_all[numeric_cols].corr()
            fig = px.imshow(corr_matrix, aspect="auto", color_continuous_scale="RdBu_r")
            st.plotly_chart(fig, use_container_width=True)

        # Individual Trends with Anomaly Detection
        for col in numeric_cols:
            if col != 'Days_Since_First':
                fig = go.Figure()
                
                # Main trend
                fig.add_trace(go.Scatter(
                    x=df_all['Date'] if 'Date' in df_all.columns else df_all.index,
                    y=df_all[col],
                    mode='lines+markers',
                    name=col,
                    line=dict(width=3)
                ))
                
                # Trend line
                if len(df_all) > 2:
                    z = np.polyfit(range(len(df_all)), df_all[col].fillna(method='ffill'), 1)
                    trend_line = np.poly1d(z)(range(len(df_all)))
                    fig.add_trace(go.Scatter(
                        x=df_all['Date'] if 'Date' in df_all.columns else df_all.index,
                        y=trend_line,
                        mode='lines',
                        name='Trend',
                        line=dict(dash='dash', color='red')
                    ))
                
                fig.update_layout(
                    title=f"{col} Trend Analysis",
                    xaxis_title="Date",
                    yaxis_title=col,
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)

        # ----------------------------
        # Enhanced Risk Assessment Engine
        # ----------------------------
        st.header("🩺 Comprehensive Risk Assessment")
        
        def calculate_diabetes_risk(df, age, bmi, family_history):
            """Enhanced diabetes risk calculation"""
            risk_score = 0
            
            # HbA1c based risk
            if "HbA1c" in df.columns:
                last_hba1c = df["HbA1c"].iloc[-1]
                if last_hba1c > 6.5: risk_score += 3
                elif last_hba1c > 5.7: risk_score += 2
                elif last_hba1c > 5.5: risk_score += 1
            
            # Glucose trends
            if "Glucose" in df.columns:
                last_glucose = df["Glucose"].iloc[-1]
                if last_glucose > 126: risk_score += 2
                elif last_glucose > 100: risk_score += 1
                
                # Check for increasing trend
                if len(df) > 2:
                    glucose_trend = np.polyfit(range(len(df)), df["Glucose"].fillna(0), 1)[0]
                    if glucose_trend > 0: risk_score += 1
            
            # Demographic factors
            if age > 45: risk_score += 1
            if bmi >= 25: risk_score += 1
            if family_diabetes: risk_score += 2
            if activity in ["Sedentary", "Light"]: risk_score += 1
            
            return risk_score

        def calculate_cancer_risk(df, test_type="pancreatic"):
            """Enhanced cancer risk calculation"""
            risk_score = 0
            if len(df) < 2:
                return risk_score
                
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            if test_type == "pancreatic":
                markers = {
                    "HbA1c": (1, 0.5),  # (weight, threshold)
                    "CA19-9": (3, 37),
                    "Bilirubin": (2, 1.2),
                    "ALT": (1, 40),
                    "AST": (1, 40)
                }
            else:  # colorectal
                markers = {
                    "Hb": (2, -1),  # Decreasing trend
                    "CEA": (3, 5),
                    "Calcium": (1, 10.5)
                }
                
            for marker, (weight, threshold) in markers.items():
                if marker in df.columns:
                    current_val = last[marker]
                    if current_val > threshold:
                        risk_score += weight
                    # Check trend
                    if len(df) > 2:
                        trend = np.polyfit(range(len(df)), df[marker].fillna(0), 1)[0]
                        if trend > 0 and marker not in ["Hb"]:
                            risk_score += 1
                        elif trend < 0 and marker in ["Hb"]:
                            risk_score += 1
                            
            return min(risk_score, 10)

        # Display Risk Assessments
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
                st.metric("Diabetes Risk", diabetes_risk, f"Score: {diabetes_risk_score}/8")
        
        with risk_col2:
            if cancer_analysis:
                pancreatic_risk_score = calculate_cancer_risk(df_all, "pancreatic")
                pancreatic_risk = "🔴 High" if pancreatic_risk_score >= 6 else "🟠 Moderate" if pancreatic_risk_score >= 3 else "🟢 Low"
                st.metric("Pancreatic Cancer Risk", pancreatic_risk, f"Score: {pancreatic_risk_score}/10")
        
        with risk_col3:
            if cancer_analysis:
                colorectal_risk_score = calculate_cancer_risk(df_all, "colorectal")
                colorectal_risk = "🔴 High" if colorectal_risk_score >= 6 else "🟠 Moderate" if colorectal_risk_score >= 3 else "🟢 Low"
                st.metric("Colorectal Cancer Risk", colorectal_risk, f"Score: {colorectal_risk_score}/10")

        # ----------------------------
        # Clinical Recommendations
        # ----------------------------
        st.header("💡 Clinical Recommendations")
        
        recommendations = []
        if diabetes_risk_score >= 3:
            recommendations.extend([
                "Consider oral glucose tolerance test",
                "Lifestyle modification: diet and exercise",
                "Monitor glucose levels regularly"
            ])
        
        if pancreatic_risk_score >= 4:
            recommendations.extend([
                "Consider abdominal ultrasound",
                "Consult gastroenterology specialist",
                "Monitor CA19-9 levels"
            ])
            
        if colorectal_risk_score >= 4:
            recommendations.extend([
                "Consider colonoscopy screening",
                "Discuss fecal immunochemical test",
                "Review family cancer history"
            ])
            
        if recommendations:
            for rec in recommendations:
                st.write(f"• {rec}")
        else:
            st.success("No immediate concerning trends detected. Continue routine monitoring.")

        # ----------------------------
        # Enhanced Genetic Insights
        # ----------------------------
        if show_genetic_insights:
            st.header("🧬 Genetic Association Insights")
            
            gene_risk_factors = {
                "High Diabetes Risk": ["TCF7L2", "PPARG", "FTO"],
                "Pancreatic Cancer Susceptibility": ["KRAS", "CDKN2A", "BRCA2"],
                "Colorectal Cancer Markers": ["APC", "MLH1", "MSH2"]
            }
            
            for risk_type, genes in gene_risk_factors.items():
                with st.expander(f"{risk_type} Genes"):
                    st.write(f"Associated genes: {', '.join(genes)}")
                    st.caption("Consider genetic testing if strong family history present")

        # ----------------------------
        # Export Functionality
        # ----------------------------
        st.header("📤 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Excel export
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_all.to_excel(writer, sheet_name='Lab_Data', index=False)
                # Add summary sheet
                summary_data = {
                    'Metric': ['Diabetes Risk Score', 'Pancreatic Cancer Risk', 'Colorectal Cancer Risk'],
                    'Value': [diabetes_risk_score, pancreatic_risk_score, colorectal_risk_score],
                    'Assessment': [diabetes_risk, pancreatic_risk, colorectal_risk]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Risk_Summary', index=False)
            
            st.download_button(
                label="📊 Download Complete Report (Excel)",
                data=excel_buffer.getvalue(),
                file_name="digital_twin_comprehensive_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            # PDF Report (simplified)
            report_text = f"""
            DIGITAL TWIN HEALTH REPORT
            Generated on: {datetime.now().strftime('%Y-%m-%d')}
            
            PATIENT SUMMARY:
            Age: {age}, Gender: {gender}, BMI: {bmi} ({bmi_category})
            
            RISK ASSESSMENT:
            Diabetes: {diabetes_risk} (Score: {diabetes_risk_score})
            Pancreatic Cancer: {pancreatic_risk} (Score: {pancreatic_risk_score})
            Colorectal Cancer: {colorectal_risk} (Score: {colorectal_risk_score})
            
            RECOMMENDATIONS:
            {chr(10).join(recommendations) if recommendations else "Continue routine monitoring"}
            """
            
            st.download_button(
                label="📄 Download Summary Report (TXT)",
                data=report_text,
                file_name="health_risk_summary.txt",
                mime="text/plain"
            )

else:
    st.info("📁 Upload PDF lab reports to start analysis. Multiple files allowed for trend analysis.")

# ----------------------------
# Footer
# ----------------------------
st.markdown("---")
st.markdown("""
*Disclaimer: This tool is for educational and research purposes only. 
Always consult healthcare professionals for medical decisions.*
""")
