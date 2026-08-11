"""TDD: DoclingDocument → ParseResult mapping (real sift_parse_core types)."""

from __future__ import annotations

from pathlib import Path

from sift_parse_core.types.doc import (
    BoundingBox,
    CoordOrigin,
    DoclingDocument,
    ProvenanceItem,
    Size,
    TableCell,
    TableData,
)
from sift_parse_core.types.doc.labels import DocItemLabel

from sift_core.models import BlockType


def _prov(page_no: int, l: float, t: float, r: float, b: float) -> ProvenanceItem:
    return ProvenanceItem(
        page_no=page_no,
        bbox=BoundingBox(l=l, t=t, r=r, b=b, coord_origin=CoordOrigin.TOPLEFT),
        charspan=(0, 1),
    )


def test_map_empty_document_yields_no_blocks() -> None:
    from sift.parse._mapping import map_document

    doc = DoclingDocument(name="empty")
    doc.add_page(page_no=1, size=Size(width=612, height=792))
    result = map_document(doc, source_path=Path("/tmp/empty.pdf"))
    assert result.blocks == []
    assert result.metadata.page_count == 1


def test_map_heading_and_paragraphs() -> None:
    from sift.parse._mapping import map_document

    doc = DoclingDocument(name="hp")
    doc.add_page(page_no=1, size=Size(width=612, height=792))
    doc.add_heading(text="Title", level=1, prov=_prov(1, 10, 40, 200, 20))
    doc.add_text(
        label=DocItemLabel.PARAGRAPH,
        text="First para",
        prov=_prov(1, 10, 80, 300, 60),
    )
    doc.add_text(
        label=DocItemLabel.PARAGRAPH,
        text="Second para",
        prov=_prov(1, 10, 120, 300, 100),
    )

    result = map_document(doc, source_path=Path("/tmp/hp.pdf"))
    types = [b.block_type for b in result.blocks]
    assert types == [BlockType.HEADING, BlockType.PARAGRAPH, BlockType.PARAGRAPH]
    assert [b.ordinal for b in result.blocks] == [0, 1, 2]
    assert result.blocks[0].text == "Title"
    assert result.blocks[0].provenance.bbox.x0 == 10.0
    assert result.blocks[0].confidence is not None


def test_map_table_3x3() -> None:
    from sift.parse._mapping import map_document

    doc = DoclingDocument(name="tbl")
    doc.add_page(page_no=1, size=Size(width=612, height=792))
    cells = [
        TableCell(
            text=f"r{r}c{c}",
            start_row_offset_idx=r,
            end_row_offset_idx=r + 1,
            start_col_offset_idx=c,
            end_col_offset_idx=c + 1,
        )
        for r in range(3)
        for c in range(3)
    ]
    doc.add_table(
        data=TableData(num_rows=3, num_cols=3, table_cells=cells),
        prov=_prov(1, 0, 400, 200, 200),
    )

    result = map_document(doc, source_path=Path("/tmp/tbl.pdf"))
    assert len(result.blocks) == 1
    block = result.blocks[0]
    assert block.block_type is BlockType.TABLE
    assert block.table_data is not None
    assert block.table_data["num_rows"] == 3
    assert block.table_data["num_cols"] == 3
    assert len(block.table_data["cells"]) == 9


def test_map_figure_and_caption() -> None:
    from sift.parse._mapping import map_document

    doc = DoclingDocument(name="fig")
    doc.add_page(page_no=1, size=Size(width=612, height=792))
    cap = doc.add_text(
        label=DocItemLabel.CAPTION,
        text="Figure 1",
        prov=_prov(1, 0, 500, 100, 480),
    )
    doc.add_picture(caption=cap, prov=_prov(1, 0, 480, 100, 400))

    result = map_document(doc, source_path=Path("/tmp/fig.pdf"))
    types = {b.block_type for b in result.blocks}
    assert BlockType.FIGURE in types
    assert BlockType.CAPTION in types


def test_map_nested_section_hierarchy() -> None:
    from sift.parse._mapping import map_document

    doc = DoclingDocument(name="nest")
    doc.add_page(page_no=1, size=Size(width=612, height=792))
    h1 = doc.add_heading(text="L1", level=1, prov=_prov(1, 0, 50, 100, 30))
    h2 = doc.add_heading(text="L2", level=2, parent=h1, prov=_prov(1, 0, 80, 100, 60))
    h3 = doc.add_heading(text="L3", level=3, parent=h2, prov=_prov(1, 0, 110, 100, 90))
    doc.add_text(
        label=DocItemLabel.PARAGRAPH,
        text="leaf",
        parent=h3,
        prov=_prov(1, 0, 140, 100, 120),
    )

    result = map_document(doc, source_path=Path("/tmp/nest.pdf"))
    leaf = next(b for b in result.blocks if b.text == "leaf")
    assert leaf.hierarchy == ["L1", "L2", "L3"]
