from app.services.similarity.detector import SimilarityDetector

def test_similarity_threshold_classification():
    # >= 0.95 -> duplicate
    assert SimilarityDetector.classify_similarity(0.98) == "duplicate"
    assert SimilarityDetector.classify_similarity(0.95) == "duplicate"
    
    # 0.85 - 0.95 -> highly_similar
    assert SimilarityDetector.classify_similarity(0.91) == "highly_similar"
    assert SimilarityDetector.classify_similarity(0.85) == "highly_similar"

    # 0.70 - 0.85 -> related
    assert SimilarityDetector.classify_similarity(0.78) == "related"
    assert SimilarityDetector.classify_similarity(0.70) == "related"

    # < 0.70 -> None (Don't show)
    assert SimilarityDetector.classify_similarity(0.69) is None
    assert SimilarityDetector.classify_similarity(0.40) is None
