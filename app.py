import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
**Complete manual health data input** - Create your digital twin by entering lab results, symptoms, and health information.
""")

# ----------------------------
# SYMPTOMS DATABASE
# ----------------------------
SYMPTOMS_DATABASE = {
    "Diabetes": {
        "symptoms": [
            "Frequent urination", "Increased thirst", "Extreme hunger", 
            "Unexplained weight loss", "Fatigue", "Blurred vision",
            "Slow healing wounds", "Frequent infections", "Tingling in hands/feet"
        ],
        "risk_weight": 2
    },
    "Liver Disease": {
        "symptoms": [
            "Jaundice (yellow skin)", "Abdominal pain", "Fatigue", "Nausea/Vomiting",
            "Loss of appetite", "Swelling in legs", "Dark urine", 
            "Pale stools", "Itchy skin"
        ],
        "risk_weight": 3
    },
    "Cardiovascular": {
        "symptoms": [
            "Chest pain", "Shortness of breath", "Palpitations", 
            "Dizziness", "Swelling in ankles", "Fatigue",
            "Irregular heartbeat", "Fainting", "Cold sweats"
        ],
        "risk_weight": 2
    },
    "Kidney Disease": {
        "symptoms": [
            "Swelling in face", "Swelling in hands", "Swelling in feet",
            "Fatigue", "Nausea", "Shortness of breath", 
            "Blood in urine", "Foamy urine", "Poor appetite"
        ],
        "risk_weight": 2
    },
    "Thyroid Issues": {
        "symptoms": [
            "Fatigue", "Weight gain", "Weight loss", "Mood swings",
            "Hair loss", "Temperature sensitivity", "Dry skin",
            "Muscle weakness", "Sleep problems"
        ],
        "risk_weight": 1
    },
    "Anemia": {
        "symptoms": [
            "Fatigue", "Weakness", "Pale skin", "Shortness of breath",
            "Dizziness", "Cold hands/feet", "Headaches", 
            "Chest pain", "Brittle nails"
        ],
        "risk_weight": 2
    },
    "Cancer General": {
        "symptoms": [
            "Unexplained weight loss", "Fatigue", "Fever", 
            "Persistent pain", "Skin changes", "Lump or thickening",
            "Bowel changes", "Persistent cough", "Difficulty swallowing"
        ],
        "risk_weight": 4
    }
}

# ----------------------------
# GENE DATABASE
# ----------------------------
GENE_ASSOCIATIONS = {
    "Type 2 Diabetes": ["TCF7L2", "PPARG", "KCNJ11", "ABCC8", "FTO", "IRS1"],
    "Pancreatic Cancer": ["KRAS", "TP53", "CDKN2A", "SMAD4", "BRCA2"],
    "Colorectal Cancer": ["APC", "KRAS", "TP53", "MLH1", "MSH2"],
    "Cardiovascular Disease": ["APOE", "PCSK9", "LDLR", "APOB", "CETP"],
    "Liver Disease": ["PNPLA3", "TM6SF2", "HFE", "SERPINA1"],
    "Obesity": ["FTO", "MC4R", "BDNF", "POMC"]
}

# ----------------------------
# INITIALIZE SESSION STATE
# ----------------------------
if 'health_data' not in st.session_state:
    st.session_state.health_data = pd.DataFrame()
if 'symptoms_data' not in st.session_state:
    st.session_state.symptoms_data = {}
if 'genetic_data' not in st.session_state:
    st.session_state.genetic_data = {}

# ----------------------------
# MANUAL DATA INPUT SECTIONS
# ----------------------------

# 1. PATIENT PROFILE
st.header("👤 Patient Profile & Demographics")

col1, col2, col3 = st.columns(3)
with col1:
    patient_name = st.text_input("Full Name", "John Doe")
    age = st.number_input("Age", 0, 120, 34)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    
with col2:
    weight = st.number_input("Weight (kg)", 10, 200, 70)
    height = st.number_input("Height (cm)", 50, 250, 170)
    if height > 0:
        bmi = round(weight / ((height/100) ** 2), 2)
        bmi_category = "Obese" if bmi >= 30 else "Overweight" if bmi >= 25 else "Normal" if bmi >= 18.5 else "Underweight"
        st.metric("BMI", f"{bmi} ({bmi_category})")
    
with col3:
    location = st.text_input("Location", "Mumbai")
    activity_level = st.selectbox("Activity Level", ["Sedentary", "Light", "Moderate", "Active", "Very Active"])
    alcohol_consumption = st.selectbox("Alcohol Consumption", ["Never", "Occasional", "Regular"])

# 2. FAMILY HISTORY
st.header("🏥 Family Medical History")

fam_col1, fam_col2, fam_col3 = st.columns(3)
with fam_col1:
    family_diabetes = st.checkbox("Diabetes")
    family_heart_disease = st.checkbox("Heart Disease")
    family_hypertension = st.checkbox("Hypertension")
    
with fam_col2:
    family_cancer = st.checkbox("Cancer")
    family_liver_disease = st.checkbox("Liver Disease")
    family_kidney_disease = st.checkbox("Kidney Disease")
    
with fam_col3:
    smoking_history = st.checkbox("Smoking History")
    family_obesity = st.checkbox("Obesity")
    family_thyroid = st.checkbox("Thyroid Disorders")

# 3. SYMPTOMS INPUT
st.header("🤒 Current Symptoms")
st.info("Select all symptoms you're currently experiencing")

# Organize symptoms by category
symptoms_container = st.container()

with symptoms_container:
    for condition, data in SYMPTOMS_DATABASE.items():
        with st.expander(f"🔍 {condition} Symptoms", expanded=False):
            cols = st.columns(2)
            for i, symptom in enumerate(data["symptoms"]):
                col_idx = i % 2
                with cols[col_idx]:
                    symptom_key = f"{condition}_{symptom}"
                    st.session_state.symptoms_data[symptom_key] = st.checkbox(symptom, key=symptom_key)

# 4. GENETIC FACTORS
st.header("🧬 Known Genetic Factors")
st.info("Select any known genetic markers from previous genetic testing")

genetic_container = st.container()
with genetic_container:
    genetic_cols = st.columns(2)
    col_idx = 0
    
    for condition, genes in GENE_ASSOCIATIONS.items():
        with genetic_cols[col_idx]:
            st.subheader(f"{condition}")
            for gene in genes:
                gene_key = f"gene_{gene}"
                st.session_state.genetic_data[gene_key] = st.checkbox(gene, key=gene_key)
        
        col_idx = (col_idx + 1) % 2

# 5. LAB RESULTS INPUT
st.header("📊 Lab Test Results")
st.info("Enter your latest lab test results. Leave blank if not tested.")

lab_date = st.date_input("Test Date", datetime.now())

# Lab results input in expandable sections
with st.expander("🩸 Complete Blood Count (CBC)", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        hemoglobin = st.number_input("Hemoglobin (g/dL)", 5.0, 20.0, 13.0, step=0.1)
        wbc = st.number_input("WBC (10³/μL)", 1.0, 50.0, 5.0, step=0.1)
    with col2:
        platelet = st.number_input("Platelet Count (10³/μL)", 50.0, 500.0, 200.0, step=10.0)
        rbc = st.number_input("RBC (10⁶/μL)", 3.0, 8.0, 5.0, step=0.1)
    with col3:
        hematocrit = st.number_input("Hematocrit (%)", 30.0, 60.0, 42.0, step=0.1)
        esr = st.number_input("ESR (mm/hr)", 0.0, 100.0, 10.0, step=1.0)

with st.expander("🩺 Diabetes & Metabolic Panel"):
    col1, col2 = st.columns(2)
    with col1:
        hba1c = st.number_input("HbA1c (%)", 4.0, 15.0, 5.5, step=0.1)
        glucose = st.number_input("Glucose (mg/dL)", 50.0, 300.0, 90.0, step=1.0)
    with col2:
        insulin = st.number_input("Insulin (μIU/mL)", 0.0, 50.0, 5.0, step=0.1)
        c_peptide = st.number_input("C-Peptide (ng/mL)", 0.0, 10.0, 1.5, step=0.1)

with st.expander("💊 Liver Function Tests"):
    col1, col2 = st.columns(2)
    with col1:
        alt = st.number_input("ALT (SGPT) U/L", 5.0, 200.0, 25.0, step=1.0)
        ast = st.number_input("AST (SGOT) U/L", 5.0, 200.0, 25.0, step=1.0)
    with col2:
        alp = st.number_input("ALP U/L", 30.0, 300.0, 80.0, step=1.0)
        bilirubin = st.number_input("Total Bilirubin (mg/dL)", 0.1, 10.0, 0.8, step=0.1)

with st.expander("🫀 Kidney Function & Electrolytes"):
    col1, col2 = st.columns(2)
    with col1:
        creatinine = st.number_input("Creatinine (mg/dL)", 0.5, 10.0, 0.9, step=0.1)
        urea = st.number_input("Urea (mg/dL)", 10.0, 100.0, 25.0, step=1.0)
    with col2:
        sodium = st.number_input("Sodium (mmol/L)", 130.0, 150.0, 140.0, step=1.0)
        potassium = st.number_input("Potassium (mmol/L)", 3.0, 6.0, 4.0, step=0.1)

with st.expander("📈 Lipid Profile"):
    col1, col2 = st.columns(2)
    with col1:
        cholesterol = st.number_input("Total Cholesterol (mg/dL)", 100.0, 300.0, 180.0, step=5.0)
        ldl = st.number_input("LDL Cholesterol (mg/dL)", 50.0, 250.0, 100.0, step=5.0)
    with col2:
        hdl = st.number_input("HDL Cholesterol (mg/dL)", 20.0, 100.0, 50.0, step=5.0)
        triglycerides = st.number_input("Triglycerides (mg/dL)", 50.0, 500.0, 120.0, step=5.0)

with st.expander("🔬 Other Important Tests"):
    col1, col2 = st.columns(2)
    with col1:
        calcium = st.number_input("Calcium (mg/dL)", 7.0, 12.0, 9.5, step=0.1)
        tsh = st.number_input("TSH (μIU/mL)", 0.1, 10.0, 2.0, step=0.1)
    with col2:
        vitamin_d = st.number_input("Vitamin D (ng/mL)", 10.0, 100.0, 30.0, step=1.0)
        psa = st.number_input("PSA (ng/mL)", 0.0, 10.0, 1.0, step=0.1)

# ----------------------------
# SAVE DATA BUTTON
# ----------------------------
if st.button("💾 Save Health Data", type="primary"):
    # Compile all lab data
    lab_data = {
        'Date': lab_date,
        'Hemoglobin': hemoglobin,
        'WBC': wbc,
        'Platelet': platelet,
        'RBC': rbc,
        'Hematocrit': hematocrit,
        'ESR': esr,
        'HbA1c': hba1c,
        'Glucose': glucose,
        'Insulin': insulin,
        'C_Peptide': c_peptide,
        'ALT': alt,
        'AST': ast,
        'ALP': alp,
        'Bilirubin': bilirubin,
        'Creatinine': creatinine,
        'Urea': urea,
        'Sodium': sodium,
        'Potassium': potassium,
        'Cholesterol': cholesterol,
        'LDL': ldl,
        'HDL': hdl,
        'Triglycerides': triglycerides,
        'Calcium': calcium,
        'TSH': tsh,
        'Vitamin_D': vitamin_d,
        'PSA': psa,
        'Patient_Name': patient_name,
        'Age': age,
        'Gender': gender,
        'BMI': bmi
    }
    
    # Convert to DataFrame
    new_entry = pd.DataFrame([lab_data])
    
    if st.session_state.health_data.empty:
        st.session_state.health_data = new_entry
    else:
        st.session_state.health_data = pd.concat([st.session_state.health_data, new_entry], ignore_index=True)
    
    st.success("✅ Health data saved successfully!")

# ----------------------------
# RISK ASSESSMENT FUNCTIONS
# ----------------------------
def calculate_diabetes_risk(lab_data, symptoms, family_history, age, bmi):
    risk_score = 0
    
    # Lab values
    if lab_data.get('HbA1c', 0) > 6.5:
        risk_score += 3
    elif lab_data.get('HbA1c', 0) > 5.7:
        risk_score += 2
    
    if lab_data.get('Glucose', 0) > 126:
        risk_score += 2
    
    # Symptoms
    diabetes_symptoms = [s for s in SYMPTOMS_DATABASE["Diabetes"]["symptoms"] 
                        if st.session_state.symptoms_data.get(f"Diabetes_{s}", False)]
    risk_score += len(diabetes_symptoms)
    
    # Demographics
    if age > 45:
        risk_score += 1
    if bmi >= 25:
        risk_score += 1
    if family_history:
        risk_score += 2
    
    return min(risk_score, 10)

def calculate_liver_risk(lab_data, symptoms, alcohol_consumption):
    risk_score = 0
    
    # Lab values
    if lab_data.get('ALT', 0) > 40:
        risk_score += 2
    if lab_data.get('AST', 0) > 40:
        risk_score += 2
    if lab_data.get('Bilirubin', 0) > 1.2:
        risk_score += 2
    
    # Symptoms
    liver_symptoms = [s for s in SYMPTOMS_DATABASE["Liver Disease"]["symptoms"] 
                     if st.session_state.symptoms_data.get(f"Liver Disease_{s}", False)]
    risk_score += len(liver_symptoms)
    
    # Lifestyle
    if alcohol_consumption == "Regular":
        risk_score += 2
    
    return min(risk_score, 10)

def get_risk_label(score):
    if score >= 7:
        return "🔴 High"
    elif score >= 4:
        return "🟠 Moderate"
    else:
        return "🟢 Low"

# ----------------------------
# DISPLAY RESULTS
# ----------------------------
if not st.session_state.health_data.empty:
    st.header("📊 Your Health Dashboard")
    
    current_data = st.session_state.health_data.iloc[-1].to_dict()
    
    # Risk Assessment
    st.subheader("🩺 Health Risk Assessment")
    
    diabetes_risk = calculate_diabetes_risk(
        current_data, 
        st.session_state.symptoms_data, 
        family_diabetes, 
        age, 
        bmi
    )
    
    liver_risk = calculate_liver_risk(
        current_data,
        st.session_state.symptoms_data,
        alcohol_consumption
    )
    
    # Display Risk Scores
    risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4)
    
    with risk_col1:
        st.metric("Diabetes Risk", get_risk_label(diabetes_risk), f"Score: {diabetes_risk}/10")
    
    with risk_col2:
        st.metric("Liver Disease Risk", get_risk_label(liver_risk), f"Score: {liver_risk}/10")
    
    with risk_col3:
        # Cardiovascular risk (simplified)
        cv_risk = 3 if family_heart_disease else 1
        if current_data.get('Cholesterol', 0) > 200:
            cv_risk += 2
        if smoking_history:
            cv_risk += 2
        st.metric("Heart Disease Risk", get_risk_label(cv_risk), f"Score: {cv_risk}/10")
    
    with risk_col4:
        # Cancer risk (simplified)
        cancer_risk = 3 if family_cancer else 1
        cancer_symptoms = [s for s in SYMPTOMS_DATABASE["Cancer General"]["symptoms"] 
                          if st.session_state.symptoms_data.get(f"Cancer General_{s}", False)]
        cancer_risk += len(cancer_symptoms)
        st.metric("Cancer Risk", get_risk_label(cancer_risk), f"Score: {cancer_risk}/10")
    
    # Symptoms Analysis
    st.subheader("🤒 Symptoms Analysis")
    
    active_symptoms = []
    for symptom_key, is_active in st.session_state.symptoms_data.items():
        if is_active:
            active_symptoms.append(symptom_key.replace("_", " "))
    
    if active_symptoms:
        st.warning(f"**Active Symptoms:** {', '.join(active_symptoms)}")
    else:
        st.success("**No concerning symptoms reported**")
    
    # Lab Results Summary
    st.subheader("📈 Key Lab Values")
    
    lab_col1, lab_col2, lab_col3, lab_col4 = st.columns(4)
    
    with lab_col1:
        hba1c_val = current_data.get('HbA1c', 0)
        status = "🔴 High" if hba1c_val > 6.5 else "🟡 Borderline" if hba1c_val > 5.7 else "🟢 Normal"
        st.metric("HbA1c", f"{hba1c_val}%", status)
    
    with lab_col2:
        alt_val = current_data.get('ALT', 0)
        status = "🔴 High" if alt_val > 40 else "🟢 Normal"
        st.metric("ALT", f"{alt_val} U/L", status)
    
    with lab_col3:
        creatinine_val = current_data.get('Creatinine', 0)
        status = "🔴 High" if creatinine_val > 1.2 else "🟢 Normal"
        st.metric("Creatinine", f"{creatinine_val} mg/dL", status)
    
    with lab_col4:
        cholesterol_val = current_data.get('Cholesterol', 0)
        status = "🔴 High" if cholesterol_val > 200 else "🟢 Normal"
        st.metric("Cholesterol", f"{cholesterol_val} mg/dL", status)
    
    # Genetic Insights
    st.subheader("🧬 Genetic Risk Factors")
    
    active_genes = [gene for gene, is_active in st.session_state.genetic_data.items() if is_active]
    if active_genes:
        gene_names = [gene.replace("gene_", "") for gene in active_genes]
        st.info(f"**Known genetic markers:** {', '.join(gene_names)}")
        
        # Show associated conditions
        for gene in gene_names:
            for condition, genes in GENE_ASSOCIATIONS.items():
                if gene in genes:
                    st.write(f"- **{gene}** → Associated with {condition}")
    else:
        st.info("No known genetic risk factors reported")
    
    # Recommendations
    st.subheader("💡 Personalized Recommendations")
    
    recommendations = []
    
    if diabetes_risk >= 4:
        recommendations.extend([
            "🩺 **Monitor HbA1c every 3-6 months**",
            "🥗 **Consult nutritionist for diabetic diet plan**",
            "🏃 **Regular exercise (30 mins, 5 days/week)**"
        ])
    
    if liver_risk >= 4:
        recommendations.extend([
            "🔍 **Consider liver ultrasound**",
            "🚫 **Reduce alcohol consumption**",
            "💊 **Avoid hepatotoxic medications**"
        ])
    
    if bmi >= 25:
        recommendations.append("⚖️ **Weight management program recommended**")
    
    if smoking_history:
        recommendations.append("🚭 **Smoking cessation program strongly recommended**")
    
    if not recommendations:
        recommendations.append("🎉 **Continue with routine health monitoring**")
    
    for rec in recommendations:
        st.write(rec)
    
    # Export Data
    st.subheader("📤 Export Health Report")
    
    if st.button("Generate Comprehensive Report"):
        report_content = f"""
        DIGITAL TWIN HEALTH REPORT
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        
        PATIENT PROFILE:
        Name: {patient_name}
        Age: {age}, Gender: {gender}, BMI: {bmi}
        
        RISK ASSESSMENT:
        Diabetes: {get_risk_label(diabetes_risk)} (Score: {diabetes_risk}/10)
        Liver Disease: {get_risk_label(liver_risk)} (Score: {liver_risk}/10)
        
        ACTIVE SYMPTOMS:
        {', '.join(active_symptoms) if active_symptoms else 'None'}
        
        RECOMMENDATIONS:
        {chr(10).join(recommendations)}
        """
        
        st.download_button(
            label="⬇️ Download Health Report",
            data=report_content,
            file_name=f"health_report_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )

else:
    st.info("👆 Fill in your health information and click 'Save Health Data' to see your analysis")

# ----------------------------
# FOOTER
# ----------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center'><em>Digital Twin Health Analyzer • Manual Data Input Version • Consult healthcare professionals for medical decisions</em></div>",
    unsafe_allow_html=True
)
