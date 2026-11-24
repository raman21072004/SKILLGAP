"""Reusable text-preprocessing pipeline (syllabus: normalisation, tokenisation,
stop-word removal, stemming, lemmatisation, n-grams, vocabulary, OOV).

Design principle: *do not apply every step to every model.*

    original text  -> kept untouched for evidence highlighting
    normalised     -> unicode/whitespace cleaned (still human readable)
    tokens         -> technical-term-aware tokens ("c++", "node.js" survive)
    model-ready    -> lower-cased, stop words removed, lemmatised (for TF-IDF/BoW)
    skill entities -> produced separately by the skill extractor

Stemming is offered for demonstration but NOT used for skill matching because it
damages technical terms (e.g. "pandas" -> "panda", "kubernetes" -> "kubernet").
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass, field
from functools import lru_cache

# ---------------------------------------------------------------------------
# Tokenisation
# ---------------------------------------------------------------------------

# Keeps tokens such as c++, c#, node.js, ci/cd, scikit-learn, gpt-4 intact.
TECH_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[.\-_/][A-Za-z0-9]+)*(?:\+\+|#)?|[^\w\s]", re.UNICODE)

# Words that look like stop words but carry technical meaning in this domain.
PROTECTED_TERMS = {"c", "r", "go", "it", "ai", "ml", "dl", "ts", "js", "qa", "c++", "c#", "ci/cd", "s3", "ec2", "k8s"}

_FALLBACK_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for", "from", "has", "have", "he", "her",
    "his", "i", "in", "into", "is", "its", "me", "my", "of", "on", "or", "our", "she", "so", "than", "that",
    "the", "their", "them", "then", "there", "these", "they", "this", "those", "to", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "will", "with", "you", "your", "about", "above", "after",
    "again", "all", "am", "any", "because", "before", "being", "below", "between", "both", "can", "did", "do",
    "does", "doing", "down", "during", "each", "few", "further", "had", "having", "here", "how", "if", "just",
    "more", "most", "no", "nor", "not", "now", "off", "once", "only", "other", "out", "over", "own", "same",
    "should", "some", "such", "through", "too", "under", "until", "up", "very", "would", "also", "etc",
}


@dataclass
class BackendInfo:
    """Which library actually produced each result (shown in the UI for honesty)."""

    tokenizer: str = "regex-tech-aware"
    stopwords: str = "builtin"
    stemmer: str = "unavailable"
    lemmatizer: str = "unavailable"
    notes: list[str] = field(default_factory=list)


@lru_cache(maxsize=1)
def _nltk_stopwords() -> frozenset[str] | None:
    try:
        from nltk.corpus import stopwords

        return frozenset(stopwords.words("english"))
    except Exception:
        return None


@lru_cache(maxsize=1)
def _porter():
    try:
        from nltk.stem import PorterStemmer

        return PorterStemmer()
    except Exception:
        return None


@lru_cache(maxsize=1)
def _wordnet():
    try:
        from nltk.stem import WordNetLemmatizer

        lemmatizer = WordNetLemmatizer()
        lemmatizer.lemmatize("tests")  # raises LookupError if wordnet data is missing
        return lemmatizer
    except Exception:
        return None


@lru_cache(maxsize=1)
def _spacy_nlp():
    try:
        import spacy

        return spacy.load("en_core_web_sm", disable=["parser", "ner"])
    except Exception:
        return None


def get_stopwords(info: BackendInfo | None = None) -> set[str]:
    words = _nltk_stopwords()
    if words is not None:
        if info:
            info.stopwords = "nltk-english"
        return set(words) - PROTECTED_TERMS
    if info:
        info.stopwords = "builtin-fallback"
        info.notes.append("NLTK stop-word list not found; using built-in list. Run scripts/download_models.py.")
    return set(_FALLBACK_STOPWORDS) - PROTECTED_TERMS


def normalize(text: str, lowercase: bool = False) -> str:
    """Unicode NFKC normalisation, smart-quote replacement and whitespace collapse."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower() if lowercase else text


