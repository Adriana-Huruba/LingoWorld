import os
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue, PayloadSchemaType, PointStruct, VectorParams, Distance, Range
from dotenv import load_dotenv

load_dotenv()
client = QdrantClient(
    url = os.getenv("QDRANT_URL"),
    api_key = os.getenv("QDRANT_API_KEY"),
    timeout=60
)

COLLECTION_NAME = "manual_chunks"

def ensure_collection_exists():
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        print(f"Collection '{COLLECTION_NAME}' does not exist. Creating it now...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        
        # index for faster filtering
        for field in ["language", "level", "skill_type", "topic", "source"]:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
            )

        # index for faster sorting
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="chunk_index",
            field_schema=PayloadSchemaType.INTEGER,
        )
        print("Collection created successfully.")
    
def store_embeddings_batch(points):
    ensure_collection_exists()
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

def store_embedding(id, vector, payload):
    ensure_collection_exists()
    point = PointStruct(id=id, vector=vector, payload=payload)
    client.upsert(collection_name=COLLECTION_NAME, points=[point])

def search_similar(vector, language, level=None, skill_type=None, topic=None, limit=5):
    query_filter = Filter(
        must=[
            FieldCondition(key="language", match=MatchValue(value=language)),
        ]
    )
    
    if level:
        query_filter.must.append(FieldCondition(key="level", match=MatchValue(value=level)))
        
    if skill_type and skill_type != "general":
        query_filter.must.append(FieldCondition(key="skill_type", match=MatchValue(value=skill_type)))
    
    if topic and topic != "general":
        query_filter.must.append(FieldCondition(key="topic", match=MatchValue(value=topic)))

    vector_list = vector.tolist() if hasattr(vector, "tolist") else vector  

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector_list,
        query_filter=query_filter,
        limit=limit
    ).points

    for i, hit in enumerate(results):
        print(f"Chunk {i+1}: Score = {hit.score:.4f} | Text: {hit.payload['text'][:50]}...")

    return results

def search_for_recommender(vector, language, levels=None, skill_type=None, topic=None, exclude_sources=None, limit=5): 
    query_filter = Filter(
        must=[
            FieldCondition(key="language", match=MatchValue(value=language)),
        ],
        must_not=[] 
    )

    if levels:
        query_filter.must.append(FieldCondition(key="level", match=MatchAny(any=levels)))

    if skill_type and skill_type != "general":
        query_filter.must.append(
            FieldCondition(key="skill_type", match=MatchValue(value=skill_type))
        )

    if topic and topic != "general":
        query_filter.must.append(
            FieldCondition(key="topic", match=MatchValue(value=topic))
        )
        
    if exclude_sources:
        query_filter.must_not.append(
            FieldCondition(key="source", match=MatchAny(any=exclude_sources))
        )

    vector_list = vector.tolist() if hasattr(vector, "tolist") else vector

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector_list,
        query_filter=query_filter,
        limit=limit
    ).points

    return results


# for teachers
TEACHER_COLLECTION_NAME = "teacher_manual_chunks"


def ensure_teacher_collection_exists():
    collections = client.get_collections().collections
    if not any(c.name == TEACHER_COLLECTION_NAME for c in collections):
        client.create_collection(
            collection_name=TEACHER_COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
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


def store_teacher_embeddings_batch(points: list[PointStruct]):
    ensure_teacher_collection_exists()
    client.upsert(collection_name=TEACHER_COLLECTION_NAME, points=points)


def search_teacher_material(vector, manual_id, page_range = None, chapter= None, limit= 20):
    ensure_teacher_collection_exists()
    must_conditions = [
        FieldCondition(key="manual_id", match=MatchValue(value=manual_id))
    ]

    if page_range:
        must_conditions.append(
            FieldCondition(key="page", range=Range(gte=page_range[0], lte=page_range[1]))
        )

    if chapter:
        must_conditions.append(
            FieldCondition(key="chapter", match=MatchValue(value=chapter))
        )

    vector_list = vector.tolist() if hasattr(vector, "tolist") else vector
    results = client.query_points(
        collection_name=TEACHER_COLLECTION_NAME,
        query=vector_list,
        query_filter=Filter(must=must_conditions),
        limit=limit,
    ).points

    for i, hit in enumerate(results):
        print(f"Chunk {i+1}: Score = {hit.score:.4f} | Text: {hit.payload['text'][:50]}...")
    return results


def delete_teacher_material_chunks(manual_id: int):
    ensure_teacher_collection_exists()
    client.delete(
        collection_name=TEACHER_COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="manual_id", match=MatchValue(value=manual_id))]
        ),
    )