import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if the API key is loaded correctly
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("API key not found in environment variables. Please check 'key.env'.")

# Configure the API key
genai.configure(api_key=GOOGLE_API_KEY)

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    prompt_template = """
    Instructions:
    You are an AI lawyer specializing in ICT and Digital Security law in Bangladesh. You are provided with the Information and Communication Technology Act, 2006 and the Digital-Security-Act-2018. Your task is to provide precise and actionable legal advice based on the user's specific concerns about ICT and DIgital security.

    Please:
    - Carefully analyze the provided context from the legal documents.
    - Offer tailored legal advice that directly addresses the user's concerns.
    - Ensure that your advice is compliant with the relevant laws and regulations.
    - If information is missing or unclear, make logical assumptions based on the context to provide the best possible legal recommendations.
    - Be concise but thorough, offering detailed steps when necessary to resolve the user's concerns.

    Context:\n{context}\n
    Question: \n{question}\n

    Legal Advice:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)

    chain = get_conversational_chain()

    response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)

    print(response)
    st.write("Reply: ", response["output_text"])

def main():
    st.set_page_config("Legal Advisor for ICT and Digital Security in Bangladesh")
    st.header("⚖️ Bangladesh ICT-Digital Security Legal Advisor")

    # Input field for user's concern
    Law = st.text_input("What concern you have in mind regarding ICT and Digital Security in Bangladesh?")

    if Law:
        user_question = f"{Law}. And Please give me guideline what will be best in this context. Give Precise instruction, Stating which law or rule it came from."
        user_input(user_question)

    with st.sidebar:
        st.title("Documents:")

        # Process the provided PDFs
        pdf_files = ["Digital-Security-Act-2018.pdf", "Information and Communication Technology Act, 2006.pdf"]
        raw_text = get_pdf_text([open(pdf, "rb") for pdf in pdf_files])
        text_chunks = get_text_chunks(raw_text)
        get_vector_store(text_chunks)

if __name__ == "__main__":
    main()
    