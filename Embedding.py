import pdfplumber
import numpy as np
from pymongo import MongoClient
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.vectorstores import Chroma
from langchain.schema import Document  # Import Document class
from langchain.chat_models import ChatOpenAI



from config import key1, openaikey, filePath

OPENAI_API_KEY = openaikey

file_path1 = filePath



# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# Function to chunk text for embedding
def chunk_text(text, chunk_size=500, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

# Initialize OpenAI Embeddings
embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

# Function to create embeddings for each chunk of text
def create_embeddings(chunks):
    # Convert chunks into Document objects (required for LangChain FAISS store)
    documents = [Document(page_content=chunk) for chunk in chunks]
    # Extract page_content from documents to pass to embed_documents()
    document_texts = [doc.page_content for doc in documents]
    embeddings_result = embeddings.embed_documents(document_texts)
    
    # Return the embeddings as a numpy array for storage
    return np.array(embeddings_result).astype("float32")

# Function to create FAISS vector store
def create_faiss_vector_store(file_path):
    # Extract text from the PDF
    text = extract_text_from_pdf(file_path)
    
    # Chunk the text
    chunks = chunk_text(text)
    
    # Create embeddings for each chunk
    chunk_embeddings = create_embeddings(chunks)
    
    # Insert the chunks and embeddings into MongoDB
    # insert_embeddings_to_mongodb(chunks, chunk_embeddings)
    
    return chunk_embeddings  # Optionally return embeddings for further use


docs = create_faiss_vector_store(file_path1)


# docs should be a string
docs = ["""{ "Queens Store":"Clothing (Aisle 3): [T-shirt,Jeans,Jacket,Sneakers,Hat,Dress,Socks,Gloves,Scarf,Sweater,Shorts,Belt,Coat,Sandals]"
,Electronics (Aisle 5): [cellphone,Laptop,Tablet,Headphones,Camera,Television,Smartwatch,Speaker,Drone,Gaming Console,Printer,Keyboard]"
,Food (Aisle 7): Apple,Banana,Orange,Bread,Milk,Cheese,Yogurt,Chicken"
,Furniture (Aisle 2): Chair,Desk,Sofa,Bed,Coffee Table,Wardrobe,Bookshelf,Dining Table,Nightstand,Dresser"
,Personal Care (Aisle 6): Shampoo,Soap,Toothpaste,Deodorant,Face Wash,Lotion",
{"Chatham":["Clothing (Aisle 1): [T-shirt,Jeans,Jacket,Sneakers,Hat,Dress,Socks,Gloves,Scarf,Sweater,Shorts,Belt,Coat,Sandals]"
 ,"Electronics (Aisle 4): [cellphone,Laptop,Tablet,Headphones,Camera,Television,Smartwatch,Speaker,Drone,Gaming Console,Printer,Keyboard]"
 ,"Food (Aisle 5): Apple,Banana,Orange,Bread,Milk,Cheese,Yogurt,Chicken"
 ,"Furniture (Aisle 3): Chair,Desk,Sofa,Bed,Coffee Table,Wardrobe,Bookshelf,Dining Table,Nightstand,Dresser"
 ,"Personal Care (Aisle 2): Shampoo,Soap,Toothpaste,Deodorant,Face Wash,Lotion"],}
}"""]



# Convert raw document texts to LangChain Document objects
documents = [Document(page_content=doc) for doc in docs]

embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

# Create Chroma vector store
vectorstore = Chroma.from_documents(documents, embeddings)

# Initialize the chat model with OpenAI
chat_model = ChatOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY)

# Set up a prompt template
prompt_template = PromptTemplate(
    template="Answer the question based on the following documents:\n\n{context}\n\nQuestion: {question}\nAnswer:",
    input_variables=["context", "question"]
)

# Initialize Retrieval-based Q&A chain
rag_chain = RetrievalQA.from_chain_type(
    llm=chat_model,
    retriever=vectorstore.as_retriever(),  # Use Chroma as retriever
    chain_type="stuff"  # "stuff" combines the documents as context
)

# Function to perform RAG and generate chatbot responses
def chatbot_response_rag(user_input):
    # Use the RAG chain to generate a response with document retrieval
    response = rag_chain.run({"query": user_input})
    return response


response = chatbot_response_rag("where is Apple in Queens?")
print("Chatbot:", response)




# handling mongodb

from pymongo import MongoClient
import numpy as np

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["vector_db"]  # Database name
collection = db["vectors"]  # Collection name

# Generate embeddings and store in MongoDB
for i, doc in enumerate(documents):
    vector = embeddings.embed_query(doc.page_content)  # Generate embedding
    document = {
        "id": i + 1,
        "text": doc.page_content,
        "embedding": vector
    }
    collection.insert_one(document)
print("Vector stored successfully!")




from sklearn.metrics.pairwise import cosine_similarity

# Query text
query_text = "Shoes and clothing items"

# Generate embedding for query
query_vector = np.array(embeddings.embed_query(query_text)).reshape(1, -1)

# Fetch all stored embeddings
stored_docs = list(collection.find({}, {"_id": 0, "embedding": 1, "text": 1}))

# Convert embeddings to numpy array
stored_vectors = np.array([doc["embedding"] for doc in stored_docs])

# Compute similarity
similarities = cosine_similarity(query_vector, stored_vectors)
most_similar_index = np.argmax(similarities)

print("Most similar document:", stored_docs[most_similar_index]["text"])