def tokenize(text: str) -> list[str]:
    """Technical-term-aware tokenizer (regex)."""
    return TECH_TOKEN_RE.findall(text)


def nltk_tokenize(text: str) -> list[str] | None:
    """NLTK Treebank-style tokenizer, shown in the Lab for comparison. None if unavailable."""
    try:
        from nltk.tokenize import word_tokenize

        return word_tokenize(text)
    except Exception:
        return None


def remove_punctuation(tokens: list[str]) -> list[str]:
    return [t for t in tokens if re.search(r"[A-Za-z0-9]", t)]


def remove_stopwords(tokens: list[str], stopwords: set[str]) -> list[str]:
    return [t for t in tokens if t.lower() not in stopwords or t.lower() in PROTECTED_TERMS]


class _SuffixStemmer:
    """Tiny fallback stemmer used only when NLTK is not installed (clearly labelled)."""

    SUFFIXES = ("ational", "ization", "fulness", "ousness", "iveness", "ations", "ation", "ments", "ment",
                "ings", "ing", "edly", "ed", "ies", "es", "ly", "s")

    def stem(self, word: str) -> str:
        for suf in self.SUFFIXES:
            if word.endswith(suf) and len(word) - len(suf) >= 3:
                return word[: -len(suf)]
        return word


def _stemmable(token: str) -> bool:
    """Only stem plain alphabetic words; keep 'node.js', 'c++', 'gpt-4' and protected terms intact."""
    return token.isalpha() and token.lower() not in PROTECTED_TERMS


def stem(tokens: list[str], info: BackendInfo | None = None) -> list[str]:
    stemmer = _porter()
    if stemmer is not None:
        if info:
            info.stemmer = "nltk-porter"
        return [stemmer.stem(t) if _stemmable(t) else t for t in tokens]
    if info:
        info.stemmer = "fallback-suffix-stripper"
        info.notes.append("NLTK not installed; using a simplified fallback stemmer.")
    fallback = _SuffixStemmer()
    return [fallback.stem(t.lower()) if _stemmable(t) else t for t in tokens]


def lemmatize(tokens: list[str], info: BackendInfo | None = None) -> list[str]:
    """Lemmatise with WordNet, else spaCy, else return tokens unchanged (labelled)."""
    wn = _wordnet()
    if wn is not None:
        if info:
            info.lemmatizer = "nltk-wordnet"
        out = []
        for t in tokens:
            if t.lower() in PROTECTED_TERMS or not t.isalpha():
                out.append(t)
            else:
                lemma = wn.lemmatize(t.lower(), pos="v")
                out.append(wn.lemmatize(lemma, pos="n"))
        return out
    nlp = _spacy_nlp()
    if nlp is not None:
        if info:
            info.lemmatizer = "spacy-en_core_web_sm"
        doc = nlp(" ".join(tokens))
        return [tok.lemma_.lower() if tok.text.lower() not in PROTECTED_TERMS else tok.text for tok in doc]
    if info:
        info.lemmatizer = "unavailable"
        info.notes.append(
            "No lemmatizer available (WordNet data / spaCy model missing). Tokens returned unchanged. "
            "Run: python backend/scripts/download_models.py"
        )
    return list(tokens)


def ngrams(tokens: list[str], n: int) -> list[str]:
    if n < 1:
        raise ValueError("n must be >= 1")
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def vocabulary_stats(tokens: list[str], top_k: int = 15) -> dict:
    counts = Counter(t.lower() for t in tokens)
    total = sum(counts.values())
    return {
        "total_tokens": total,
        "unique_tokens": len(counts),
        "type_token_ratio": round(len(counts) / total, 4) if total else 0.0,
        "most_common": counts.most_common(top_k),
    }


