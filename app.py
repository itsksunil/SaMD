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

st.title("🧬 AI-Powered Digital Twin Health Analyzer")
st.markdown("""
**AI-driven genetic risk prediction** based on your symptoms, lab reports, and clinical profile for precise treatment planning.
""")

# ----------------------------
# AI GENE PREDICTION DATABASE
# ----------------------------
GENE_PREDICTION_ENGINE = {
    "Diabetes": {
        "high_risk_genes": ["TCF7L2", "PPARG", "KCNJ11", "FTO", "IRS1"],
        "moderate_risk_genes": ["ABCC8", "APOE", "LCAT", "IRS2"],
        "triggers": {
            "lab": {"HbA1c": (5.7, 6.4), "Glucose": (100, 126)},
            "symptoms": ["frequent_urination", "increased_thirst", "unexplained_weight_loss", "fatigue", "blurred_vision"],
            "clinical": ["obesity", "family_history", "sedentary_lifestyle", "hypertension"]
        }
    },
    "Pancreatic_Cancer": {
        "high_risk_genes": ["KRAS", "TP53", "CDKN2A", "SMAD4"],
        "moderate_risk_genes": ["BRCA2", "PALB2", "ATM"],
        "triggers": {
            "lab": {"ALT": (40, 100), "AST": (40, 100), "Bilirubin": (1.2, 3.0), "HbA1c": (6.5, 10.0)},
            "symptoms": ["abdominal_pain", "jaundice", "weight_loss", "loss_of_appetite", "back_pain", "new_onset_diabetes"],
            "clinical": ["smoking", "chronic_pancreatitis", "family_history", "obesity"]
        }
    },
    "Colorectal_Cancer": {
        "high_risk_genes": ["APC", "KRAS", "TP53", "MLH1", "MSH2"],
        "moderate_risk_genes": ["MSH6", "PMS2", "BMPR1A", "SMAD4"],
        "triggers": {
            "lab": {"Hb": (0, 12), "CEA": (5, 20), "Calcium": (10.5, 15.0)},
            "symptoms": ["blood_in_stool", "abdominal_pain", "change_in_bowel_habits", "unexplained_weight_loss", "fatigue"],
            "clinical": ["family_history", "inflammatory_bowel_disease", "sedentary_lifestyle", "red_meat_consumption"]
        }
    },
    "Cardiovascular_Disease": {
        "high_risk_genes": ["APOE", "PCSK9", "LDLR", "APOB"],
        "moderate_risk_genes": ["CETP", "LPL", "ACE", "AGTR1"],
        "triggers": {
            "lab": {"Cholesterol": (200, 240), "LDL": (130, 190), "HDL": (0, 40)},
            "symptoms": ["chest_pain", "shortness_of_breath", "palpitations", "swelling_in_legs"],
            "clinical": ["hypertension", "diabetes", "smoking", "obesity", "family_history"]
        }
    },
    "Liver_Disease": {
        "high_risk_genes": ["PNPLA3", "TM6SF2", "HFE", "SERPINA1"],
        "moderate_risk_genes": ["MBOAT7", "GCKR", "LYPLAL1"],
        "triggers": {
            "lab": {"ALT": (40, 150), "AST": (40, 150), "Bilirubin": (1.2, 5.0), "ALP": (120, 300)},
            "symptoms": ["jaundice", "abdominal_pain", "fatigue", "nausea", "swelling_in_legs"],
            "clinical": ["alcohol_consumption", "obesity", "diabetes", "family_history"]
        }
    }
}

