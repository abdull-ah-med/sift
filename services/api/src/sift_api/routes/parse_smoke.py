"""Internal Phase 0 parse smoke endpoint."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field

from sift_parse.smoke import ParseSmokeResult, run_parse_smoke

router = APIRouter(prefix="/internal", tags=["internal"])

_MAX_UPLOAD_BYTES = 25 * 1024 * 1024


class ParseSmokeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    blocks: int = Field(ge=0)
    markdown_length: int = Field(ge=0)
    source_filename: str
    engine: str


@router.post(
    "/parse-smoke",
    response_model=ParseSmokeResponse,
    status_code=status.HTTP_200_OK,
)
async def parse_smoke(file: UploadFile = File(...)) -> ParseSmokeResponse:
    """Accept a PDF, run Phase 0 parse smoke, return block counts."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")
    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="empty upload")
    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="upload exceeds 25 MiB cap")

    suffix = Path(file.filename).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(raw)
        tmp.flush()
        try:
            result: ParseSmokeResult = run_parse_smoke(Path(tmp.name))
        except ImportError as exc:
            raise HTTPException(
                status_code=503,
                detail="parse stack unavailable in this environment",
            ) from exc
        except (OSError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="parse failed") from exc

    return ParseSmokeResponse(
        blocks=result.blocks,
        markdown_length=result.markdown_length,
        source_filename=file.filename,
        engine=result.engine,
    )
