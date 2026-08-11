def ocr_engines():
    from sift_parse.models.stages.ocr.auto_ocr_model import OcrAutoModel
    from sift_parse.models.stages.ocr.easyocr_model import EasyOcrModel
    from sift_parse.models.stages.ocr.kserve_v2_ocr_model import KserveV2OcrModel
    from sift_parse.models.stages.ocr.nemotron_ocr_model import NemotronOcrModel
    from sift_parse.models.stages.ocr.ocr_mac_model import OcrMacModel
    from sift_parse.models.stages.ocr.rapid_ocr_model import RapidOcrModel
    from sift_parse.models.stages.ocr.tesseract_ocr_cli_model import TesseractOcrCliModel
    from sift_parse.models.stages.ocr.tesseract_ocr_model import TesseractOcrModel

    return {
        "ocr_engines": [
            OcrAutoModel,
            EasyOcrModel,
            KserveV2OcrModel,
            NemotronOcrModel,
            OcrMacModel,
            RapidOcrModel,
            TesseractOcrModel,
            TesseractOcrCliModel,
        ]
    }


def picture_description():
    from sift_parse.models.stages.picture_description.picture_description_api_model import (
        PictureDescriptionApiModel,
    )
    from sift_parse.models.stages.picture_description.picture_description_vlm_engine_model import (
        PictureDescriptionVlmEngineModel,
    )
    from sift_parse.models.stages.picture_description.picture_description_vlm_model import (
        PictureDescriptionVlmModel,
    )

    return {
        "picture_description": [
            PictureDescriptionVlmEngineModel,  # New engine-based (preferred)
            PictureDescriptionVlmModel,  # Legacy direct transformers
            PictureDescriptionApiModel,  # API-based
        ]
    }


def layout_engines():
    from sift_parse.experimental.models.table_crops_layout_model import (
        TableCropsLayoutModel,
    )
    from sift_parse.models.stages.layout.layout_model import LayoutModel
    from sift_parse.models.stages.layout.layout_object_detection_model import (
        LayoutObjectDetectionModel,
    )

    return {
        "layout_engines": [
            LayoutObjectDetectionModel,
            LayoutModel,
            TableCropsLayoutModel,
        ]
    }


def table_structure_engines():
    from sift_parse.models.stages.table_structure.table_structure_model import (
        TableStructureModel,
    )
    from sift_parse.models.stages.table_structure.table_structure_model_granite_vision import (
        GraniteVisionTableStructureModel,
    )
    from sift_parse.models.stages.table_structure.table_structure_model_v2 import (
        TableStructureModelV2,
    )

    return {
        "table_structure_engines": [
            TableStructureModel,
            TableStructureModelV2,
            GraniteVisionTableStructureModel,
        ]
    }
