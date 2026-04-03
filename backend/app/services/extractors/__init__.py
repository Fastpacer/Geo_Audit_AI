# backend/app/services/extractors/__init__.py
import sys

from .reader_mode import ReaderModeExtractor
from .llm_enricher import LLMContentEnricher

if sys.platform == "win32":
    from .playwright_sync import PlaywrightSyncExtractor as PlaywrightExtractor
else:
    from .playwright import PlaywrightExtractor

__all__ = [
    'ReaderModeExtractor', 
    'PlaywrightExtractor', 
    'LLMContentEnricher',
    'PlaywrightSyncExtractor'
]