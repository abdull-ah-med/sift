import warnings
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from sift_parse.backend.sift_parse_pdf_backend import DoclingParseDocumentBackend
from sift_parse.datamodel.backend_options import PdfBackendOptions

if TYPE_CHECKING:
    from sift_parse.datamodel.document import InputDocument


class DoclingParseV4DocumentBackend(DoclingParseDocumentBackend):
    def __init__(
        self,
        in_doc: "InputDocument",
        path_or_stream: Union[BytesIO, Path],
        options: Optional[PdfBackendOptions] = None,
    ):
        if options is None:
            options = PdfBackendOptions()
        warnings.warn(
            "DoclingParseV4DocumentBackend was removed in sift_parse 2.74.0 and will raise an "
            "error in a future release. Use DoclingParseDocumentBackend instead.",
            FutureWarning,
            stacklevel=2,
        )
        super().__init__(in_doc, path_or_stream, options)
