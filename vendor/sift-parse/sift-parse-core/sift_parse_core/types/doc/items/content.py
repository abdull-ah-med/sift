"""Discriminated union of all leaf content item types."""

from typing import Annotated, Union

from pydantic import Field

from sift_parse_core.types.doc.items.code import CodeItem
from sift_parse_core.types.doc.items.form import FieldItem, FieldRegionItem
from sift_parse_core.types.doc.items.key_value import KeyValueItem
from sift_parse_core.types.doc.items.picture.picture import PictureItem
from sift_parse_core.types.doc.items.table.table import TableItem
from sift_parse_core.types.doc.items.text import FormulaItem, ListItem, SectionHeaderItem, TextItem, TitleItem

ContentItem = Annotated[
    Union[
        TextItem,
        TitleItem,
        SectionHeaderItem,
        ListItem,
        CodeItem,
        FormulaItem,
        PictureItem,
        TableItem,
        KeyValueItem,
        FieldRegionItem,
        FieldItem,
    ],
    Field(discriminator="label"),
]
