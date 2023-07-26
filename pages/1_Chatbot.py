import streamlit as st
import os
import time
import pinecone
from langchain.vectorstores import Pinecone
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter


# Setting up Streamlit page configuration
st.set_page_config(
    layout="centered", 
    initial_sidebar_state="expanded"
)


# Getting the OpenAI API key from Streamlit Secrets
openai_api_key = st.secrets.secrets.OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = openai_api_key

# Getting the Pinecone API key and environment from Streamlit Secrets
PINECONE_API_KEY = st.secrets.secrets.PINECONE_API_KEY
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
PINECONE_ENV = st.secrets.secrets.PINECONE_ENV
os.environ["PINECONE_ENV"] = PINECONE_ENV
# Initialize Pinecone with API key and environment
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
param1 = True
@st.cache_data
def select_index(param1):
    #time.sleep(10)
    if param1:
        #st.sidebar.write("Existing Indexes:👇")
        #st.sidebar.write(pinecone.list_indexes())
        pinecone_index_list = pinecone.list_indexes()
        #pinecone_index = st.sidebar.selectbox(label="Select Index", options=pinecone.list_indexes())
        #pinecone_index = st.sidebar.text_input("Write Name of Index to load: ")
    return pinecone_index_list

# Set the text field for embeddings
text_field = "text"
# Create OpenAI embeddings
embeddings = OpenAIEmbeddings(model = 'text-embedding-ada-002')
MODEL_OPTIONS = ["gpt-3.5-turbo", "gpt-4"]
model_name = st.sidebar.selectbox(label="Select Model", options=MODEL_OPTIONS)

pinecone_index_list = select_index(param1)
pinecone_index = st.sidebar.selectbox(label="Select Index", options = pinecone_index_list )

@st.cache_resource
def ret(pinecone_index):
    if pinecone_index != "":
        # load a Pinecone index
        time.sleep(5)
        index = pinecone.Index(pinecone_index)
        db = Pinecone(index, embeddings.embed_query, text_field)
        #retriever = db.as_retriever()
    return db#retriever, db
    
def chat():
    # if pinecone_index != "":
    #     # load a Pinecone index
    #     time.sleep(5)
    #     index = pinecone.Index(pinecone_index)
    #     db = Pinecone(index, embeddings.embed_query, text_field)
    #     retriever = db.as_retriever()
    db = ret(pinecone_index)
    def conversational_chat(query):
        llm = ChatOpenAI(model=model_name)
        docs = db.max_marginal_relevance_search(query, k=2, fetch_k=10)#.similarity_search(query)
        qa = load_qa_chain(llm=llm, chain_type="stuff")
        # Run the query through the RetrievalQA model
        result = qa.run(input_documents=docs, question=query) #chain({"question": query, "chat_history": st.session_state['history']})
        #st.session_state['history'].append((query, result))#["answer"]))

        return result   #["answer"]


    # Set a default model
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = model_name

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Send a message"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content":prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            output = conversational_chat(prompt)
            full_response = ""
            for response in output:
                full_response += response
                message_placeholder.markdown(full_response + "|")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

if pinecone_index != "":
    chat()
    #st.sidebar.write(st.session_state.messages)
    con_check = st.sidebar.checkbox("Check to Upload Conversation to loaded Index")
    if con_check:
        text = []
        for item in st.session_state.messages:
            text.append(f"Role: {item['role']}, Content: {item['content']}\n")
        #st.sidebar.write(text)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.create_documents(text)
        st.sidebar.info('Initializing Conversation Uploading to DB...')
        time.sleep(11)
        # Upload documents to the Pinecone index
        vector_store = Pinecone.from_documents(docs, embeddings, index_name=pinecone_index)
        
        # Display success message
        st.sidebar.success("Conversation Uploaded Successfully!")
