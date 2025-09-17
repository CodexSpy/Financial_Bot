import os
from utils.rag import create_rag_chain
from utils.embeddings import create_embeddings, load_vector_store

RAG_CHAIN = None

# the main function for generating response
# implemented lazy loading, to curb FAISS errors

def ask_bot(user_input: str, stream: bool = False):

    global RAG_CHAIN
    
    if not os.path.exists("Finance_index"):
        error_msg = "Vector store not found. Please upload documents first."
        if stream:
            yield error_msg
            return
        else:
            return error_msg
    
    try:
        if RAG_CHAIN is None:
            embeddings = create_embeddings()
            vector_store = load_vector_store(index_name="Finance_index", embeddings=embeddings)
            RAG_CHAIN = create_rag_chain(vector_store)
        
        if stream:

            for chunk in RAG_CHAIN.stream({"question": user_input}):
                if 'answer' in chunk:
                    yield chunk['answer']
                elif 'result' in chunk:
                    yield chunk['result']
        else:
            response = RAG_CHAIN({"question": user_input})
            return response.get('answer', response.get('result', 'No response generated'))
            
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        if stream:
            yield error_msg
        else:
            return error_msg