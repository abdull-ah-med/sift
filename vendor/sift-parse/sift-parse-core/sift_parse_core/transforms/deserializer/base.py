"""Define base classes for deserialization."""

from abc import ABC, abstractmethod

from sift_parse_core.types.doc import DoclingDocument


class BaseDocDeserializer(ABC):
    """Base class for document deserializers."""

    @abstractmethod
    def deserialize_str(self, text: str, **kwargs) -> DoclingDocument:
        """Deserialize a string representation into a DoclingDocument."""
        ...