# Treatment implications for genetic variants
GENE_TREATMENT_IMPLICATIONS = {
    "TCF7L2": {
        "implication": "Strongest genetic risk for Type 2 Diabetes",
        "treatment": "Metformin response may be reduced. Consider GLP-1 agonists early",
        "monitoring": "Annual HbA1c, consider continuous glucose monitoring"
    },
    "KRAS": {
        "implication": "Oncogene driver in pancreatic cancer",
        "treatment": "Targeted therapy with KRAS inhibitors if available",
        "monitoring": "Regular CA19-9, CT scans every 6 months"
    },
    "APC": {
        "implication": "Familial adenomatous polyposis risk",
        "treatment": "Consider prophylactic colectomy in high-risk cases",
        "monitoring": "Colonoscopy starting at age 10-12, annual thereafter"
    },
    "PCSK9": {
        "implication": "High LDL cholesterol, increased cardiovascular risk",
        "treatment": "PCSK9 inhibitors highly effective",
        "monitoring": "LDL levels every 3 months"
    },
    "HFE": {
        "implication": "Hereditary hemochromatosis risk",
        "treatment": "Therapeutic phlebotomy, iron chelation",
        "monitoring": "Ferritin, transferrin saturation every 3-6 months"
    }
}

# ----------------------------
# AI GENE PREDICTION FUNCTIONS
# ----------------------------
def predict_genetic_risks(df, symptoms, clinical_factors, age, gender):
    """AI engine to predict probable genetic risks based on patient data"""
    predicted_genes = {}
    risk_explanations = {}
    
    # Analyze for each condition
    for condition, data in GENE_PREDICTION_ENGINE.items():
        condition_score = 0
        trigger_details = []
        
        # Lab value analysis
        for test, (low_threshold, high_threshold) in data["triggers"]["lab"].items():
            if test in df.columns and not df[test].isna().all():
                latest_value = df[test].dropna().iloc[-1]
                if low_threshold <= latest_value <= high_threshold:
                    condition_score += 1
                    trigger_details.append(f"{test}: {latest_value} (borderline)")
                elif latest_value > high_threshold:
                    condition_score += 2
                    trigger_details.append(f"{test}: {latest_value} (elevated)")
        
        # Symptom analysis
        symptom_matches = [symptom for symptom in data["triggers"]["symptoms"] if symptoms.get(symptom, False)]
        condition_score += len(symptom_matches)
        if symptom_matches:
            trigger_details.append(f"Symptoms: {', '.join(symptom_matches)}")
        
        # Clinical factor analysis
        clinical_matches = [factor for factor in data["triggers"]["clinical"] if clinical_factors.get(factor, False)]
        condition_score += len(clinical_matches)
        if clinical_matches:
            trigger_details.append(f"Clinical: {', '.join(clinical_matches)}")
        
        # Age adjustment
        if condition in ["Colorectal_Cancer", "Cardiovascular_Disease"] and age > 50:
            condition_score += 1
            trigger_details.append("Age > 50")
        
        # Predict genes if condition score is significant
        if condition_score >= 3:
            # High confidence prediction
            predicted_genes.update({gene: "high" for gene in data["high_risk_genes"]})
            # Moderate confidence prediction
            predicted_genes.update({gene: "moderate" for gene in data["moderate_risk_genes"]})
            
            risk_explanations[condition] = {
                "score": condition_score,
                "triggers": trigger_details,
                "confidence": "high" if condition_score >= 5 else "moderate"
            }
    
    return predicted_genes, risk_explanations

def generate_genetic_insights(predicted_genes, risk_explanations):
    """Generate actionable insights from predicted genetic risks"""
    insights = []
    
    for condition, details in risk_explanations.items():
        condition_name = condition.replace("_", " ")
        confidence = details["confidence"]
        
        insight = {
            "condition": condition_name,
            "confidence": confidence,
            "triggers": details["triggers"],
            "recommended_genes": [],
            "actions": []
        }
        
        # Get high-risk genes for this condition
        high_risk_genes = GENE_PREDICTION_ENGINE[condition]["high_risk_genes"]
        for gene in high_risk_genes:
            if gene in predicted_genes:
                insight["recommended_genes"].append({
                    "gene": gene,
                    "risk_level": predicted_genes[gene],
                    "implication": GENE_TREATMENT_IMPLICATIONS.get(gene, {}).get("implication", "Genetic risk factor identified")
                })
        
        # Generate actions based on confidence
        if confidence == "high":
            insight["actions"].extend([
                f"Consider genetic testing for {condition_name}",
                "Consult genetic counselor",
                "Discuss with relevant specialist"
            ])
        else:
            insight["actions"].extend([
                f"Monitor for {condition_name} development",
                "Consider genetic testing if symptoms persist"
            ])
        
        insights.append(insight)
    
    return insights

