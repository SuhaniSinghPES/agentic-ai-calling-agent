from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


KNOWLEDGE_FILE = Path("data/knowledge.txt")


def load_knowledge():

    text = KNOWLEDGE_FILE.read_text(
        encoding="utf-8"
    )

    return [
        chunk.strip()
        for chunk in text.split("\n\n")
        if chunk.strip()
    ]


def search_knowledge(query, top_k=3):

    documents = load_knowledge()

    if not documents:
        return "No knowledge base information is available."

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    vectors = vectorizer.fit_transform(
        documents + [query]
    )

    scores = cosine_similarity(
        vectors[-1],
        vectors[:-1]
    )[0]

    ranked_indices = scores.argsort()[::-1]

    results = []

    for index in ranked_indices[:top_k]:

        if scores[index] > 0:
            results.append(documents[index])

    if not results:
        return (
            "No relevant information was found "
            "in the company knowledge base."
        )

    return "\n\n".join(results)