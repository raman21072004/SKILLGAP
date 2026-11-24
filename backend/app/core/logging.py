"""Logging configuration. Resume and job-description contents are never logged."""

from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # Third-party libraries are noisy at INFO level
    for noisy in ("sentence_transformers", "transformers", "gensim", "httpx", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
