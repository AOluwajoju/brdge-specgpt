import streamlit as st
import os
import clipboard
from docx import Document
from functions import upload_file
from functions import create_docx
from tempfile import NamedTemporaryFile
from pathlib import Path
from identt import client
from dotenv import load_dotenv

load_dotenv()


BASE_URL = os.getenv("IDEN_BASE_URL")
TOKEN = os.getenv("IDEN_USER_TOKEN")

spec_string = ""

client = client.Client(base_url=BASE_URL, token=TOKEN)

SYSTEM_PROMPT = f"""You are a helpful assistant that is expert in generate Technical Specification Documents for products, by strictly following the format/structure provided.
                    Structure/format:
                    - **Title**  
                    - **Summary**  
                    - **Unique Value Proposition**  
                    - **Core Features**  
                    - **Delivery Phases**  
                    - **Technical Specification**  
                    - **Innovation and Unique Selling Proposition**  
                    - **Potential Applications**  
                    - **Patentability**  
                """


model_id = client.get_model_id_by_name(name="SpecGPT")
index_uuid = client.get_index_uuid_by_name(name="specgpt_final")


#streamlit code

# State variable to track the button's disabled state
if "generate_button_disabled" not in st.session_state:
    st.session_state.generate_button_disabled = True
 
if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False
    
if "generating" not in st.session_state:
    st.session_state.generating = False 
    
if "generated" not in st.session_state:   
    st.session_state.generated = False  
    
if "text_inputted" not in st.session_state:
    st.session_state.text_inputted = False   
    
if "spec_string" not in st.session_state:
    st.session_state.spec_string = ""     


st.title("SpecGPT")
st.write("A Technical Specification Document Generator for Brdge. Based on Iden.")
st.divider()

if not st.session_state.generated:
    if not st.session_state.generating:
        if not st.session_state.text_inputted:
            uploaded_file = st.file_uploader("Upload a reference file")
            if uploaded_file is not None:
                st.session_state.file_uploaded = True
                st.session_state.generate_button_disabled = False
                # Show a spinner while the file is being analyzed
                with st.spinner("Analysing file..."):
                    try:
                        # Process the uploaded file
                        file_path = upload_file(uploaded_file)

                        if file_path:
                            st.success("File uploaded and analyzed successfully.")
                        else:
                            st.error("File analysis failed.")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

        if not st.session_state.file_uploaded and not st.session_state.text_inputted:
            col1, col2, col3 = st.columns([2, 1, 1])
            col2.write("OR")
        
        if not st.session_state.file_uploaded:
            txt = st.text_area("Write a detailed description of the product")
            if txt:
                st.session_state.generate_button_disabled = False
                st.session_state.text_inputted = True
                st.session_state.file_uploaded = False
                
    if st.button(
        "Generate Tech Spec", 
        icon="✨", 
        type="primary", 
        use_container_width=True, 
        disabled=st.session_state.generate_button_disabled,
        ):
        
        st.session_state.generating = True
        
        if st.session_state.file_uploaded:
                    
            file_objects = {}

            file_objects["reference_doc.txt"] = open("reference_doc.txt", "rb")
            file_objects["example_doc.txt"] = open("example_doc.txt", "rb")
        elif txt:
            
            with open("reference_doc.txt", "w", encoding='utf-8') as f:
                f.write("reference document\n" + txt)
            
            file_objects = {}
            file_objects["reference_doc.txt"] = open("reference_doc.txt", "rb")
            file_objects["example_doc.txt"] = open("example_doc.txt", "rb")    

        with st.spinner("Generating Technical Specification Document..."):
            try:
                index = client.index_files(file_objects=file_objects, index_uuid=index_uuid)
                
                response = client.chat(
                    model_id=model_id,
                    index_uuid=index_uuid,
                    query=f"""write the detailed and extensive technical specification for the reference doc, make sure to use all the information at your disposal. follow the following structure:
                Structure/format:
                                - **Title**  
                                - **Summary**  
                                - **Unique Value Proposition**  
                                - **Core Features**  
                                - **Delivery Phases**  
                                - **Technical Specification**  
                                - **Innovation and Unique Selling Proposition**  
                                - **Potential Applications**  
                                - **Patentability**""",
                )
                
                st.session_state.generated = True
                st.session_state.spec_string = response['response']
                st.rerun()
                st.write(spec_string)
            except Exception as e:
                st.error(f"An error occurred: {e}")    

else:
    st.success("Tech Spec generated! ⚡")
    spec_string = st.session_state.spec_string
    st.write(spec_string)
    # Create the .docx file and download
    docx_file = create_docx(spec_string)
    
    col1, col2 = st.columns(2)
    if col1.button("Copy to Clipboard", type="primary", icon="📋", use_container_width=True):
        clipboard.copy(spec_string)
        st.toast("Copied to clipboard!")
    
    
    col2.download_button(
        label="Download .docx",
        data=docx_file,
        file_name="Tech Spec.docx",
        use_container_width=True,
        type="primary",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    
    
    
    if st.button("Generate another Tech Spec", type="primary", icon="🔄", use_container_width=True):
        st.session_state.file_uploaded = False
        st.session_state.generating = False
        st.session_state.generated = False
        st.session_state.generate_button_disabled = True
        st.session_state.text_inputted = False
        st.session_state.spec_string = ""
        st.rerun()    
    
    # st.write(file.name)
    # suffix = Path(file.name).suffix
    
    # with NamedTemporaryFile(suffix=suffix) as temp_file:
    #     temp_file.write(file.getvalue())
    #     temp_file.seek(0)
    #     st.write(temp_file.name)

    #     st.write("File contents:")
        
    # st.write(upload_file(temp_file.name))