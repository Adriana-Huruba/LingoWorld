import os

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType
from dotenv import load_dotenv

load_dotenv()

TEACHER_COLLECTION_NAME = "teacher_manual_chunks"

def init_teacher_collection():
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )

    existing = [c.name for c in client.get_collections().collections]
    if TEACHER_COLLECTION_NAME in existing:
        print(f"Collection '{TEACHER_COLLECTION_NAME}' already exists.")
        return

    client.create_collection(
        collection_name=TEACHER_COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print(f"Created collection '{TEACHER_COLLECTION_NAME}'.")

    for field, schema in [
        ("manual_id", PayloadSchemaType.INTEGER),
        ("teacher_id", PayloadSchemaType.INTEGER),
        ("page", PayloadSchemaType.INTEGER),
        ("chapter", PayloadSchemaType.KEYWORD),
    ]:
        client.create_payload_index(
            collection_name=TEACHER_COLLECTION_NAME,
            field_name=field,
            field_schema=schema,
        )
    print("Payload indexes created.")


if __name__ == "__main__":
    init_teacher_collection()