import os
import json
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image

from src.config.settings import CLEANED_DIR, FILTERED_DIR, STYLES
from src.utils.logger import setup_logger

logger = setup_logger("YOLOFilter")

class YOLOFilter:
    """
    Etapa D — Filtragem Inteligente com Ultralytics YOLO11 / YOLOv8:
    - Detecção de pessoas via YOLO11 (classe 0 = person).
    - Descarta imagens sem presença humana.
    - Valida a bounding box: mantendo apenas corpo inteiro ou médio corpo (altura mínima relativa do corpo).
    - Descarta close-ups de acessórios, rostos isolados, sapatos isolados ou objetos sem outfit completo.
    - Salva imagens filtradas em data/filtered/<style>/.
    """
    def __init__(
        self,
        model_name: str = "yolo11n.pt",
        fallback_model_name: str = "yolov8n.pt",
        min_person_height_ratio: float = 0.35,
        min_person_area_ratio: float = 0.12
    ):
        self.model_name = model_name
        self.fallback_model_name = fallback_model_name
        self.min_person_height_ratio = min_person_height_ratio
        self.min_person_area_ratio = min_person_area_ratio
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from ultralytics import YOLO
            try:
                logger.info(f"Carregando a modelo mais recente Ultralytics ({self.model_name})...")
                self._model = YOLO(self.model_name)
            except Exception as e:
                logger.warning(f"Erro ao carregar {self.model_name}, usando fallback ({self.fallback_model_name}): {e}")
                self._model = YOLO(self.fallback_model_name)
        return self._model

    def validate_image(self, img_path: Path) -> bool:
        """
        Retorna True se a imagem contém pelo menos uma pessoa satisfazendo
        os critérios de corpo inteiro ou médio corpo.
        """
        try:
            with Image.open(img_path) as img:
                width, height = img.size
                img_area = width * height

            results = self.model(str(img_path), verbose=False)
            if not results or len(results) == 0:
                return False

            boxes = results[0].boxes
            if boxes is None or len(boxes) == 0:
                return False

            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())

                # Class 0 is 'person' in COCO dataset
                if cls_id == 0 and conf >= 0.4:
                    xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    box_w = xyxy[2] - xyxy[0]
                    box_h = xyxy[3] - xyxy[1]
                    box_area = box_w * box_h

                    height_ratio = box_h / height
                    area_ratio = box_area / img_area
                    box_center_x = (xyxy[0] + xyxy[2]) / 2 / width

                    # Valida se a pessoa ocupa proporção suficiente e está minimamente centralizada na foto
                    if height_ratio >= self.min_person_height_ratio and area_ratio >= self.min_person_area_ratio:
                        if 0.15 <= box_center_x <= 0.85:
                            return True

        except Exception as e:
            logger.debug(f"Erro na inferência YOLO em {img_path}: {e}")

        return False

    def process_style(self, style_name: str) -> List[Dict[str, Any]]:
        cleaned_style_dir = CLEANED_DIR / style_name
        filtered_style_dir = FILTERED_DIR / style_name
        filtered_style_dir.mkdir(parents=True, exist_ok=True)

        if not cleaned_style_dir.exists():
            logger.warning(f"Diretório limpo {cleaned_style_dir} não existe. Pulei estilo '{style_name}'.")
            return []

        meta_path = cleaned_style_dir / "metadata.json"
        cleaned_items = []
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    cleaned_items = json.load(f)
            except Exception as e:
                logger.error(f"Erro ao ler metadata de {cleaned_style_dir}: {e}")

        if not cleaned_items:
            for p in cleaned_style_dir.glob("*.jpg"):
                cleaned_items.append({
                    "id": p.stem,
                    "style": style_name,
                    "cleaned_path": str(p)
                })

        logger.info(f"Aplicando filtragem inteligência YOLO (YOLO11) em {len(cleaned_items)} imagens de '{style_name}'...")

        filtered_metadata = []
        approved_count = 0
        rejected_count = 0

        for item in cleaned_items:
            img_path = Path(item.get("cleaned_path", ""))
            if not img_path.exists():
                continue

            if self.validate_image(img_path):
                out_filepath = filtered_style_dir / img_path.name
                
                # Copy / Save to filtered dir
                with Image.open(img_path) as img:
                    img.save(out_filepath, "JPEG", quality=95)

                filtered_item = dict(item)
                filtered_item["filtered_path"] = str(out_filepath)
                filtered_metadata.append(filtered_item)
                approved_count += 1
            else:
                rejected_count += 1

        filtered_meta_file = filtered_style_dir / "metadata.json"
        with open(filtered_meta_file, "w", encoding="utf-8") as f:
            json.dump(filtered_metadata, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Estilo '{style_name}': {approved_count} imagens aprovadas pelo YOLO, "
            f"{rejected_count} descartadas (sem pessoa ou proporção inadequada)."
        )
        return filtered_metadata

    def run_all(self):
        for style_name in STYLES.keys():
            self.process_style(style_name)
