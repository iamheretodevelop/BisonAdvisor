# Importing required packages
import streamlit as st
from openai import OpenAI
import pinecone
import os
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
# from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain

client = OpenAI()
import promptlayer

#configure the Streamlit page by setting the page title and displaying a title and sidebar with some information about the chatbot

st.set_page_config(page_title="Chat with BisonAdvisor")
st.title("Chat with Advisor")
st.sidebar.markdown("Developed by Hrishav Sapkota")
st.sidebar.markdown("Current Version: 0.0.1")
st.sidebar.markdown("Using GPT-4 API")
st.sidebar.markdown("Not optimised")
st.sidebar.markdown("May run out of OpenAI credits")

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
promptlayer.api_key = st.secrets["PROMPTLAYER"]

#Define the AI Model

MODEL = "gpt-3.5-turbo"

openai = promptlayer.openai

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = MODEL

#Define the prompt

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
            "role": "system",
            "content": f"""
            You are Bison Advisor an expert Historically Black College and University (HBCU) cultural historian.
            “historian” means an understanding of the African American experience and culture of HBCUs with well over twenty years historical knowledge.
            You use examples from wikipedia, britanica, uncf, tmcf, and various HBCU websites in your answers, to better illustrate your arguments.
            Your language should be for an 12 year old to understand.
            If you do not know the answer to a question, do not make information up - instead, ask a follow-up question in order to gain more context.
            Use a mix of popular culture and African American vernacular to create an accessible and engaging tone and response.
            Provide your answers in a form of a short paragraph no more than 100 words.
            Start by introducing yourself
            """
        })
    st.session_state.messages.append(   
        {
            "role": "user",
            "content": ""
        })
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": ""
        })

for message in st.session_state.messages:
    if message["role"] in ["user", "assistant"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything about HBCUs?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        query = st.session_state.messages[-1]["content"]
        message_placeholder = st.empty()
        full_response = ""
        print(query)
        # # similar_docs = get_similiar_docs()
        # for response in client.chat.completions.create(model=st.session_state["openai_model"],
        # messages=[
        #     {"role": m["role"], "content": m["content"]}
        #     for m in st.session_state.messages
        # ],
        # stream=True):
        #     full_response += response.choices[0].delta.content
        #     message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
