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
# ENHANCED PDF TEXT EXTRACTION
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

# ----------------------------
# ENHANCED LAB VALUE EXTRACTION FOR YOUR PDF FORMAT
# ----------------------------
def extract_lab_values_advanced(text, tests):
    """Extract lab values using multiple pattern matching for Indian lab reports"""
    lab_data = {}
    
    # Enhanced patterns for common tests in Indian lab formats
    patterns = {
        'HbA1c': [
            r'HbA1c\s*([\d.]+)\s*%',
            r'HBA1C\s*([\d.]+)\s*%',
            r'HbA1c.*?([\d.]+)\s*%'
        ],
        'Glucose': [
            r'Glucose.*?Random\s*([\d.]+)',
            r'Glucose.*?([\d.]+)\s*mg/dL',
            r'Random Glucose\s*([\d.]+)',
            r'Glucose\s*-\s*Random\s*([\d.]+)'
        ],
        'Hb': [
            r'Hemoglobin\s*([\d.]+)',
            r'Hb\s*([\d.]+)',
            r'Hemoglobin.*?([\d.]+)\s*gm/dl'
        ],
        'WBC': [
            r'WBC/TLC\s*([\d.]+)',
            r'WBC\s*([\d.]+)',
            r'White Blood Cell.*?([\d.]+)'
        ],
        'Platelet': [
            r'Platelet Count\s*([\d.]+)',
            r'Platelet\s*([\d.]+)',
            r'PLT\s*([\d.]+)'
        ],
        'ALT': [
            r'SGPT - ALT\s*([\d.]+)',
            r'ALT\s*([\d.]+)',
            r'SGPT\s*([\d.]+)'
        ],
        'AST': [
            r'SGOT - AST\s*([\d.]+)',
            r'AST\s*([\d.]+)',
            r'SGOT\s*([\d.]+)'
        ],
        'Creatinine': [
            r'Creatinine\s*([\d.]+)',
            r'CREATININE\s*([\d.]+)'
        ],
        'Cholesterol': [
            r'Cholesterol\s*([\d.]+)',
            r'CHOLESTEROL\s*([\d.]+)'
        ],
        'ESR': [
            r'E\.S\.R\.\s*([\d.]+)',
            r'ESR\s*([\d.]+)',
            r'Erythrocyte Sedimentation Rate\s*([\d.]+)'
        ],
        'Calcium': [
            r'Serum Calcium\s*([\d.]+)',
            r'Calcium\s*([\d.]+)'
        ],
        'Urea': [
            r'Urea\s*([\d.]+)',
            r'UREA\s*([\d.]+)'
        ],
        'Albumin': [
            r'Albumin\s*([\d.]+)',
            r'ALBUMIN\s*([\d.]+)'
        ],
        'Bilirubin': [
            r'Total Bilirubin\s*([\d.]+)',
            r'Bilirubin Total\s*([\d.]+)'
        ],
        'ALP': [
            r'Serum alkaline phosphatase - ALP\s*([\d.]+)',
            r'ALP\s*([\d.]+)',
            r'Alkaline Phosphatase\s*([\d.]+)'
        ]
    }
    
    # Clean the text - remove extra spaces and normalize
    text = re.sub(r'\s+', ' ', text)
    
    for test in tests:
        value_found = None
        
        # Try multiple patterns for known tests
        if test in patterns:
            for pattern in patterns[test]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value_found = match.group(1).replace(",", "").strip()
                    break
        
        # If no specific pattern found, try generic search
        if not value_found:
            # Look for test name followed by numbers
            generic_pattern = rf"{test}.*?([\d.]+)\s*(?:{r'%|mg/dL|U/L|mmol/L|gm/dL|10\^3/uL|10\^6/uL|fL|Pg'})"
            match = re.search(generic_pattern, text, re.IGNORECASE)
            if match:
                value_found = match.group(1).replace(",", "").strip()
        
        # Convert to float if possible
        if value_found:
            try:
                lab_data[test] = float(value_found)
            except ValueError:
                lab_data[test] = value_found
                st.warning(f"Could not convert {test} value '{value_found}' to number")
    
    # Extract date from text
    date_patterns = [
        r'Received On\s*:\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'Reported On\s*:\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                date_str = match.group(1)
                lab_data['Date'] = pd.to_datetime(date_str, format='%d/%m/%Y', errors='coerce')
                if pd.notna(lab_data['Date']):
                    break
            except:
                continue
    
    # Extract patient information
    name_match = re.search(r'Name\s*:\s*([A-Z\s]+)', text)
    if name_match:
        lab_data['Patient_Name'] = name_match.group(1).strip()
    
    age_match = re.search(r'Age\s*:\s*(\d+)', text)
    if age_match:
        lab_data['Patient_Age'] = age_match.group(1).strip()
    
    gender_match = re.search(r'Gender\s*/\s*Age\s*:\s*([A-Za-z]+)', text)
    if gender_match:
        lab_data['Patient_Gender'] = gender_match.group(1).strip()
    
    return lab_data

# ----------------------------
# DEBUG FUNCTION TO SEE EXTRACTED TEXT
# ----------------------------
def debug_pdf_extraction(file):
    """Show what text is actually being extracted from PDF"""
    text = extract_text_from_pdf(file)
    
    with st.expander("🔍 DEBUG: View Raw Extracted Text"):
        st.text_area("Raw PDF Text", text, height=300)
    
    return text

# ... (rest of your Streamlit app code remains the same)

# ----------------------------
# MODIFIED PDF PROCESSING SECTION
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
    
    # Add debug option
    debug_mode = st.checkbox("Enable Debug Mode (Show raw extracted text)")
    
    # Process files with progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_extracted_data = []
    successful_files = 0
    
    for i, file in enumerate(uploaded_files):
        status_text.text(f"Processing {file.name}... ({i+1}/{len(uploaded_files)})")
        
        try:
            if debug_mode:
                # Show debug information
                text = debug_pdf_extraction(file)
            else:
                text = extract_text_from_pdf(file)
            
            if text and len(text.strip()) > 0:
                # Extract lab values
                data = extract_lab_values_advanced(text, selected_tests)
                
                if debug_mode:
                    st.write(f"📊 Extracted data from {file.name}:")
                    st.json(data)
                
                if data:  # Only add if we extracted something
                    data['Filename'] = file.name
                    all_extracted_data.append(data)
                    successful_files += 1
                    st.success(f"✅ Successfully extracted data from {file.name}")
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
        
        # Display what was extracted
        st.subheader("🎯 Tests Successfully Extracted")
        extracted_tests = [col for col in df_all.columns if col not in ['Date', 'Filename', 'Patient_Name', 'Patient_Age', 'Patient_Gender']]
        st.write(f"Found {len(extracted_tests)} tests: {', '.join(extracted_tests)}")
        
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
            extracted_tests_count = len([col for col in df_all.columns if col not in ['Date', 'Filename', 'Days_Since_First', 'Patient_Name', 'Patient_Age', 'Patient_Gender']])
            col2.metric("Tests Extracted", extracted_tests_count)
            
            if 'Date' in df_all.columns and not df_all['Date'].isna().all():
                date_range = f"{df_all['Date'].min().strftime('%Y-%m-%d')} to {df_all['Date'].max().strftime('%Y-%m-%d')}"
            else:
                date_range = "N/A"
            col3.metric("Date Range", date_range)
            
            # Display data table
            st.dataframe(df_all, use_container_width=True)
            
            # Continue with analysis... (rest of your analysis code)
