import os
from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import shutil


load_dotenv()

def create_embeddings():
    cohere_api_key = os.getenv("COHERE_API_KEY") # replace with your choosen LLM API key
    if not cohere_api_key:
        raise ValueError("Cohere API key not found. Please Check weather it is saved in your .env or not")
    
    return CohereEmbeddings(
        cohere_api_key=cohere_api_key,
        model='embed-multilingual-v3.0', # embedding model by cohere you can also use huggingface and openAPI embedding models
        user_agent='FinancialBot/1.0'
    )


# creating and saving a vector store using Facebook Simialrity Search (FAISS) you can also use chroma DB

def create_vector_store(documents, embeddings, index_name="Finance_index"):
    
    if not documents:
     raise ValueError("No documents provided to create the vector store.")

    db = FAISS.from_documents(documents, embeddings)
    db.save_local(index_name) # creating a local .pickle file so that processing will be faster for the current session
    return db

def load_vector_store(index_name="Finance_index", embeddings=None):
    if not os.path.exists(index_name):
        raise FileNotFoundError(f"FAISS index '{index_name}' not found. Create it first using create_vector_store().")
     
    if embeddings is None:
        embeddings = create_embeddings()
    return FAISS.load_local(index_name, embeddings, allow_dangerous_deserialization=True)

# The below function will execute when user click 'ResetChat' button, it will delete our saved binary knowledgebase e.g. is our pickle file for the current session

def delete_vector_store(index_name):
    index_path = index_name
    if os.path.exists(index_path):
        def remove_readonly(func, path, excinfo):
            import stat
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(index_path, onexc=remove_readonly)
        print(f"Deleted vector store: {index_path}")
    else:
        print(f"Vector store not found: {index_path}")