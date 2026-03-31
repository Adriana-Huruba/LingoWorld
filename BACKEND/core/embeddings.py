import os
from sentence_transformers import SentenceTransformer # type: ignore
from dotenv import load_dotenv

load_dotenv() 

hf_token = os.getenv("HF_TOKEN")
if hf_token:
    os.environ["HF_TOKEN"] = hf_token
    # os.environ["HUGGINGFACEHUB_API_TOKEN"] = hf_token
    
model = SentenceTransformer("all-MiniLM-L6-v2")

def create_embedding(text):
    return model.encode(text)