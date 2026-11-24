from app.nlp.preprocessing.pipeline import (
    PreprocessOptions,
    build_representations,
    get_stopwords,
    lemmatize,
    ngrams,
    normalize,
    oov_analysis,
    preprocessing_demo,
    remove_stopwords,
    stem,
    tokenize,
    vocabulary_stats,
)


def test_normalization_unicode_and_whitespace():
    assert normalize("  Machine Learning – “NLP”  ") == 'Machine Learning - "NLP"'
    assert normalize("ABC", lowercase=True) == "abc"


def test_tokenizer_keeps_technical_terms():
    tokens = tokenize("Skilled in C++, C#, Node.js, CI/CD and scikit-learn.")
    for t in ("C++", "C#", "Node.js", "CI/CD", "scikit-learn"):
        assert t in tokens


def test_stopword_removal_protects_technical_terms():
    stop = get_stopwords()
    out = remove_stopwords(["the", "c", "and", "go", "is", "python"], stop)
    assert out == ["c", "go", "python"]


def test_stemming_reduces_words_but_not_tech_tokens():
    out = stem(["developers", "building", "node.js", "c++"])
    assert out[0].startswith("develop")
    assert out[1] == "build"
    assert out[2:] == ["node.js", "c++"]


def test_lemmatization_or_reported_fallback():
    from app.nlp.preprocessing.pipeline import BackendInfo

    info = BackendInfo()
    out = lemmatize(["studies", "built"], info)
    if info.lemmatizer == "unavailable":
        assert out == ["studies", "built"]  # unchanged, and the limitation is reported
        assert info.notes
    else:
        assert out[0] == "study"


def test_ngrams():
    assert ngrams(["deep", "learning", "with", "pytorch"], 2) == ["deep learning", "learning with", "with pytorch"]
    assert ngrams(["a"], 2) == []


def test_vocabulary_and_oov():
    stats = vocabulary_stats(["a", "b", "a"])
    assert stats["unique_tokens"] == 2 and stats["total_tokens"] == 3
    oov = oov_analysis(["python", "blockchainz"], {"python"})
    assert oov["oov_tokens"] == ["blockchainz"]
    assert oov["mapped"] == ["python", "<UNK>"]


def test_separate_representations_keep_original():
    text = "Built REST APIs in Python."
    rep = build_representations(text, PreprocessOptions(do_lemmatize=False))
    assert rep.original == text
    assert "python" in rep.model_ready_tokens and "in" not in rep.model_ready_tokens


def test_demo_has_all_steps():
    demo = preprocessing_demo("The engineers were training models")
    names = [s["name"] for s in demo["steps"]]
    assert any("Stemming" in n for n in names) and any("Lemmatization" in n for n in names)
    assert demo["backend"]["tokenizer"] == "regex-tech-aware"
