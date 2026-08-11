"""Define the deserializer types."""

from sift_parse_core.transforms.deserializer.base import BaseDocDeserializer
from sift_parse_core.transforms.deserializer.doclang import DocLangDocDeserializer
from sift_parse_core.transforms.deserializer.doclang_source_mapping import (
    DocLangSourceMap,
    DocLangSourceTarget,
)

__all__ = [
    "BaseDocDeserializer",
    "DocLangDocDeserializer",
    "DocLangSourceMap",
    "DocLangSourceTarget",
]
