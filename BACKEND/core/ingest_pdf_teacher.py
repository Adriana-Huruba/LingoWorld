import os
import re
import uuid

from typing import Optional
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.models import PointStruct

from core.embeddings import create_embeddings_batch
from services.vector_service import store_teacher_embeddings_batch
from dao.teacher_dao import TeacherDAO


CHAPTER_PATTERNS = [
    r"^\s*(chapter|unit|lesson)\s+(\d+|[IVXLC]+)[\s:.\-—]*(.{0,80})?$",
    r"^\s*(chapitre|unité|leçon)\s+(\d+|[IVXLC]+)[\s:.\-—]*(.{0,80})?$",
    r"^\s*(capítulo|unidad|lección|)\s+(\d+|[IVXLC]+)[\s:.\-—]*(.{0,80})?$",
    r"^\s*(capitolul|unitatea|lecția)\s+(\d+|[IVXLC]+)[\s:.\-—]*(.{0,80})?$",
]


def is_junk_text(text: str) -> bool:
    if len(text.strip()) < 50:
        return True
    
    if text.count('.') > 20 and len(re.findall(r'\d+', text)) > 5:
        return True
    
    junk_keywords = [
        "isbn", "copyright", "all rights reserved", "printed in", "acknowledgements", 
        "editura", "cuprins", "drepturi de autor", "redactare"
        "derechos reservados", "editorial", "impreso en", "diseño de cubierta", "agradecimientos",
        "sommaire", "éditeur", "tous droits réservés"
    ]
    if any(k in text.lower() for k in junk_keywords):
        return True
    return False


def extract_chapters_from_pages(pages_text: list[str]) -> dict[int, str]:
    chapter_map = {}
    for page_idx, page_text in enumerate(pages_text):
        lines = page_text.split('\n')[:15]
        for line in lines:
            matched = False
            for pattern in CHAPTER_PATTERNS:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    chapter_map[page_idx + 1] = line.strip()[:100]
                    matched = True
                    break
            if matched:
                break
    return chapter_map


def detect_chapter_for_page(page_num: int, chapter_map: dict[int, str]) -> Optional[str]:
    current_chapter = None
    for start_page in sorted(chapter_map.keys()):
        if start_page <= page_num:
            current_chapter = chapter_map[start_page]
        else:
            break
    return current_chapter


def run_teacher_ingestion(pdf_path, teacher_id, language, level, material_title, conn) -> dict:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File {pdf_path} not found.")

    source = os.path.basename(pdf_path)

    reader = PdfReader(pdf_path)
    pages_text = []
    for page in reader.pages:
        content = page.extract_text() or ""
        pages_text.append(content)

    total_pages = len(pages_text)
    print(f"Extracted {total_pages} pages")

    # chapters
    chapter_map = extract_chapters_from_pages(pages_text)
    print(f"Detected {len(chapter_map)} chapters")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600, chunk_overlap=100,
        separators=["\n\n", "\n", ".", "?", "!", " "],
    )

    all_chunks_with_meta = []
    for page_idx, page_text in enumerate(pages_text):
        page_num = page_idx + 1
        page_chunks = splitter.split_text(page_text)
        chapter = detect_chapter_for_page(page_num, chapter_map)
        for chunk in page_chunks:
            if not is_junk_text(chunk):
                all_chunks_with_meta.append((chunk, page_num, chapter))

    print(f"Got {len(all_chunks_with_meta)} clean chunks")

    if not all_chunks_with_meta:
        raise ValueError("No usable content extracted from PDF")

    manual_id = TeacherDAO.insert_manual(
        teacher_id=teacher_id,
        filename=source,
        title=material_title,
        language=language.lower(),
        level=level,
        total_pages=total_pages,
        total_chunks=len(all_chunks_with_meta),
        chapters=list(chapter_map.values()),
        conn=conn,
    )

    texts = [t for t, _, _ in all_chunks_with_meta]
    vectors = create_embeddings_batch(texts)

    BATCH_SIZE = 100
    points_buffer = []
    for (text, page_num, chapter), vector in zip(all_chunks_with_meta, vectors):
        points_buffer.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector.tolist(),
            payload={
                "text": text,
                "manual_id": manual_id,
                "teacher_id": teacher_id,
                "page": page_num,
                "chapter": chapter or "unknown",
                "language": language.lower(),
                "level": level,
                "source": source,
            },
        ))
        if len(points_buffer) >= BATCH_SIZE:
            store_teacher_embeddings_batch(points_buffer)
            points_buffer = []

    if points_buffer:
        store_teacher_embeddings_batch(points_buffer)

    TeacherDAO.mark_manual_processed(manual_id, conn)

    print(f"Ingestion done for manual_id={manual_id}")
    return {
        "manual_id": manual_id,
        "total_pages": total_pages,
        "total_chunks": len(all_chunks_with_meta),
        "chapters_detected": list(chapter_map.values()),
    }