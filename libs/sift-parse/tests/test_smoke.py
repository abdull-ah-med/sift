from pathlib import Path

import pytest

from sift.parse.smoke import ParseSmokeResult, run_parse_smoke

CORPUS = Path(__file__).resolve().parents[3] / "evals" / "corpus"
DIGITAL_PDFS = sorted(CORPUS.glob("digital-*.pdf"))


class _FakeDocument:
    def __init__(self) -> None:
        self.texts = ["a", "b", "c"]
        self.tables: list[object] = []
        self.pictures: list[object] = []

    def export_to_markdown(self) -> str:
        return "# hello\n\nworld"


class _FakeResult:
    def __init__(self) -> None:
        self.document = _FakeDocument()


class _FakeConverter:
    def convert(self, source: str | Path) -> _FakeResult:
        assert Path(source).exists()
        return _FakeResult()


def test_run_parse_smoke_returns_counts_when_converter_injected(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.1\n%\xe2\xe3\xcf\xd3\n")

    result = run_parse_smoke(pdf, converter_factory=_FakeConverter)

    assert isinstance(result, ParseSmokeResult)
    assert result.blocks == len(_FakeDocument().texts)
    assert result.markdown_length == len("# hello\n\nworld")
    assert result.source.endswith("sample.pdf")
    assert result.engine == "injected"


def test_run_parse_smoke_raises_when_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.pdf"
    with pytest.raises(FileNotFoundError):
        run_parse_smoke(missing, converter_factory=_FakeConverter)


@pytest.mark.parametrize("pdf_path", DIGITAL_PDFS, ids=lambda p: p.name)
def test_digital_corpus_parse_smoke_returns_blocks(pdf_path: Path) -> None:
    assert pdf_path.is_file()
    result = run_parse_smoke(pdf_path)
    assert result.blocks > 0
    assert result.markdown_length > 0
    assert result.engine == "pypdfium2"
