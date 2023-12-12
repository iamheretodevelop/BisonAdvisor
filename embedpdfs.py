import os
import re
import pdfplumber
import openai
import pinecone
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
load_dotenv()
PINECONE_API = os.environ['PINECONE_API_KEY']

# Initialize OpenAI
openai.api_key = os.environ['OPENAI_API_KEY']
client = OpenAI()
MODEL = "ada"
model = SentenceTransformer('all-MiniLM-L6-v2')


# Initialize Pinecone
pinecone.init(api_key=PINECONE_API, environment='gcp-starter')

# Define the index name
index_name = "course-info"

# Create the index if it doesn't exist
if index_name not in pinecone.list_indexes():
    pinecone.create_index(index_name, dimension=384)

# Instantiate the index
index = pinecone.Index(index_name)

# Define a function to preprocess text
def preprocess_text(text):
    # Replace consecutive spaces, newlines and tabs
    text = re.sub(r'\s+', ' ', text)
    return text

def process_pdf(file_path):
    # create a loader
    loader = PyPDFLoader(file_path)
    # load your data
    data = loader.load()
    # Split your data up into smaller documents with Chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    documents = text_splitter.split_documents(data)
    # Convert Document objects into strings
    texts = [str(doc) for doc in documents]
    return texts

# Define a function to create embeddings
def create_embeddings(texts):
    embeddings_list = model.encode(texts).tolist()
    # print(len(embeddings_list[0]))
    return embeddings_list

# Define a function to upsert embeddings to Pinecone
def upsert_embeddings_to_pinecone(index, embeddings, ids, text):
    index.upsert(vectors=[(id, embedding, {"text": text}) for id, embedding, text in zip(ids, embeddings,text)])

# Process a PDF and create embeddings
file_path = "./doc/CourseInfo.pdf"  # Replace with your actual file path
texts = process_pdf(file_path)

count = 1
for text in texts:
    # print(text, "\n")
    embeddings = create_embeddings(texts)
    print(f"{count}/{len(texts)}")

    count += 1
    upsert_embeddings_to_pinecone(index, embeddings, [str(i) for i in range(len(texts))], texts)


