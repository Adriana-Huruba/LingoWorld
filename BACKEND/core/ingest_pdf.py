import time
import json
import sys
import os
import uuid

current_dir = os.path.dirname(os.path.abspath(__file__)) 
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

import google.generativeai as genai
from pypdf import PdfReader
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.vector_service import store_embeddings_batch
from core.embeddings import create_embedding
from qdrant_client.models import PointStruct

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SKILL_TYPES = ["grammar", "vocabulary", "reading", "writing", "pronunciation", "general"]
 
TOPIC_LIST = [
    "present_tense", "past_tense", "future_tense", "modal_verbs", "subjunctive",
    "conditionals", "passive_voice", "reported_speech", "relative_clauses",
    "nouns_gender", "articles", "adjectives", "adverbs", "prepositions",
    "pronouns", "conjunctions", "word_order",
    "greetings", "family", "numbers", "colors", "food", "travel", "work",
    "health", "environment", "technology", "culture", "emotions",
    "general"
]

def classify_chunks_batch(chunks, language, level) -> dict: # getting skill type + topic from llm
    previews = [f"[{i}] {c[:200]}" for i, c in enumerate(chunks)]
    combined = "\n---\n".join(previews)

    generation_config = {
        "temperature": 0.2,
        "response_mime_type": "application/json",
    }

    prompt = f"""
    You are a language curriculum expert. Classify each text chunk from a {language} textbook (level {level}).
    For EACH chunk identified by [index], return skill_type and topic.
    skill_type must be ONE of: {SKILL_TYPES}
    topic must be ONE of: {TOPIC_LIST}
  
    Chunks:
    {combined}
    
    Respond ONLY with a valid JSON array, no explanation, no markdown, like this example:
    [
        {{"index": 0, "skill_type": "grammar", "topic": "present_tense"}},
        {{"index": 1, "skill_type": "vocabulary", "topic": "family"}}
    ]

    IMPORTANT: The text is in {language}, but you must classify it using the English labels provided.
    """
 
    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash', generation_config=generation_config)
        response = model.generate_content(prompt)
        results = json.loads(response.text)

        classified = {}
        for r in results:
            idx = r.get("index", -1)
            skill_type = r.get("skill_type", "general")
            topic = r.get("topic", "general")

            if skill_type not in SKILL_TYPES:
                skill_type = "general" # default to general if not classified correctly
            if topic not in TOPIC_LIST:
                topic = "general"

            classified[idx] = {"skill_type": skill_type, "topic": topic}
        return [classified.get(i, {"skill_type": "general", "topic": "general"})
                for i in range(len(chunks))]
    except Exception as e: # if it doesnt work for any reason, fallback to general
        print(f"  [batch classify] Fallback — {e}")
        return [{"skill_type": "general", "topic": "general"}] * len(chunks) 

def run_ingestion(pdf_path, language, level, uploaded_by_user=None):
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

    source = os.path.basename(pdf_path)

    # classify - skill type + topic
    BATCH_CLASSIFY_SIZE = 20
    all_classifications = []

    print("Classifying chunks with LLM...")
    for i in range(0, len(chunks), BATCH_CLASSIFY_SIZE):
        time.sleep(2)
        batch = chunks[i : i + BATCH_CLASSIFY_SIZE]
        print(f"Classifying batch {i//BATCH_CLASSIFY_SIZE + 1}...")
        batch_results = classify_chunks_batch(batch, language, level)
        all_classifications.extend(batch_results)

    # batching for speed
    BATCH_SIZE = 50 
    all_points = []
    
    print("Creating embeddings and storing in Qdrant...")
    for i, (chunk, classifications) in enumerate(zip(chunks, all_classifications)): # for each chunk, create embedding and store in qdrant
        vector = create_embedding(chunk)
        
        all_points.append(PointStruct( # meta data
            id=str(uuid.uuid4()),
            vector=vector.tolist(),
            payload={
                "text": chunk,
                "language": language,
                "level": level,
                "skill_type": classifications["skill_type"],
                "topic": classifications["topic"],
                "source": source,
                "chunk_index": i,
                "uploaded_by_user": uploaded_by_user
            }
        ))
        
        if len(all_points) >= BATCH_SIZE:
            store_embeddings_batch(all_points)
            all_points = []
            print(f"Saved {i+1}/{len(chunks)} chunks...")

    if all_points: # rest of the points
        store_embeddings_batch(all_points)
    
    print("\nIngestion completed")