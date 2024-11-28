import vertexai
from vertexai.preview.generative_models import GenerativeModel
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import streamlit_scrollable_textbox as stx
import pandas as pd
import polars as pl
import json
from pathlib import Path
import random
import string
from textwrap import fill
import PyPDF2
import base64
from utils.logging_utils import log_api_interaction, format_json

# Variables
PROJECT_ID = "your-project-id"
REGION = "your-region"

custom_css = """
<style>
    .dataframe th, .dataframe td {
        white-space: pre-wrap;
        vertical-align: top;
        font-size: 14px;
    }
    .dataframe .blank, .dataframe .nan {
        color: #ccc;
    }
</style>
"""

def extract_text_from_pdf(pdf_path):
    """Extract text content from PDF file with page tracking"""
    text_by_page = {}
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num, page in enumerate(reader.pages, 1):
            text_by_page[page_num] = page.extract_text()
    return text_by_page

def load_prompt_template():
    """Load the analysis prompt template with improved error handling"""
    try:
        prompt_path = Path("prompts/regulatory_analysis.md")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
            
        # Ensure the template has the required placeholders
        if "{document_text}" not in template:
            st.warning("Invalid prompt template - missing {document_text} placeholder")
            template = """
            Analyze the following documents and provide results in JSON format:
            
            {document_text}
            
            Format the response as a JSON object with a 'list_of_statements' array containing
            objects with: verbatim_text, risk_level, risk_reason, lower_risk_text_suggestion,
            and page_location fields.
            """
        
        return template
        
    except Exception as e:
        st.error(f"Failed to load prompt template: {str(e)}")
        return "{document_text}"

def analyze_document(text_dict, pdf_path, model):
    """Analyze document using both text and PDF content"""
    prompt_template = load_prompt_template()
    
    # Encode PDF as base64
    pdf_content = encode_pdf(pdf_path)
    
    # Format the document text with clear separation between contract and regulations
    formatted_text = "CONTRACT TO ANALYZE:\n"
    formatted_text += "\n".join([f"Page {page}: {content}" for page, content in text_dict["contract"].items()])
    formatted_text += "\n\nREGULATORY REFERENCES:\n"
    for doc_name, pages in text_dict["regulations"].items():
        formatted_text += f"\n{doc_name}:\n"
        formatted_text += "\n".join([f"Page {page}: {content}" for page, content in pages.items()])
    
    # Create input data for logging
    input_data = {
        "contract_name": Path(pdf_path).name,
        "regulatory_docs": list(text_dict["regulations"].keys()),
        "prompt_template": prompt_template
    }
    
    # Create the actual prompt
    prompt = prompt_template.replace("{document_text}", formatted_text)
    
    try:
        response = model.generate_content(prompt)
        log_api_interaction(input_data, response.text, [{"name": Path(pdf_path).name}])
        result = transform_analysis_result(response.text)
        
        if result["high"] or result["medium"]:
            return result
        else:
            clarification_prompt = """
            Please format your previous response as a valid JSON object with this structure:
            {
                "list_of_statements": [
                    {
                        "verbatim_text": "...",
                        "risk_level": "high|medium",
                        "risk_reason": "...",
                        "lower_risk_text_suggestion": "...",
                        "page_location": 1
                    }
                ]
            }
            """
            retry_response = model.generate_content(clarification_prompt)
            
            # Log the retry interaction
            log_api_interaction(
                {"type": "clarification", "prompt": clarification_prompt},
                retry_response.text
            )
            
            return transform_analysis_result(retry_response.text)
            
    except Exception as e:
        error_msg = str(e)
        log_api_interaction(input_data, f"Error: {error_msg}", [{"name": Path(pdf_path).name}])
        return {"high": [], "medium": [], "error": error_msg}

def transform_analysis_result(result):
    """Transform the analysis result from the VertexService to the desired format"""
    try:
        # Parse JSON string to dictionary - need to clean the response first
        cleaned_result = result.strip().replace("```json", "").replace("```", "").strip()
        result_dict = json.loads(cleaned_result)
        
        # Initialize output structure
        output = {
            "high": [],
            "medium": []
        }
        
        for item in result_dict.get("list_of_statements", []):
            try:
                risk_level = str(item.get("risk_level", "medium")).lower()
                if risk_level in ["high", "medium"]:
                    output[risk_level].append({
                        "text": str(item.get("verbatim_text", "")),
                        "suggestion": str(item.get("lower_risk_text_suggestion", "")),
                        "analysis": str(item.get("risk_reason", "")),
                        "page": int(item.get("page_location", 1)),
                        "source": "main"
                    })
            except (ValueError, TypeError) as e:
                st.warning(f"Skipped invalid statement: {str(e)}")
                continue
        
        return output
        
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON response: {str(e)}")
        return {"high": [], "medium": []}