# ----------------------------
# PDF PROCESSING FUNCTIONS (Same as before)
# ----------------------------
def extract_text_from_pdf(file):
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
        'Cholesterol': r'Cholesterol\s+([\d.]+)',
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
    
    date_match = re.search(r'Received On\s*:\s*(\d{2}/\d{2}/\d{4})', text)
    if date_match:
        try:
            lab_data['Date'] = pd.to_datetime(date_match.group(1), format='%d/%m/%Y')
        except:
            pass
    
    return lab_data

# ----------------------------
# STREAMLIT APP
# ----------------------------
with st.sidebar:
    st.header("⚙️ AI Analysis Settings")
    analysis_depth = st.select_slider(
        "Analysis Depth",
        options=["Basic", "Comprehensive", "Advanced Genetic"],
        value="Comprehensive"
    )

# Patient Profile
st.header("👤 Patient Profile & Symptoms")

col1, col2 = st.columns(2)
with col1:
    age = st.number_input("Age", 0, 120, 34)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    weight = st.number_input("Weight (kg)", 10, 200, 70)
    height = st.number_input("Height (cm)", 50, 250, 170)
    bmi = round(weight / ((height/100) ** 2), 2) if height > 0 else 0
    st.metric("BMI", f"{bmi}")

with col2:
    st.subheader("🏥 Clinical Factors")
    family_diabetes = st.checkbox("Family History: Diabetes")
    family_cancer = st.checkbox("Family History: Cancer")
    family_heart = st.checkbox("Family History: Heart Disease")
    smoking = st.checkbox("Smoking History")
    alcohol = st.selectbox("Alcohol Consumption", ["Never", "Occasional", "Regular"])
    activity = st.selectbox("Activity Level", ["Sedentary", "Light", "Moderate", "Active"])

# Symptoms
st.subheader("🤒 Current Symptoms")
symptom_col1, symptom_col2, symptom_col3 = st.columns(3)

symptoms = {}
with symptom_col1:
    symptoms['frequent_urination'] = st.checkbox("Frequent Urination")
    symptoms['increased_thirst'] = st.checkbox("Increased Thirst")
    symptoms['unexplained_weight_loss'] = st.checkbox("Unexplained Weight Loss")
    symptoms['fatigue'] = st.checkbox("Persistent Fatigue")
with symptom_col2:
    symptoms['abdominal_pain'] = st.checkbox("Abdominal Pain")
    symptoms['jaundice'] = st.checkbox("Jaundice/Yellow Skin")
    symptoms['blood_in_stool'] = st.checkbox("Blood in Stool")
    symptoms['change_in_bowel_habits'] = st.checkbox("Change in Bowel Habits")
with symptom_col3:
    symptoms['blurred_vision'] = st.checkbox("Blurred Vision")
    symptoms['chest_pain'] = st.checkbox("Chest Pain")
    symptoms['shortness_of_breath'] = st.checkbox("Shortness of Breath")
    symptoms['palpitations'] = st.checkbox("Palpitations")

# Clinical factors dictionary for AI analysis
clinical_factors = {
    "family_history": family_diabetes or family_cancer or family_heart,
    "obesity": bmi >= 30,
    "sedentary_lifestyle": activity in ["Sedentary", "Light"],
    "smoking": smoking,
    "alcohol_consumption": alcohol == "Regular",
    "hypertension": False,  # Could be added as input
    "chronic_pancreatitis": False,  # Could be added as input
    "inflammatory_bowel_disease": False  # Could be added as input
}

