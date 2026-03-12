import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.embeddings import create_embedding
from services.vector_service import search_similar

def test_manual_knowledge(query):
    print(f"\nAsking about: '{query}'")
    
    vector = create_embedding(query)
    
    results = search_similar(vector) # similarity search
    
    if not results:
        print("Did not find anything.")
    else:
        print(f"Found {len(results)} relevant fragments:")
        for i, res in enumerate(results):
            print(f"\n--- Fragment {i+1} (Score: {res.score:.2f}) ---")
            print(res.payload['text'][:300] + "...")

if __name__ == "__main__":
    # topics: gestures, communication, grammar
    test_manual_knowledge("holiday")