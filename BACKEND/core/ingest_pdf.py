import math
import time
import json
import sys
import os
import uuid
import re

current_dir = os.path.dirname(os.path.abspath(__file__)) 
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from pypdf import PdfReader
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.vector_service import store_embeddings_batch
from core.embeddings import create_embeddings_batch
from qdrant_client.models import PointStruct
from groq import Groq

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def is_junk_text(text: str) -> bool:
    if len(text.strip()) < 50:
        return True

    # for table of contents
    if text.count('.') > 20 and len(re.findall(r'\d+', text)) > 5:
        return True

    # key words that have to be avoided
    junk_keywords = ["isbn", "copyright", "all rights reserved", "printed in", "table of contents", "acknowledgements", "first published", "illustrations by",
                     "editura", "autor", "bibliografie", "drepturi de autor", "redactare", "cuprins",
                     "índice", "derechos reservados", "editorial", "impreso en", "diseño de cubierta", "agradecimientos",
                     "sommaire", "tous droits réservés", "achevé d'imprimer", "éditeur", "remerciements", "crédits photographiques"]
    if any(keyword in text.lower() for keyword in junk_keywords):
        return True

    return False


def classify_chunks_batch(chunks, language, level) -> list:
    previews = [f"[{i}] {c[:300]}" for i, c in enumerate(chunks)]
    combined = "\n---\n".join(previews)

    prompt = f"""
        You are a language curriculum expert for the {language} language. 
        
        Task: Analyze each text chunk from the textbook (level {level}) and classify it.

        GUARDRAILS (STRICT RULES):
        For EACH chunk identified by [index], return:
        1. "index": the chunk index (integer)
        2. "is_educational": **true** if the chunk contains language learning content (grammar explanation, vocabulary, dialogue, reading text, exercises). **false** if it's a table of contents, page numbers, copyright or any administrative text.
        3. "skill_type": **MUST** be a *LIST* containing one or both of: ["grammar", "vocabulary"].
        4. "topic": **MUST** be a *LIST* of the following predefined tags that apply to the text. Choose ONLY from:
            -"family", "jobs", "health", "food", "travel", "daily_routine", "clothes", "household_items", "animals", "emotions", "numbers", "time", "weather_and_nature", "school", "transportation", "technology_and_media", "hobbies_and_sports", "general_vocabulary"
            -"verb_conjugation", "verb_tenses", "prepositions", "nouns_and_gender", "pronouns", "articles", "adjectives", "conjunctions_and_linking", "subjunctive_and_imperative", "general_grammar"
        5. "chunk_level": **MUST** evaluate the linguistic complexity of the text. Return **ONE** string from: ["A1", "A2", "B1", "B2", "C1", "C2"]. 
            - Choose A1 or A2 if the text contains basic words used often (car, go, boy), short direct sentences (subject, verb and object) and basic tenses (Present, Simple Past, Near Future).
            - Choose B1 or B2 if the text contains intermediate vocabulary, compound and complex sentences with relative clauses, diverse tenses and introduction of the subjunctive, conditional or indirect speech.
            - Choose C1 or C2 if the text contains abstract words, idioms, technical vocabulary, long sentences with complex subordinate clauses, passive voice and highly advanced grammatical structures.
        Even though the textbook is level {level}, this specific chunk might be a simpler review or a complex reading text of another level.
        If you cannot evaluate it, use the {level} of the given textbook.
        
        6. DO NOT invent your own topics. If nothing specific fits, default to ["general_vocabulary"] or ["general_grammar"]

        Here are are some examples:
        Chunk: "Je vais au supermarché. Tu vas à la gare. Nous allons au cinéma..."
        Output: 
        {{"index": 0, "is_educational": true, "skill_type": ["grammar"], "topic": ["verb_conjugation"], "chunk_level": "A2"}}

        Chunk: "What I admired most about the city was its stunning architecture. Rarely have I witnessed such a mesmerizing sight."
        Output: 
        {{"index": 1, "is_educational": true, "skill_type": ["vocabulary", "grammar"], "topic": ["family", "jobs", "verb_tenses"], "chunk_level": "C1"}}

        Chunk: "Îmi place să mănânc fructe de pădure. De exemplu, îmi plac murele și afinele..."
        Output: 
        {{"index": 2, "is_educational": true, "skill_type": ["vocabulary", "grammar"], "topic": ["food", "articles"], "chunk_level": "A1"}}

        Chunk: "Maria tiene muchas animales! Ella tiene dos perros, un gato y una tortuga..."
        Output: 
        {{"index": 3, "is_educational": true, "skill_type": ["vocabulary"], "topic": ["animals"], "chunk_level": "B1"}}
        
        Chunk: "We would like to thank all the staff at Express Publishing who have contributed..." 
        Output: 
        {{"index": 4, "is_educational": false, "skill_type": [], "topic": [], "chunk_level": "{level}"}}
        Chunks:
        {combined}

        Respond ONLY with a valid JSON object containing a "results" array. 
        IMPORTANT: The text is in {language}, but you must use English labels for skill_type and topic.
    """

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)

        if isinstance(parsed, list):
            results = parsed
        elif "results" in parsed:
            results = parsed["results"]
        else:
            results = next((v for v in parsed.values() if isinstance(v, list)), [])

        classified = {}
        for r in results:
            idx = r.get("index", -1)

            raw_skill = r.get("skill_type", [])
            raw_topic = r.get("topic", [])

            if isinstance(raw_skill, list):
                skill_str = ",".join(s.strip().lower() for s in raw_skill if s) or "general_grammar"
            else:
                skill_str = str(raw_skill).strip().lower() or "general_grammar"

            if isinstance(raw_topic, list):
                topic_str = ",".join(t.strip().lower() for t in raw_topic if t) or "general_vocabulary"
            else:
                topic_str = str(raw_topic).strip().lower() or "general_vocabulary"

            classified[idx] = {
                "is_educational": bool(r.get("is_educational", True)),
                "skill_type": skill_str,
                "topic": topic_str,
                "chunk_level": r.get("chunk_level", level),
            }

        return [classified.get(i, {"is_educational": True, "skill_type": "general_grammar", "topic": "general_vocabulary", "chunk_level": level})
                for i in range(len(chunks))]

    except Exception as e:
        print(f"[batch classify] Groq error: {e}")
        return [{"is_educational": True, "skill_type": "reading", "topic": "general", "chunk_level": level}] * len(chunks)


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

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600, chunk_overlap=100,
        separators=["\n\n", "\n", ".", "?", "!", " "]
    )

    raw_chunks = splitter.split_text(text)
    chunks = [c for c in raw_chunks if not is_junk_text(c)]
    print(f"From {len(raw_chunks)} initial chunks, {len(chunks)} chunks remained after local cleanup")

    source = os.path.basename(pdf_path)

    BATCH_CLASSIFY_SIZE = 40 # 40 sau 20
    all_classifications = []

    print("Classifying chunks with LLM (Groq - Llama 3.1 8B)...")
    for i in range(0, len(chunks), BATCH_CLASSIFY_SIZE):
        batch = chunks[i: i + BATCH_CLASSIFY_SIZE]
        batch_num = i // BATCH_CLASSIFY_SIZE + 1
        total_batches = math.ceil(len(chunks) / BATCH_CLASSIFY_SIZE)
        print(f"Classifying batch {batch_num}/{total_batches}...")

        max_retries=3
        for attempt in range(max_retries):
            try:
                batch_results = classify_chunks_batch(batch, language, level)
                all_classifications.extend(batch_results)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 15 * (attempt + 1)
                    print(f"Groq limit hit. Waiting {wait_time} sec(try nr{attempt + 1})")
                    time.sleep(wait_time)
                else:
                    print("Total fail, fallback.")
                    all_classifications.extend([{"is_educational": True, "skill_type": "general_grammar", "topic": "general_vocabulary", "chunk_level": level}] * len(batch))

        # batch_results = classify_chunks_batch(batch, language, level)
        # all_classifications.extend(batch_results)
        if i + BATCH_CLASSIFY_SIZE < len(chunks):
            time.sleep(3.0)

    educational_chunks = [
        (chunk, cls)
        for chunk, cls in zip(chunks, all_classifications)
        if cls.get("is_educational", False)
    ]
    print(f"{len(educational_chunks)}/{len(chunks)} chunks are educational, creating embeddings...")

    texts_to_embed = [chunk for chunk, _ in educational_chunks]
    all_vectors = create_embeddings_batch(texts_to_embed)

    BATCH_SIZE = 50
    all_points = []

    for i, ((chunk, classifications), vector) in enumerate(zip(educational_chunks, all_vectors)):
        all_points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector.tolist(),
            payload={
                "text": chunk,
                "language": language,
                "level": level,
                "skill_type": classifications["skill_type"],
                "topic": classifications["topic"],
                "source": source,
                "uploaded_by_user": uploaded_by_user,
                "chunk_level": classifications.get("chunk_level", level)
            }
        ))

        if len(all_points) >= BATCH_SIZE:
            store_embeddings_batch(all_points)
            all_points = []
            print(f"Saved {i + 1}/{len(educational_chunks)} chunks in Qdrant...")

    if all_points:
        store_embeddings_batch(all_points)

    print(f"\nIngestion done:{len(educational_chunks)} chunks were stored from the total {len(chunks)} chunks")