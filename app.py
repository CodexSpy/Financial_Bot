import streamlit as st
import os
import shutil
from datetime import datetime
from utils.file_parser import load_pdf, load_xlsx
from utils.embeddings import create_embeddings, create_vector_store, load_vector_store, delete_vector_store
from utils.rag import create_rag_chain
from utils.bot import ask_bot
import time


UPLOAD_DIR = 'data/uploads' # temporary location to save current session user uploaded file

os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_icon='💸', page_title='FinanceBot-byMoin', layout='centered')
st.title('Finance Bot 💸')

# Initialize session states
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store_ready" not in st.session_state:
    st.session_state.vector_store_ready = False
if "chain" not in st.session_state:
    st.session_state.chain = None
if "processing" not in st.session_state:
    st.session_state.processing = False

# Reset Chat button
if st.button("Reset Chat"):
    st.session_state.messages = []
    st.session_state.vector_store_ready = False
    st.session_state.chain = None
    st.session_state.processing = False
    
    if 'uploaded_file' in st.session_state:
        del st.session_state['uploaded_file']
    
    if os.path.exists(UPLOAD_DIR):
        shutil.rmtree(UPLOAD_DIR)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    try:
        delete_vector_store("Finance_index")
    except:
        pass
    
    st.success("Chat reset successfully!")
    st.rerun()

uploaded_file = st.file_uploader('Upload PDF or Excel', type=['pdf', 'xls', 'xlsx'], key='uploaded_file')

if uploaded_file and not st.session_state.vector_store_ready and not st.session_state.processing:
    st.session_state.processing = True
    
    file_path = os.path.join(
        UPLOAD_DIR,
        f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"
    )
    
    with st.spinner('Processing document...'):
        # Save file temporarily for each session
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        time.sleep(2)
        
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext in ['.xls', '.xlsx']:
            documents = load_xlsx(file_path)
        elif ext == '.pdf':
            documents = load_pdf(file_path)
        else:
            st.error("Unsupported file type")
            st.session_state.processing = False
            st.stop()
        
        if documents:
            # st.write(f"Loaded {len(documents)} document chunks!") //uncomment this if you want debugging 
            
            embeddings = create_embeddings()
            create_vector_store(documents, embeddings, index_name="Finance_index")
            
            # Loading the vector store and creating the chain
            vector_store = load_vector_store(index_name="Finance_index", embeddings=embeddings)
            st.session_state.chain = create_rag_chain(vector_store)
            st.session_state.vector_store_ready = True
            st.session_state.processing = False
            st.success("Your Document processed successfully! You can now start chatting.")
        else:
            st.error("Could not load any documents from the file.")
            st.session_state.processing = False

# Our Main user-bot chat interface

if st.session_state.vector_store_ready:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
             st.markdown(msg["content"], unsafe_allow_html=True)
    
    if user_input := st.chat_input("Ask a question"):
        user_input_prefixed = "Please respond only in English and with proper spacing" + user_input # can be removed too but it ensures proper response
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.chat_message('assistant'):
     
            def stream_bot_response():
                response_tokens = []
                try:
                    for token in ask_bot(user_input_prefixed, stream=True):
                        response_tokens.append(token)
                        yield token
                    # Store the full response in session state after streaming
                    st.session_state.messages.append({"role": "assistant", "content": "".join(response_tokens)})
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    yield error_msg

            answer = stream_bot_response()  
            with st.spinner('Getting results...'):
             time.sleep(2)
             st.write_stream(answer)

else:
    st.info("Please upload a document to start chatting.")
