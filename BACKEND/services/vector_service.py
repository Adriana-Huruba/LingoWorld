from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct, VectorParams, Distance

client = QdrantClient("http://localhost:6333")
COLLECTION_NAME = "manual_chunks"

def ensure_collection_exists():
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        print(f"Collection '{COLLECTION_NAME}' does not exist. Creating it now...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            # size=384 for all-MiniLM-L6-v2
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        print("Collection created successfully.")

# for speed        
def store_embeddings_batch(points):
    ensure_collection_exists()
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

def store_embedding(id, vector, payload):
    ensure_collection_exists()

    point = PointStruct(
        id=id,
        vector=vector,
        payload=payload
    )
    
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[point]
    )


def search_similar(vector, topic=None):
    query_filter = None
    if topic:
        query_filter = Filter(
            must=[FieldCondition(key="category", match=MatchValue(value=topic))]
        )

    vector_list = vector.tolist() if hasattr(vector, "tolist") else vector  
    return client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector_list,
        query_filter=query_filter,
        limit=5
    ).points