from pipeline1 import setup_llm, get_sql_response
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.memory import ConversationSummaryBufferMemory
import os
from dotenv import load_dotenv
import logging
from litellm.integrations.opik.opik import OpikLogger
import litellm
import opik
from opik import track
from opik.opik_context import get_current_span_data
from opik import opik_context
from opik.integrations.langchain import OpikTracer

# OPIK CONFIGURATION
os.environ["OPIK_API_KEY"] = os.getenv("OPIK_API_KEY")
os.environ["OPIK_WORKSPACE"] = "yaane-tech"
opik.configure(use_local=False)
opik_logger = OpikLogger()
litellm.callbacks = [opik_logger]

# RAG PIPELINE
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
DB_FAISS_PATH = 'vectorstore/db_faiss'

def setup_vector_db(response_tuple, db_path):
    df, sql_query = response_tuple
    df_text = df.to_string()
    document_content = f"""
    SQL Query:
    {sql_query}
    
    Query Results:
    {df_text}
    """
    documents = [{"page_content": document_content, "metadata": {}}]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    doc = text_splitter.create_documents([document_content])
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    db = FAISS.from_documents(doc, embeddings)
    db.save_local(db_path)
    return db

def llm_response(input, db_path, memory):
    opik_tracer = OpikTracer()
    llm = ChatGroq(
        model="deepseek-r1-distill-llama-70b",
        temperature=0.4,
        callbacks=[opik_tracer],
    )
    
    prompt = ChatPromptTemplate.from_template(
        """
        You will be given a question which is based on the DB and the answer for that question will be present in the context.
        Answer the question based on the context and previous conversation history.
        Return only in natural language format. Provide it in a structured format . Use tables if necessary. 
        Also check the previous conversation history provided once to check if the input is actaully a follow up question from the user's previous history and then answer. 
        
        Previous conversation history:
        {history}
        
        <context>
        {context}
        </context>
        
        Question: {input}
        """
    )
    
    doc_chain = create_stuff_documents_chain(llm, prompt)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    db = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever()
    retriever_chain = create_retrieval_chain(retriever, doc_chain)
    

    memory_vars = memory.load_memory_variables({})
    
    final_response = retriever_chain.invoke({
        "input": input,
        "history": memory_vars.get("history", "")
    },
    callbacks=[opik_tracer])
    
    # Save the interaction to memory
    memory.save_context({"input": input}, {"output": final_response["answer"]})
    
    return final_response

@track(project_name='SQL-RAG-ChatBot')
def get_final_response(input, username):
    if not hasattr(get_final_response, 'memories'):
        get_final_response.memories = {}
    
    if username not in get_final_response.memories:
        get_final_response.memories[username] = ConversationSummaryBufferMemory(
            llm=ChatGroq(model="deepseek-r1-distill-llama-70b", temperature=0.1),
            max_token_limit=2000,
            return_messages=True
        )
    
    memory = get_final_response.memories[username]
    if memory is not None:
        print(memory)
    else:
        print(None)
    
    try:
        response = get_sql_response(input)
        print("DB DATA RESPONSE:")
        print("---------------------------------------------------------------")
        print(response)
    except Exception as e:
        logging.error("An Error Occurred in Pipeline 1: ", e)
    
    if response[0] is not None:
        try:
            db = setup_vector_db(response, DB_FAISS_PATH)
            if db is not None:
                print("Vector DB Created Successfully....")
                final_res = llm_response(input, DB_FAISS_PATH, memory)
                
                opik_context.update_current_trace(
                    tags=[username]
                )
                
                opik_context.update_current_span(
                    name="get_final_response",
                    metadata={
                        "username": username,
                        "input_length": len(input),
                        "response_type": "successful",
                        "db_created": True
                    },
                )
                
                print("RETRIEVER HAS RETRIEVED THE RESPONSE....")
                print("Process Over.....")
                print(final_res)
                return final_res
                
        except Exception as e:
            logging.error("An Error Occurred in Pipeline 2: %s", str(e))