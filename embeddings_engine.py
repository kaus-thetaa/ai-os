#imports
from sentence_transformers import SentenceTransformer
import numpy as np
import config

class EmbeddingError(Exception):
    pass


try:
    _embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
except Exception as error:

    _embedding_model = None
    _model_load_error = error
else:
    _model_load_error = None


def _ensure_model_loaded() -> None:

    if _embedding_model is None:
        raise EmbeddingError(
            f"The embedding model '{config.EMBEDDING_MODEL_NAME}' "
            f"failed to load. If this is the first time running "
            f"AI-OS, make sure you have an internet connection so "
            f"the model can be downloaded once. Original error: "
            f"{_model_load_error}"
        )


#convert a single piece of text into a vector
def embed_text(text: str) -> np.ndarray:

    _ensure_model_loaded()

    if not text or not text.strip():
        raise EmbeddingError("embed_text() was called with empty text.")

    try:
        vector = _embedding_model.encode(text.strip())
        return vector
    except Exception as error:
        raise EmbeddingError(
            f"Failed to generate embedding for the given text. "
            f"Original error: {error}"
        )


#embed a list of texts into a list of vectors
def embed_texts(texts: list[str]) -> np.ndarray:

    _ensure_model_loaded()

    if not texts:
        raise EmbeddingError("embed_texts() was called with an empty list.")

   
    for index, text in enumerate(texts):
        if not text or not text.strip():
            raise EmbeddingError(
                f"embed_texts() received an empty string at index "
                f"{index} in the input list. All texts must be "
                f"non-empty."
            )

    try:
        cleaned_texts = [text.strip() for text in texts]
        vectors = _embedding_model.encode(cleaned_texts)
        return vectors
    except Exception as error:
        raise EmbeddingError(
            f"Failed to generate embeddings for the given text batch. "
            f"Original error: {error}"
        )


#compare two pieces of text for semantic similarity, returning a score between -1.0 and 1.0
def calculate_similarity(text_a: str, text_b: str) -> float:

    vector_a = embed_text(text_a)
    vector_b = embed_text(text_b)


    dot_product = np.dot(vector_a, vector_b)
    magnitude_a = np.linalg.norm(vector_a)
    magnitude_b = np.linalg.norm(vector_b)

    if magnitude_a == 0 or magnitude_b == 0:
        raise EmbeddingError(
            "Could not calculate similarity — one of the text "
            "embeddings had zero magnitude, which should not happen "
            "with valid text input."
        )

    similarity_score = dot_product / (magnitude_a * magnitude_b)


    return float(similarity_score)


#test
if __name__ == "__main__":
    print("embeddings_engine.py self-test")
    print("-" * 50)

    print(f"Loading embedding model: {config.EMBEDDING_MODEL_NAME}")
    try:
        _ensure_model_loaded()
        print("OK — embedding model loaded successfully.")
    except EmbeddingError as error:
        print(f"FAILED — {error}")
        exit(1)

    print("-" * 50)
    print("Testing single text embedding...")
    sample_text = "This is a tax return document from 2023."
    vector = embed_text(sample_text)
    print(f"Input text: {sample_text!r}")
    print(f"Vector shape: {vector.shape}")
    print(f"First 5 values: {vector[:5]}")

    print("-" * 50)
    print("Testing batch text embedding...")
    sample_texts = [
        "This is a tax return document from 2023.",
        "A photo from my summer vacation in Italy.",
        "Meeting notes from the quarterly budget review.",
    ]
    vectors = embed_texts(sample_texts)
    print(f"Input: {len(sample_texts)} texts")
    print(f"Output shape: {vectors.shape}")

    print("-" * 50)
    print("Testing similarity calculation...")
    print("Comparing related texts (should score HIGH):")
    similar_score = calculate_similarity(
        "tax return document",
        "income tax filing paperwork",
    )
    print(f"  'tax return document' vs 'income tax filing paperwork'")
    print(f"  Similarity: {similar_score:.4f}")

    print()
    print("Comparing unrelated texts (should score LOW):")
    different_score = calculate_similarity(
        "tax return document",
        "photo from summer vacation",
    )
    print(f"  'tax return document' vs 'photo from summer vacation'")
    print(f"  Similarity: {different_score:.4f}")

    print("-" * 50)
    if similar_score > different_score:
        print("OK — related texts scored higher than unrelated texts,")
        print("confirming the embedding model correctly captures meaning.")
    else:
        print("WARNING — similarity scores did not behave as expected.")
        print("This may indicate a problem with the embedding model.")

    print("-" * 50)
    print("embeddings_engine.py self-test complete.")