def oov_analysis(tokens: list[str], vocabulary: set[str], unk_token: str = "<UNK>") -> dict:
    """Out-of-vocabulary handling: which tokens a model's vocabulary does not know."""
    lowered = [t.lower() for t in tokens]
    oov = [t for t in lowered if t not in vocabulary]
    return {
        "vocabulary_size": len(vocabulary),
        "oov_tokens": sorted(set(oov)),
        "oov_rate": round(len(oov) / len(lowered), 4) if lowered else 0.0,
        "mapped": [t if t in vocabulary else unk_token for t in lowered],
    }


@dataclass
class PreprocessOptions:
    lowercase: bool = True
    remove_punct: bool = True
    remove_stop: bool = True
    do_stem: bool = False
    do_lemmatize: bool = True
    ngram_n: int = 2


@dataclass
class DocumentRepresentations:
    original: str
    normalized: str
    tokens: list[str]
    model_ready_tokens: list[str]
    model_ready_text: str
    backend: BackendInfo

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def build_representations(text: str, options: PreprocessOptions | None = None) -> DocumentRepresentations:
    """Produce the separate representations used by different parts of the system."""
    options = options or PreprocessOptions()
    info = BackendInfo()
    normalized = normalize(text)
    tokens = tokenize(normalized)
    work = [t.lower() for t in tokens] if options.lowercase else list(tokens)
    if options.remove_punct:
        work = remove_punctuation(work)
    if options.remove_stop:
        work = remove_stopwords(work, get_stopwords(info))
    if options.do_lemmatize:
        work = lemmatize(work, info)
    if options.do_stem:
        work = stem(work, info)
    return DocumentRepresentations(
        original=text,
        normalized=normalized,
        tokens=tokens,
        model_ready_tokens=work,
        model_ready_text=" ".join(work),
        backend=info,
    )


def preprocessing_demo(text: str, options: PreprocessOptions | None = None, vocabulary: set[str] | None = None) -> dict:
    """Step-by-step output for the NLP Lab (each transformation side by side)."""
    options = options or PreprocessOptions()
    info = BackendInfo()
    normalized = normalize(text, lowercase=options.lowercase)
    tokens = tokenize(normalized)
    nltk_tokens = nltk_tokenize(normalized)
    no_punct = remove_punctuation(tokens)
    stop = get_stopwords(info)
    no_stop = remove_stopwords(no_punct, stop)
    removed_stop = [t for t in no_punct if t not in no_stop]
    stems = stem(no_stop, info)
    lemmas = lemmatize(no_stop, info)
    base = lemmas if options.do_lemmatize else no_stop
    n = max(1, min(options.ngram_n, 4))
    result = {
        "original": text,
        "steps": [
            {"name": "Normalization", "description": "Unicode NFKC, smart quotes, whitespace" + (", lower-casing" if options.lowercase else ""), "output": normalized},
            {"name": "Tokenization (tech-aware regex)", "description": "Keeps C++, C#, Node.js and CI/CD as single tokens", "output": tokens},
            {"name": "Tokenization (NLTK word_tokenize)", "description": "Standard Treebank tokenizer for comparison" if nltk_tokens is not None else "NLTK punkt data not installed", "output": nltk_tokens if nltk_tokens is not None else []},
            {"name": "Punctuation removal", "description": "Drops tokens without letters or digits", "output": no_punct},
            {"name": "Stop-word removal", "description": f"Removed {len(removed_stop)} stop words; technical terms such as 'C', 'R', 'Go' are protected", "output": no_stop, "removed": removed_stop},
            {"name": "Stemming (Porter)", "description": "Rule-based suffix stripping; may produce non-words", "output": stems},
            {"name": "Lemmatization", "description": "Dictionary-based reduction to base form", "output": lemmas},
            {"name": f"{n}-grams", "description": f"Contiguous sequences of {n} tokens", "output": ngrams(base, n)},
        ],
        "vocabulary": vocabulary_stats(base),
        "backend": asdict(info),
    }
    if vocabulary is not None:
        result["oov"] = oov_analysis(base, vocabulary)
    return result