def get_files_dict():
    """Get dictionary of files from data and docs folders"""
    data_folder = Path("data")
    docs_folder = Path("docs")
    
    data_files = list(data_folder.glob("*.pdf"))
    docs_files = list(docs_folder.glob("*.pdf"))
    
    files_dict = {
        "Main Document": {
            "primary_party": data_files[0].stem if data_files else "No document",
            "path": str(data_files[0]) if data_files else None,
        }
    }
    
    for doc in docs_files:
        files_dict[f"Reference - {doc.stem}"] = {
            "primary_party": doc.stem,
            "path": str(doc),
        }
    
    return files_dict

def encode_pdf(pdf_path):
    """Encode PDF file as base64 string"""
    try:
        with open(pdf_path, "rb") as pdf_file:
            return base64.b64encode(pdf_file.read()).decode('utf-8')
    except Exception as e:
        st.error(f"Failed to encode PDF: {str(e)}")
        return None

def main():
    vertexai.init(project=PROJECT_ID, location=REGION)

    st.set_page_config(page_title="Contract Reviewer", layout="wide")
    st.title("Contract Reviewer")

    files_dict = get_files_dict()
    
    # Main navigation tabs
    tab_main, tab_refs, tab_log = st.tabs([
        "Main Analysis", 
        "Reference Documents",
        "API Log"
    ])
    
    with tab_main:
        with st.container(border=True):
            col_a1, col_a2, col_a3 = st.columns([2, 4, 4], vertical_alignment="bottom")
            
            # Get reference documents (excluding the main document)
            ref_docs = [k for k in files_dict.keys() if k.startswith("Reference")]
            
            with col_a3:
                if ref_docs:
                    selected_ref = st.selectbox(
                        "Select Regulatory Reference",
                        ref_docs,
                        index=0,  # Always select first reference by default
                        key="regulatory_ref"
                    )
                else:
                    st.error("No regulatory reference documents available")
                    selected_ref = None
                
            with col_a1:
                button_submit = st.button(
                    "Run Regulatory Analysis", 
                    type="primary",
                    disabled=selected_ref is None
                )
            
            with col_a2:
                main_doc = list(files_dict.keys())[0]  # Get main document
                st.markdown(f"**Document to Analyze:** {main_doc}")

        if files_dict[main_doc]["path"]:
            with st.container(border=True):
                col_b1, col_b2 = st.columns([4, 6])
                
                with col_b1:
                    pdf_viewer(
                        input=files_dict[main_doc]["path"],
                        width=500,
                        height=600,
                    )
                
                with col_b2:
                    if button_submit:
                        st.subheader(f"Regulatory Analysis: {files_dict[main_doc]['primary_party']}")
                        
                        with st.spinner("Analyzing document..."):
                            # Extract text from contract
                            contract_text = extract_text_from_pdf(files_dict[main_doc]["path"])
                            
                            # Extract text from all regulatory documents
                            regulatory_texts = {}
                            for ref_doc in ref_docs:
                                regulatory_texts[ref_doc] = extract_text_from_pdf(files_dict[ref_doc]["path"])
                            
                            # Combine texts with clear structure
                            document_texts = {
                                "contract": contract_text,
                                "regulations": regulatory_texts
                            }
                            
                            # Initialize model and get analysis
                            model = GenerativeModel("gemini-1.5-pro")
                            analysis_dict = analyze_document(
                                document_texts,
                                files_dict[main_doc]["path"],
                                model
                            )
                            
                            if "error" not in analysis_dict:
                                # Convert to Polars DataFrame for better handling
                                high_risks = []
                                medium_risks = []
                                
                                if "high" in analysis_dict:
                                    high_risks = analysis_dict["high"]
                                if "medium" in analysis_dict:
                                    medium_risks = analysis_dict["medium"]
                                
                                df_high = pl.DataFrame(high_risks)
                                df_medium = pl.DataFrame(medium_risks)
                                
                                # Create tabs with count indicators
                                tab_high, tab_medium = st.tabs([
                                    f"High Risk ({len(df_high)})", 
                                    f"Medium Risk ({len(df_medium)})"
                                ])
                                
                                # Display high risks
                                with tab_high:
                                    if not df_high.is_empty():
                                        for page in sorted(df_high['page'].unique()):
                                            page_items = df_high.filter(pl.col('page') == page)
                                            with st.expander(f"Page {page}"):
                                                for row in page_items.iter_rows(named=True):
                                                    col1, col2 = st.columns([2, 2])
                                                    with col1:
                                                        st.markdown("**Contract Statement**")
                                                        stx.scrollableTextbox(
                                                            row['text'],
                                                            height=200,
                                                            key=f"high_text_{random.choices(string.ascii_uppercase + string.digits, k=4)}"
                                                        )
                                                    with col2:
                                                        st.markdown("**Suggested Version**")
                                                        stx.scrollableTextbox(
                                                            row['suggestion'],
                                                            height=200,
                                                            key=f"high_sugg_{random.choices(string.ascii_uppercase + string.digits, k=4)}"
                                                        )
                                                    st.markdown("**Risk Analysis**")
                                                    stx.scrollableTextbox(
                                                        row['analysis'],
                                                        height=200,
                                                        key=f"high_analysis_{random.choices(string.ascii_uppercase + string.digits, k=4)}"
                                                    )
                                                    st.divider()
                                
                                # Display medium risks
                                with tab_medium:
                                    if not df_medium.is_empty():
                                        for page in sorted(df_medium['page'].unique()):
                                            page_items = df_medium.filter(pl.col('page') == page)
                                            with st.expander(f"Page {page}"):
                                                for row in page_items.iter_rows(named=True):
                                                    col1, col2 = st.columns([2, 2])
                                                    with col1:
                                                        st.markdown("**Contract Statement**")
                                                        stx.scrollableTextbox(
                                                            row['text'],
                                                            height=200,
                                                            key=f"med_text_{random.choices(string.ascii_uppercase + string.digits, k=4)}"
                                                        )
                                                    with col2:
                                                        st.markdown("**Suggested Version**")
                                                        stx.scrollableTextbox(
                                                            row['suggestion'],
                                                            height=200,
                                                            key=f"med_sugg_{random.choices(string.ascii_uppercase + string.digits, k=4)}"
                                                        )
                                                    st.markdown("**Risk Analysis**")
                                                    stx.scrollableTextbox(
                                                        row['analysis'],
                                                        height=200,
                                                        key=f"med_analysis_{random.choices(string.ascii_uppercase + string.digits, k=4)}"
                                                    )
                                                    st.divider()
                            else:
                                st.error("Failed to parse analysis results")
                                st.code(analysis_dict["error"])

    with tab_refs:
        if ref_docs:
            col_r1, col_r2 = st.columns([4, 6])
            
            with col_r1:
                selected_ref_doc = st.selectbox(
                    "Select Reference Document",
                    ref_docs,
                    key="ref_doc_selector"
                )
                
                if selected_ref_doc and files_dict[selected_ref_doc]["path"]:
                    pdf_viewer(
                        input=files_dict[selected_ref_doc]["path"],
                        width=500,
                        height=600,
                    )
            
            with col_r2:
                if selected_ref_doc:
                    analyze_button = st.button("Analyze Reference Document", key="analyze_ref")
                    
                    if analyze_button:
                        with st.spinner("Analyzing reference document..."):
                            # Extract text from reference document
                            ref_text = "\n".join(
                                extract_text_from_pdf(
                                    files_dict[selected_ref_doc]["path"]
                                ).values()
                            )[:8000]
                            
                            # Load reference analysis prompt
                            with open("prompts/reference_analysis.md", "r", encoding="utf-8") as f:
                                ref_prompt = f.read()
                            
                            # Prepare and send prompt
                            ref_prompt = ref_prompt.replace("{document_text}", ref_text)
                            model = GenerativeModel("gemini-1.5-pro")
                            response = model.generate_content(ref_prompt)
                            
                            # Display formatted response
                            st.markdown(response.text)
        else:
            st.info("No reference documents available in the docs folder.")

    with tab_log:
        st.subheader("Vertex API Interaction Log")
        
        if 'api_logs' not in st.session_state:
            st.info("No API interactions logged yet.")
        else:
            for idx, log_entry in enumerate(st.session_state.api_logs):
                with st.expander(
                    f"[{log_entry['timestamp']}] API Call {len(st.session_state.api_logs) - idx}"
                ):
                    # Input section
                    st.markdown("### Input")
                    st.code(format_json(log_entry["input"]), language="json")
                    
                    # Files section
                    if log_entry["files"]:
                        st.markdown("### Files")
                        st.code(format_json(log_entry["files"]), language="json")
                    
                    # Response section
                    st.markdown("### Response")
                    st.code(log_entry["response"], language="json")

if __name__ == "__main__":
    main()
