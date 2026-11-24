"""Download optional model/data files ONCE (needs internet). The app works without
them, but with reduced functionality that is clearly reported in the UI.

    python scripts/download_models.py            # NLTK data + sentence-transformer + spaCy model
    python scripts/download_models.py --glove    # also pretrained GloVe (~66 MB)

Run from the backend/ folder.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def step(name: str, fn) -> bool:
    print(f"\n==> {name}")
    try:
        fn()
        print("    OK")
        return True
    except Exception as exc:  # report and continue with the next item
        print(f"    FAILED: {type(exc).__name__}: {exc}")
        return False


def nltk_data() -> None:
    import nltk

    for pkg in ("punkt", "punkt_tab", "stopwords", "wordnet", "omw-1.4"):
        nltk.download(pkg, quiet=True)


def sentence_model() -> None:
    from sentence_transformers import SentenceTransformer

    from app.nlp.config import get_nlp_config

    name = get_nlp_config().semantic_model_name
    model = SentenceTransformer(name, device="cpu")
    vec = model.encode(["Python developer"])
    print(f"    {name} loaded, embedding dimension = {vec.shape[1]}")


def spacy_model() -> None:
    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)


def glove() -> None:
    import gensim.downloader as api

    from app.nlp.config import data_dir
    from app.nlp.embeddings.word_vectors import GLOVE_NAME

    kv = api.load(GLOVE_NAME)
    out = data_dir() / "models" / f"{GLOVE_NAME}.kv"
    out.parent.mkdir(parents=True, exist_ok=True)
    kv.save(str(out))
    print(f"    saved {len(kv.index_to_key)} words x {kv.vector_size} dims to {out}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--glove", action="store_true", help="also download pretrained GloVe vectors (~66 MB)")
    parser.add_argument("--skip-transformer", action="store_true")
    parser.add_argument("--skip-spacy", action="store_true")
    args = parser.parse_args()

    results = {"NLTK data": step("NLTK data (punkt, stopwords, wordnet)", nltk_data)}
    if not args.skip_transformer:
        results["Sentence transformer"] = step("Sentence-transformer model (~90 MB)", sentence_model)
    if not args.skip_spacy:
        results["spaCy en_core_web_sm"] = step("spaCy English model (optional)", spacy_model)
    if args.glove:
        results["GloVe"] = step("Pretrained GloVe vectors glove-wiki-gigaword-50 (~66 MB)", glove)

    print("\nSummary:")
    for k, ok in results.items():
        print(f"  {'OK    ' if ok else 'FAILED'} {k}")
    print("\nFailed items are optional; the app reports any missing capability in the UI.")


if __name__ == "__main__":
    main()