# PDF Upload
st.header("📁 Upload Lab Reports for AI Analysis")

uploaded_files = st.file_uploader(
    "Upload PDF lab reports for genetic risk prediction", 
    type="pdf", 
    accept_multiple_files=True
)

if 'df_all' not in st.session_state:
    st.session_state.df_all = pd.DataFrame()
if 'predicted_genes' not in st.session_state:
    st.session_state.predicted_genes = {}
if 'genetic_insights' not in st.session_state:
    st.session_state.genetic_insights = []

if uploaded_files:
    st.success(f"📄 {len(uploaded_files)} file(s) uploaded for AI analysis!")
    
    if st.button("🧠 Run AI Genetic Risk Analysis", type="primary"):
        all_extracted_data = []
        
        for file in uploaded_files:
            with st.spinner(f"Analyzing {file.name}..."):
                text = extract_text_from_pdf(file)
                if text:
                    data = extract_lab_values_simple(text, [
                        'HbA1c', 'Glucose', 'Hb', 'WBC', 'Platelet', 'ALT', 'AST', 
                        'ESR', 'Calcium', 'Creatinine', 'Bilirubin', 'Albumin', 'ALP', 'Cholesterol'
                    ])
                    if data:
                        data['Filename'] = file.name
                        all_extracted_data.append(data)
        
        if all_extracted_data:
            st.session_state.df_all = pd.DataFrame(all_extracted_data)
            if 'Date' in st.session_state.df_all.columns:
                st.session_state.df_all['Date'] = pd.to_datetime(
                    st.session_state.df_all['Date'], errors='coerce'
                )
                st.session_state.df_all = st.session_state.df_all.sort_values('Date').reset_index(drop=True)
            
            # Run AI Genetic Prediction
            with st.spinner("🤖 AI analyzing genetic risks..."):
                st.session_state.predicted_genes, risk_explanations = predict_genetic_risks(
                    st.session_state.df_all, symptoms, clinical_factors, age, gender
                )
                st.session_state.genetic_insights = generate_genetic_insights(
                    st.session_state.predicted_genes, risk_explanations
                )

