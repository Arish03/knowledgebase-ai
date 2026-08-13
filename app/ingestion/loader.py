"""
Document loader — loads PDF, .docx, .md, and .txt files from the
company_docs directory into LangChain Document objects.
"""

from pathlib import Path
from typing import List

from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_community.document_loaders import Docx2txtLoader

from app.config import COMPANY_DOCS_PATH


def _make_loader(glob: str, loader_cls, **kwargs) -> DirectoryLoader:
    """Create a DirectoryLoader for a specific file type."""
    return DirectoryLoader(
        COMPANY_DOCS_PATH,
        glob=glob,
        loader_cls=loader_cls,
        show_progress=True,
        use_multithreading=True,
        **kwargs,
    )


def load_documents() -> List:
    """
    Load all supported documents from COMPANY_DOCS_PATH.

    Returns a flat list of LangChain Document objects, each carrying
    ``metadata["source"]`` pointing back to the original file.
    """
    docs_path = Path(COMPANY_DOCS_PATH)
    if not docs_path.exists():
        raise FileNotFoundError(
            f"Company docs directory not found: {COMPANY_DOCS_PATH}"
        )

    loaders = [
        _make_loader("**/*.pdf", PyPDFLoader),
        _make_loader("**/*.docx", Docx2txtLoader),
        _make_loader("**/*.md", TextLoader, loader_kwargs={"encoding": "utf-8"}),
        _make_loader("**/*.txt", TextLoader, loader_kwargs={"encoding": "utf-8"}),
    ]

    all_docs = []
    for loader in loaders:
        try:
            docs = loader.load()
            all_docs.extend(docs)
        except Exception as exc:
            # Log but continue — one bad file shouldn't block the rest.
            print(f"Warning: loader error ({exc}), continuing with other files.")

    print(f"Loaded {len(all_docs)} document section(s) from {COMPANY_DOCS_PATH}")
    return all_docs
