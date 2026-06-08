import hashlib
import os
import uuid
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.models import PointStruct

from core.embeddings import create_embeddings_batch
from services.vector_service import store_teacher_embeddings_batch
from repository.teacher_repository import TeacherRepository
from core.ingest_pdf_teacher import is_junk_text, extract_chapters_from_pages, detect_chapter_for_page

def calculate_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

class TeacherService:
    @staticmethod
    def get_teacher_manuals(teacher_id: int, conn):
        return TeacherRepository.list_manuals(teacher_id, conn)
        
    @staticmethod
    def get_teacher_worksheets(teacher_id: int, conn):
        return TeacherRepository.list_worksheets(teacher_id, conn)

    @staticmethod
    def process_and_ingest_manual(pdf_path: str, teacher_id: int, language: str, level: str, title: str, conn) -> dict:
        reader = PdfReader(pdf_path)
        pages_text = [page.extract_text() or "" for page in reader.pages]
        total_pages = len(pages_text)

        chapter_map = extract_chapters_from_pages(pages_text)
        splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)

        all_chunks = []
        for page_idx, page_text in enumerate(pages_text):
            page_num = page_idx + 1
            chunks = splitter.split_text(page_text)
            chapter = detect_chapter_for_page(page_num, chapter_map)
            for chunk in chunks:
                if not is_junk_text(chunk):
                    all_chunks.append((chunk, page_num, chapter))

        if not all_chunks:
            raise ValueError("Couldn't process any text from this textbook")

        filename = os.path.basename(pdf_path)
        
        manual_id = TeacherRepository.save_manual_metadata(
            teacher_id=teacher_id, filename=filename, title=title, 
            language=language, level=level, total_pages=total_pages, 
            total_chunks=len(all_chunks), chapters=list(chapter_map.values()), 
            conn=conn
        )

        texts = [t for t, _, _ in all_chunks]
        vectors = create_embeddings_batch(texts)

        points_buffer = []
        BATCH_SIZE = 100
        
        for (text, page_num, chapter), vector in zip(all_chunks, vectors):
            points_buffer.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vector.tolist(),
                payload={
                    "text": text, "manual_id": manual_id, "teacher_id": teacher_id,
                    "page": page_num, "chapter": chapter or "unknown",
                    "language": language.lower(), "level": level, "source": filename
                }
            ))
            
            if len(points_buffer) >= BATCH_SIZE:
                store_teacher_embeddings_batch(points_buffer)
                points_buffer = []

        if points_buffer:
            store_teacher_embeddings_batch(points_buffer)
            
        TeacherRepository.set_manual_as_active(manual_id, conn)

        return {
            "manual_id": manual_id,
            "total_pages": total_pages,
            "chapters_detected": list(chapter_map.values())
        }