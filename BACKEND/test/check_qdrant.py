"""Quick script to see what's actually indexed in Qdrant SE POATE STERGEEE."""
from qdrant_client import QdrantClient
from collections import Counter

client = QdrantClient(host="localhost", port=6333)

# Show ALL payload keys from first 5 points
points, _ = client.scroll(collection_name="manual_chunks", limit=5, with_payload=True, with_vectors=False)
print("=== SAMPLE PAYLOAD KEYS ===")
for p in points:
    print(p.payload.keys(), "→", {k: str(v)[:80] for k, v in p.payload.items()})

print("\n=== FULL STATS (500 samples) ===")
points, _ = client.scroll(collection_name="manual_chunks", limit=500, with_payload=True, with_vectors=False)
languages  = Counter()
levels     = Counter()
skill_types = Counter()
topics     = Counter()

for p in points:
    pl = p.payload or {}
    languages[pl.get("language", "?")] += 1
    levels[pl.get("level", "?")] += 1
    skill_types[pl.get("skill_type", "?")] += 1
    topics[pl.get("topic", pl.get("skill_type", "?"))] += 1

print("Languages:  ", dict(languages.most_common()))
print("Levels:     ", dict(levels.most_common()))
print("Skill types:", dict(skill_types.most_common(20)))
print("Topics:     ", dict(topics.most_common(20)))
