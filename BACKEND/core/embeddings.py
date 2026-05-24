import os
from transformers import logging as hf_logging # type: ignore
from sentence_transformers import SentenceTransformer # type: ignore
from dotenv import load_dotenv

load_dotenv() 

hf_token = os.getenv("HF_TOKEN")
if hf_token:
    os.environ["HF_TOKEN"] = hf_token

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

hf_logging.set_verbosity_error()

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def create_embedding(text):
    return model.encode(text)

def create_embeddings_batch(texts: list, batch_size: int = 64):
    return model.encode(texts, batch_size=batch_size, show_progress_bar=False)