# Display Results
if not st.session_state.df_all.empty and st.session_state.genetic_insights:
    df = st.session_state.df_all
    
    st.header("🎯 AI Genetic Risk Prediction Results")
    
    # Summary of predicted risks
    st.subheader("🧬 Predicted Genetic Risk Profile")
    
    for insight in st.session_state.genetic_insights:
        with st.expander(f"🔍 {insight['condition'].title()} - {insight['confidence'].upper()} Confidence", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔄 Triggering Factors:**")
                for trigger in insight['triggers']:
                    st.write(f"• {trigger}")
                
                st.markdown("**🧬 Recommended Genetic Testing:**")
                for gene_info in insight['recommended_genes']:
                    risk_color = "🔴" if gene_info['risk_level'] == 'high' else "🟠"
                    st.write(f"{risk_color} **{gene_info['gene']}** - {gene_info['implication']}")
            
            with col2:
                st.markdown("**💡 Recommended Actions:**")
                for action in insight['actions']:
                    st.write(f"• {action}")
                
                # Treatment implications for high-risk genes
                high_risk_genes = [g for g in insight['recommended_genes'] if g['risk_level'] == 'high']
                if high_risk_genes:
                    st.markdown("**🎯 Precision Medicine Implications:**")
                    for gene_info in high_risk_genes[:2]:  # Show top 2
                        treatment = GENE_TREATMENT_IMPLICATIONS.get(gene_info['gene'], {})
                        if treatment:
                            st.write(f"**{gene_info['gene']}:** {treatment.get('treatment', 'Consult specialist')}")
    
    # Detailed Gene Analysis
    st.subheader("📊 Comprehensive Gene-Disease Association")
    
    gene_disease_data = []
    for condition, data in GENE_PREDICTION_ENGINE.items():
        for gene in data["high_risk_genes"] + data["moderate_risk_genes"]:
            gene_disease_data.append({
                "Gene": gene,
                "Disease": condition.replace("_", " ").title(),
                "Risk_Level": "High" if gene in data["high_risk_genes"] else "Moderate",
                "Predicted": gene in st.session_state.predicted_genes
            })
    
    gene_df = pd.DataFrame(gene_disease_data)
    
    # Create interactive visualization
    fig = px.treemap(
        gene_df, 
        path=['Disease', 'Gene'], 
        color='Risk_Level',
        color_discrete_map={'High': 'red', 'Moderate': 'orange'},
        title="Gene-Disease Risk Associations"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Precision Treatment Recommendations
    st.header("💊 Precision Treatment Recommendations")
    
    treatment_col1, treatment_col2 = st.columns(2)
    
    with treatment_col1:
        st.markdown("**🎯 Targeted Therapies**")
        high_risk_predicted = [gene for gene, level in st.session_state.predicted_genes.items() if level == "high"]
        
        for gene in high_risk_predicted:
            treatment = GENE_TREATMENT_IMPLICATIONS.get(gene, {})
            if treatment:
                st.markdown(f"**{gene}**")
                st.write(f"*Implication:* {treatment['implication']}")
                st.write(f"*Treatment:* {treatment['treatment']}")
                st.write(f"*Monitoring:* {treatment['monitoring']}")
                st.markdown("---")
    
    with treatment_col2:
        st.markdown("**🛡️ Preventive Strategies**")
        
        preventive_measures = {
            "Diabetes": ["Lifestyle modification", "Early metformin", "GLP-1 agonists if high risk"],
            "Pancreatic_Cancer": ["Smoking cessation", "Healthy weight", "Regular screening if family history"],
            "Colorectal_Cancer": ["High-fiber diet", "Regular colonoscopy", "Aspirin prophylaxis if indicated"],
            "Cardiovascular_Disease": ["Statins early", "Blood pressure control", "Lifestyle changes"]
        }
        
        for condition in st.session_state.genetic_insights:
            condition_key = condition['condition'].replace(' ', '_')
            if condition_key in preventive_measures:
                st.markdown(f"**{condition['condition'].title()}**")
                for measure in preventive_measures[condition_key]:
                    st.write(f"• {measure}")
                st.markdown("---")
    
    # Export Genetic Report
    st.header("📤 Download Genetic Risk Report")
    
    if st.button("Generate Comprehensive Genetic Report"):
        report_content = f"""
        AI-POWERED GENETIC RISK ASSESSMENT REPORT
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        
        PATIENT PROFILE:
        Age: {age}, Gender: {gender}, BMI: {bmi}
        
        PREDICTED GENETIC RISKS:
        """
        
        for insight in st.session_state.genetic_insights:
            report_content += f"\n{insight['condition'].upper()}:\n"
            report_content += f"Confidence: {insight['confidence']}\n"
            report_content += "Recommended Genetic Testing:\n"
            for gene in insight['recommended_genes']:
                report_content += f"- {gene['gene']} ({gene['risk_level']} risk)\n"
        
        st.download_button(
            label="⬇️ Download Genetic Risk Report",
            data=report_content,
            file_name=f"genetic_risk_report_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )

elif not st.session_state.df_all.empty:
    st.info("👆 Click 'Run AI Genetic Risk Analysis' to generate genetic predictions")

else:
    st.info("👆 Upload lab reports and provide patient information for AI genetic risk analysis")

# ----------------------------
# FOOTER
# ----------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center'><em>AI-Powered Genetic Risk Prediction • For Research and Educational Purposes • Consult Healthcare Professionals for Medical Decisions</em></div>",
    unsafe_allow_html=True
)
