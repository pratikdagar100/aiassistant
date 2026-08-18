"""Vision API: screenshot (as an actual image response), OCR, and optional
vision-LLM Q&A. These bypass the generic /api/computer/execute string-result
wrapper because a screenshot needs to come back as real image bytes.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.vision import ocr, screenshot, vision_model

router = APIRouter()


class DescribeRequest(BaseModel):
    question: str = "Describe what's on the screen."
    model: str | None = None


@router.get("/screenshot")
def get_screenshot() -> Response:
    try:
        png = screenshot.capture_full_screen()
    except screenshot.ScreenshotError as exc:
        raise HTTPException(500, str(exc)) from exc
    return Response(content=png, media_type="image/png")


@router.get("/dimensions")
def get_dimensions() -> dict:
    try:
        return screenshot.screen_dimensions()
    except screenshot.ScreenshotError as exc:
        raise HTTPException(500, str(exc)) from exc


@router.get("/ocr")
def get_ocr_text() -> dict:
    try:
        png = screenshot.capture_full_screen()
        text = ocr.extract_text(png)
    except (screenshot.ScreenshotError, ocr.OCRError) as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"text": text}


@router.post("/describe")
async def describe_screen(req: DescribeRequest) -> dict:
    try:
        png = screenshot.capture_full_screen()
        description = await vision_model.describe_image(png, question=req.question, model=req.model)
    except (screenshot.ScreenshotError, vision_model.VisionModelError) as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"description": description}


@router.get("/status")
def vision_status() -> dict:
    return {"ocr_available": ocr.is_available()}
