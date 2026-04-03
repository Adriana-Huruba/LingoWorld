import sys
import os
import uuid
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.vector_service import store_embeddings_batch
from core.embeddings import create_embedding
from qdrant_client.models import PointStruct

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

def run_ingestion(pdf_path, category, language, level):
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} was not found.")
        return
    
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content: 
            text += content + "\n"
    
    # split
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    chunks = splitter.split_text(text)
    print(f"Split into {len(chunks)} chunks.")

    # batching for speed
    batch_size = 50 
    all_points = []
    
    print("Creating embeddings and storing in Qdrant...")
    for i, chunk in enumerate(chunks): # for each chunk, create embedding and store in qdrant
        vector = create_embedding(chunk)
        
        all_points.append(PointStruct( # meta data
            id=str(uuid.uuid4()),
            vector=vector.tolist(),
            payload={
                "text": chunk,
                "category": category,
                "language": language,
                "level": level,
                "source": os.path.basename(pdf_path)
            }
        ))
        
        if len(all_points) >= batch_size:
            store_embeddings_batch(all_points)
            all_points = []
            print(f"Saved {i+1}/{len(chunks)} chunks...")

    if all_points: # rest of the points
        store_embeddings_batch(all_points)
    
    print("\nIngestion completed")