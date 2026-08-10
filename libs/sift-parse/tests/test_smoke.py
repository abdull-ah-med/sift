from pathlib import Path

from sift_parse.smoke import ParseSmokeResult, run_parse_smoke


class _FakeDocument:
    def __init__(self) -> None:
        self.texts = ["a", "b", "c"]
        self.tables = []
        self.pictures = []

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


def test_run_parse_smoke_raises_when_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.pdf"
    try:
        run_parse_smoke(missing, converter_factory=_FakeConverter)
    except FileNotFoundError:
        return
    raise AssertionError("expected FileNotFoundError")
