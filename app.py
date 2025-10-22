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

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .risk-high { color: #ff4b4b; font-weight: bold; }
    .risk-moderate { color: #ffa500; font-weight: bold; }
    .risk-low { color: #00cc66; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🧬 Digital Twin Health Risk Analyzer")
st.markdown("""
Create your **Digital Twin**, upload lab reports, analyze trends, and get **comprehensive health risk assessment**.
""")

# ----------------------------
# GENE DATABASE & SYMPTOM MAPPING
# ----------------------------
GENE_ASSOCIATIONS = {
    "Type 1 Diabetes": ["HLA-DQA1", "HLA-DQB1", "HLA-DRB1", "CTLA4", "IL2RA", "PTPN22"],
    "Type 2 Diabetes": ["TCF7L2", "PPARG", "KCNJ11", "ABCC8", "LCAT", "APOE", "FTO", "IRS1", "IRS2"],
    "Pancreatic Cancer": ["KRAS", "TP53", "CDKN2A", "SMAD4", "BRCA2", "PALB2"],
    "Colorectal Cancer": ["APC", "KRAS", "TP53", "MLH1", "MSH2", "MSH6", "PMS2"],
    "Liver Cancer": ["TP53", "CTNNB1", "AXIN1", "ARID1A", "TERT"],
    "Cardiovascular Disease": ["APOE", "PCSK9", "LDLR", "APOB", "CETP"],
    "Hypertension": ["ACE", "AGTR1", "NPPA", "CYP11B2"],
    "Obesity": ["FTO", "MC4R", "BDNF", "POMC"]
}

SYMPTOM_RISK_FACTORS = {
    "Diabetes": {
        "symptoms": ["frequent_urination", "increased_thirst", "unexplained_weight_loss", "fatigue", "blurred_vision"],
        "weight": 2
    },
    "Pancreatic Cancer": {
        "symptoms": ["abdominal_pain", "jaundice", "weight_loss", "loss_of_appetite", "back_pain", "new_onset_diabetes"],
        "weight": 3
    },
    "Colorectal Cancer": {
        "symptoms": ["blood_in_stool", "abdominal_pain", "change_in_bowel_habits", "unexplained_weight_loss", "fatigue"],
        "weight": 3
    },
    "Liver Disease": {
        "symptoms": ["jaundice", "abdominal_pain", "fatigue", "nausea", "swelling_in_legs"],
        "weight": 2
    },
    "Cardiovascular Disease": {
        "symptoms": ["chest_pain", "shortness_of_breath", "palpitations", "swelling_in_legs", "fatigue"],
        "weight": 2
    }
}

# ----------------------------
# PDF PROCESSING FUNCTIONS
# ----------------------------
def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    try:
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

def extract_lab_values_simple(text, tests):
    """Simple and robust lab value extraction"""
    lab_data = {}
    
    text = re.sub(r'\s+', ' ', text)
    
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
                except ValueError:
                    pass
    
    # Extract date
    date_match = re.search(r'Received On\s*:\s*(\d{2}/\d{2}/\d{4})', text)
    if date_match:
        try:
            lab_data['Date'] = pd.to_datetime(date_match.group(1), format='%d/%m/%Y')
        except:
            pass
    
    return lab_data

# ----------------------------
# ENHANCED RISK ASSESSMENT FUNCTIONS
# ----------------------------
def calculate_diabetes_risk(df, age, bmi, family_history, symptoms, genetic_factors):
    """Enhanced diabetes risk calculation with symptoms and genes"""
    risk_score = 0
    
    # Lab values (40%)
    if "HbA1c" in df.columns:
        last_hba1c = df["HbA1c"].dropna().iloc[-1] if not df["HbA1c"].dropna().empty else None
        if last_hba1c:
            if last_hba1c > 6.5: risk_score += 3
            elif last_hba1c > 5.7: risk_score += 2
            elif last_hba1c > 5.5: risk_score += 1
    
    if "Glucose" in df.columns:
        last_glucose = df["Glucose"].dropna().iloc[-1] if not df["Glucose"].dropna().empty else None
        if last_glucose:
            if last_glucose > 126: risk_score += 2
            elif last_glucose > 100: risk_score += 1
    
    # Demographic factors (20%)
    if age > 45: risk_score += 1
    if bmi >= 25: risk_score += 1
    if family_history: risk_score += 2
    
    # Symptoms (20%)
    diabetes_symptoms = SYMPTOM_RISK_FACTORS["Diabetes"]["symptoms"]
    symptom_count = sum(1 for symptom in diabetes_symptoms if symptoms.get(symptom, False))
    risk_score += min(symptom_count * SYMPTOM_RISK_FACTORS["Diabetes"]["weight"], 4)
    
    # Genetic factors (20%)
    diabetes_genes = GENE_ASSOCIATIONS["Type 2 Diabetes"]
    genetic_count = sum(1 for gene in diabetes_genes if genetic_factors.get(gene, False))
    risk_score += min(genetic_count, 2)
    
    return min(risk_score, 10)

def calculate_cancer_risk(df, cancer_type, symptoms, genetic_factors, family_history):
    """Enhanced cancer risk calculation"""
    risk_score = 0
    
    if cancer_type == "pancreatic":
        # Lab markers
        markers = {
            "HbA1c": (1.5, 6.0),
            "ALT": (1, 40),
            "AST": (1, 40),
            "Bilirubin": (2, 1.2)
        }
        
        for marker, (weight, threshold) in markers.items():
            if marker in df.columns:
                last_value = df[marker].dropna().iloc[-1] if not df[marker].dropna().empty else None
                if last_value and last_value > threshold:
                    risk_score += weight
        
        # Symptoms
        cancer_symptoms = SYMPTOM_RISK_FACTORS["Pancreatic Cancer"]["symptoms"]
        symptom_count = sum(1 for symptom in cancer_symptoms if symptoms.get(symptom, False))
        risk_score += symptom_count * SYMPTOM_RISK_FACTORS["Pancreatic Cancer"]["weight"]
        
        # Genetic factors
        cancer_genes = GENE_ASSOCIATIONS["Pancreatic Cancer"]
        genetic_count = sum(1 for gene in cancer_genes if genetic_factors.get(gene, False))
        risk_score += genetic_count * 1.5
        
        # Family history
        if family_history: risk_score += 2
    
    elif cancer_type == "colorectal":
        # Lab markers
        if "Hb" in df.columns:
            last_hb = df["Hb"].dropna().iloc[-1] if not df["Hb"].dropna().empty else None
            if last_hb and last_hb < 12: risk_score += 2
        
        # Symptoms
        cancer_symptoms = SYMPTOM_RISK_FACTORS["Colorectal Cancer"]["symptoms"]
        symptom_count = sum(1 for symptom in cancer_symptoms if symptoms.get(symptom, False))
        risk_score += symptom_count * SYMPTOM_RISK_FACTORS["Colorectal Cancer"]["weight"]
        
        # Genetic factors
        cancer_genes = GENE_ASSOCIATIONS["Colorectal Cancer"]
        genetic_count = sum(1 for gene in cancer_genes if genetic_factors.get(gene, False))
        risk_score += genetic_count * 1.5
        
        # Family history
        if family_history: risk_score += 2
    
    return min(risk_score, 10)

def get_risk_label(score):
    """Convert risk score to label"""
    if score >= 7: return "🔴 High"
    elif score >= 4: return "🟠 Moderate"
    else: return "🟢 Low"

# ----------------------------
# SIDEBAR
# ----------------------------
with st.sidebar:
    st.header("⚙️ Analysis Settings")
    st.info("Configure your risk assessment parameters")
    
    st.markdown("---")
    st.header("🔬 Test Selection")
    
    common_tests = st.multiselect(
        "Select tests to extract:",
        ["HbA1c", "Glucose", "Hb", "WBC", "Platelet", "ALT", "AST", "ESR", "Calcium", "Creatinine", "Bilirubin", "Albumin"],
        default=["HbA1c", "Glucose", "Hb", "WBC", "Platelet", "ALT", "AST"]
    )

# ----------------------------
# MAIN CONTENT
# ----------------------------
st.header("👤 Digital Twin Profile")

col1, col2, col3 = st.columns(3)
with col1:
    age = st.number_input("Age", 0, 120, 34)
    weight = st.number_input("Weight (kg)", 10, 200, 70)
with col2:
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    height = st.number_input("Height (cm)", 50, 250, 170)
with col3:
    bmi = round(weight / ((height/100) ** 2), 2) if height > 0 else 0
    st.metric("BMI", f"{bmi} ({'Obese' if bmi >= 30 else 'Overweight' if bmi >= 25 else 'Normal' if bmi >= 18.5 else 'Underweight'})")

# Family History
st.subheader("🏥 Family Medical History")
fam_col1, fam_col2, fam_col3 = st.columns(3)
with fam_col1:
    family_diabetes = st.checkbox("Diabetes")
    family_heart = st.checkbox("Heart Disease")
with fam_col2:
    family_cancer = st.checkbox("Cancer")
    family_hypertension = st.checkbox("Hypertension")
with fam_col3:
    smoking = st.checkbox("Smoking History")
    alcohol = st.selectbox("Alcohol", ["Never", "Occasional", "Regular"])

# Symptoms Input
st.subheader("🤒 Current Symptoms")
symptom_col1, symptom_col2, symptom_col3 = st.columns(3)

symptoms = {}
with symptom_col1:
    symptoms['frequent_urination'] = st.checkbox("Frequent Urination")
    symptoms['increased_thirst'] = st.checkbox("Increased Thirst")
    symptoms['unexplained_weight_loss'] = st.checkbox("Unexplained Weight Loss")
with symptom_col2:
    symptoms['abdominal_pain'] = st.checkbox("Abdominal Pain")
    symptoms['jaundice'] = st.checkbox("Jaundice/Yellow Skin")
    symptoms['fatigue'] = st.checkbox("Persistent Fatigue")
with symptom_col3:
    symptoms['blood_in_stool'] = st.checkbox("Blood in Stool")
    symptoms['blurred_vision'] = st.checkbox("Blurred Vision")
    symptoms['chest_pain'] = st.checkbox("Chest Pain")

# Genetic Factors
st.subheader("🧬 Genetic Risk Factors")
st.info("Select known genetic markers from previous genetic testing")

genetic_col1, genetic_col2 = st.columns(2)
genetic_factors = {}

with genetic_col1:
    st.markdown("**Diabetes Genes**")
    for gene in GENE_ASSOCIATIONS["Type 2 Diabetes"][:4]:
        genetic_factors[gene] = st.checkbox(f"{gene} (T2D)")
    
    st.markdown("**Pancreatic Cancer Genes**")
    for gene in GENE_ASSOCIATIONS["Pancreatic Cancer"][:3]:
        genetic_factors[gene] = st.checkbox(f"{gene} (Pancreatic)")

with genetic_col2:
    st.markdown("**Colorectal Cancer Genes**")
    for gene in GENE_ASSOCIATIONS["Colorectal Cancer"][:4]:
        genetic_factors[gene] = st.checkbox(f"{gene} (Colorectal)")
    
    st.markdown("**Cardiovascular Genes**")
    for gene in GENE_ASSOCIATIONS["Cardiovascular Disease"][:3]:
        genetic_factors[gene] = st.checkbox(f"{gene} (Heart)")

# PDF Upload Section
st.header("📁 Upload Lab Reports")

uploaded_files = st.file_uploader(
    "Choose PDF lab reports", 
    type="pdf", 
    accept_multiple_files=True
)

# Initialize session state
if 'df_all' not in st.session_state:
    st.session_state.df_all = pd.DataFrame()

if uploaded_files:
    st.success(f"📄 {len(uploaded_files)} file(s) uploaded!")
    
    if st.button("🚀 Process PDF Files", type="primary"):
        all_extracted_data = []
        
        for i, file in enumerate(uploaded_files):
            with st.spinner(f"Processing {file.name}..."):
                text = extract_text_from_pdf(file)
                
                if text:
                    data = extract_lab_values_simple(text, common_tests)
                    if data:
                        data['Filename'] = file.name
                        all_extracted_data.append(data)
                        st.success(f"✅ {file.name} processed")
                    else:
                        st.warning(f"⚠️ No data extracted from {file.name}")
                else:
                    st.error(f"❌ Could not read {file.name}")
        
        if all_extracted_data:
            st.session_state.df_all = pd.DataFrame(all_extracted_data)
            if 'Date' in st.session_state.df_all.columns:
                st.session_state.df_all['Date'] = pd.to_datetime(
                    st.session_state.df_all['Date'], errors='coerce'
                )
                st.session_state.df_all = st.session_state.df_all.sort_values('Date').reset_index(drop=True)

# Display Results and Analysis
if not st.session_state.df_all.empty:
    df = st.session_state.df_all
    
    st.header("📊 Extracted Lab Data")
    st.dataframe(df, use_container_width=True)
    
    # Enhanced Risk Assessment
    st.header("🩺 Comprehensive Risk Assessment")
    
    # Calculate risks
    diabetes_risk_score = calculate_diabetes_risk(df, age, bmi, family_diabetes, symptoms, genetic_factors)
    pancreatic_risk_score = calculate_cancer_risk(df, "pancreatic", symptoms, genetic_factors, family_cancer)
    colorectal_risk_score = calculate_cancer_risk(df, "colorectal", symptoms, genetic_factors, family_cancer)
    
    # Display Risk Scores
    risk_col1, risk_col2, risk_col3 = st.columns(3)
    
    with risk_col1:
        diabetes_risk = get_risk_label(diabetes_risk_score)
        st.metric("Diabetes Risk", diabetes_risk, f"Score: {diabetes_risk_score}/10")
        
    with risk_col2:
        pancreatic_risk = get_risk_label(pancreatic_risk_score)
        st.metric("Pancreatic Cancer Risk", pancreatic_risk, f"Score: {pancreatic_risk_score}/10")
        
    with risk_col3:
        colorectal_risk = get_risk_label(colorectal_risk_score)
        st.metric("Colorectal Cancer Risk", colorectal_risk, f"Score: {colorectal_risk_score}/10")
    
    # Risk Breakdown
    st.subheader("📋 Risk Factor Analysis")
    
    risk_col1, risk_col2 = st.columns(2)
    
    with risk_col1:
        st.markdown("**🔬 Lab-Based Risks**")
        if 'HbA1c' in df.columns and not df['HbA1c'].isna().all():
            hba1c = df['HbA1c'].dropna().iloc[-1]
            status = "🟢 Normal" if hba1c <= 5.6 else "🟡 Prediabetic" if hba1c <= 6.4 else "🔴 Diabetic"
            st.write(f"- HbA1c: {hba1c}% ({status})")
        
        if 'ALT' in df.columns and not df['ALT'].isna().all():
            alt = df['ALT'].dropna().iloc[-1]
            status = "🔴 High" if alt > 50 else "🟢 Normal"
            st.write(f"- ALT: {alt} U/L ({status})")
        
        if 'Hb' in df.columns and not df['Hb'].isna().all():
            hb = df['Hb'].dropna().iloc[-1]
            status = "🔴 Low" if (gender == "Male" and hb < 13) or (gender == "Female" and hb < 12) else "🟢 Normal"
            st.write(f"- Hemoglobin: {hb} g/dL ({status})")
    
    with risk_col2:
        st.markdown("**🧬 Genetic Risks**")
        active_genes = [gene for gene, active in genetic_factors.items() if active]
        if active_genes:
            for gene in active_genes:
                # Find which condition this gene is associated with
                for condition, genes in GENE_ASSOCIATIONS.items():
                    if gene in genes:
                        st.write(f"- {gene} ({condition})")
                        break
        else:
            st.write("- No known genetic risk factors selected")
        
        st.markdown("**🤒 Symptom Risks**")
        active_symptoms = [symptom for symptom, active in symptoms.items() if active]
        if active_symptoms:
            for symptom in active_symptoms:
                st.write(f"- {symptom.replace('_', ' ').title()}")
        else:
            st.write("- No concerning symptoms reported")
    
    # Gene Association Insights
    st.subheader("🧬 Gene Association Insights")
    
    gene_col1, gene_col2 = st.columns(2)
    
    with gene_col1:
        st.markdown("**Diabetes Associated Genes**")
        for gene in GENE_ASSOCIATIONS["Type 2 Diabetes"]:
            status = "✅ Selected" if genetic_factors.get(gene, False) else "⚪ Not Selected"
            st.write(f"- {gene} {status}")
    
    with gene_col2:
        st.markdown("**Cancer Associated Genes**")
        for gene in GENE_ASSOCIATIONS["Pancreatic Cancer"][:3] + GENE_ASSOCIATIONS["Colorectal Cancer"][:3]:
            status = "✅ Selected" if genetic_factors.get(gene, False) else "⚪ Not Selected"
            st.write(f"- {gene} {status}")
    
    # Clinical Recommendations
    st.subheader("💡 Personalized Recommendations")
    
    recommendations = []
    
    # Diabetes recommendations
    if diabetes_risk_score >= 4:
        recommendations.extend([
            "🩺 **Schedule HbA1c test every 3-6 months**",
            "🥗 **Consult nutritionist for diabetic diet plan**",
            "🏃 **Start regular exercise (30 mins, 5 days/week)**",
            "📊 **Monitor blood glucose levels regularly**"
        ])
    
    # Cancer risk recommendations
    if pancreatic_risk_score >= 5:
        recommendations.extend([
            "🔍 **Consider abdominal ultrasound**",
            "🩺 **Consult gastroenterology specialist**",
            "📋 **Discuss family cancer history with oncologist**"
        ])
    
    if colorectal_risk_score >= 5:
        recommendations.extend([
            "🔍 **Schedule colonoscopy screening**",
            "💊 **Discuss fecal immunochemical test (FIT)**",
            "🩺 **Consult gastroenterology specialist**"
        ])
    
    # General health recommendations
    if bmi >= 25:
        recommendations.append("⚖️ **Weight management program recommended**")
    
    if smoking:
        recommendations.append("🚭 **Smoking cessation program strongly recommended**")
    
    if not recommendations:
        recommendations.append("🎉 **Continue with routine health monitoring**")
    
    for rec in recommendations:
        st.write(rec)
    
    # Export Functionality
    st.header("📤 Export Comprehensive Report")
    
    if st.button("Generate Full Health Report"):
        report_data = {
            "Patient Profile": {
                "Age": age, "Gender": gender, "BMI": bmi,
                "Family History": {
                    "Diabetes": family_diabetes,
                    "Cancer": family_cancer,
                    "Heart Disease": family_heart
                }
            },
            "Risk Scores": {
                "Diabetes": f"{diabetes_risk_score}/10 ({diabetes_risk})",
                "Pancreatic Cancer": f"{pancreatic_risk_score}/10 ({pancreatic_risk})",
                "Colorectal Cancer": f"{colorectal_risk_score}/10 ({colorectal_risk})"
            },
            "Recommendations": recommendations
        }
        
        st.download_button(
            label="⬇️ Download Health Report",
            data=str(report_data),
            file_name=f"comprehensive_health_report_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )

else:
    st.info("👆 Upload PDF lab reports and click 'Process PDF Files' to begin analysis.")

# ----------------------------
# FOOTER
# ----------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center'><em>Disclaimer: This tool is for educational purposes only. Consult healthcare professionals for medical decisions.</em></div>",
    unsafe_allow_html=True
)
