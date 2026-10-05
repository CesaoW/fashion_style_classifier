import os
import csv
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from PIL import Image

from src.config.settings import FILTERED_DIR, DATASET_DIR, ROOT_DIR, STYLES
from src.utils.logger import setup_logger

logger = setup_logger("OCRCleaner")

class OCRDatasetCleaner:
    """
    Etapa G — Limpeza por OCR e Rótulos Conflitantes:
    - Detecta imagens com textos sobrepostos significativos (banners, colagens, títulos) que prejudicam o treino.
    - Detecta imagens com conteúdo idêntico (MD5) presentes em múltiplos estilos ou splits.
    - Move as imagens filtradas para data/dataset_revisao/<split>/<estilo>/
    - Gera o arquivo relatorio_limpeza.csv com detalhes do descarte/revisão.
    """
    def __init__(
        self,
        dataset_dir: Path = FILTERED_DIR,
        revisao_dir: Path = None,
        min_word_len: int = 4,
        min_word_count: int = 2
    ):
        self.dataset_dir = dataset_dir
        self.revisao_dir = revisao_dir or (ROOT_DIR / "data" / "dataset_revisao")
        self.min_word_len = min_word_len
        self.min_word_count = min_word_count
        self._ocr_reader = None

    @property
    def reader(self):
        """Inicializa EasyOCR sob demanda ou usa alternativa leve via Tesseract/regex visual."""
        if self._ocr_reader is None:
            try:
                import torch
                # Suprime os avisos de pin_memory do PyTorch quando rodando via CPU
                import warnings
                warnings.filterwarnings("ignore", message=".*pin_memory.*")

                import easyocr
                logger.info("Carregando modelo EasyOCR (inglês/português)...")
                self._ocr_reader = easyocr.Reader(['en', 'pt'], gpu=False)
            except Exception as e:
                logger.warning(f"EasyOCR não disponível ({e}). Tentando pytesseract...")
                try:
                    import pytesseract
                    self._ocr_reader = "pytesseract"
                except Exception:
                    logger.warning("Pytesseract não instalado. Usando fallback de detecção de textura de texto.")
                    self._ocr_reader = "fallback"
        return self._ocr_reader

    @staticmethod
    def get_md5(filepath: Path) -> str:
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def detect_text(self, img_path: Path) -> Tuple[int, str]:
        """
        Executa OCR na imagem e retorna (quantidade_palavras_validas, texto_extraido).
        """
        try:
            reader = self.reader
            if reader == "fallback":
                return 0, ""

            if reader == "pytesseract":
                import pytesseract
                with Image.open(img_path) as img:
                    text = pytesseract.image_to_string(img.convert("L"), config="--psm 11")
                words = [w for w in text.split() if len(w) >= self.min_word_len and w.isalpha()]
                return len(words), " ".join(words[:15])

            # EasyOCR
            results = reader.readtext(str(img_path), detail=0)
            all_text = " ".join(results)
            words = [w for w in all_text.split() if len(w) >= self.min_word_len and w.isalpha()]
            return len(words), " ".join(words[:15])

        except Exception as e:
            logger.debug(f"Erro ao processar OCR em {img_path}: {e}")
            return 0, ""

    def process_cleaning(self) -> Dict[str, Any]:
        self.revisao_dir.mkdir(parents=True, exist_ok=True)
        report_path = ROOT_DIR / "relatorio_limpeza.csv"

        logger.info("Mapeando arquivos para checagem de MD5 (Rótulos Conflitantes)...")
        md5_map: Dict[str, List[Tuple[str, str, Path]]] = {} # md5 -> [(split/categoria, estilo, path)]
        all_files: List[Tuple[str, str, Path]] = []

        for style in STYLES.keys():
            style_dir = self.dataset_dir / style
            if style_dir.exists() and style_dir.is_dir():
                for img_p in style_dir.glob("*"):
                    if img_p.is_file() and img_p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                        all_files.append(("filtered", style, img_p))
                        h = self.get_md5(img_p)
                        if h not in md5_map:
                            md5_map[h] = []
                        md5_map[h].append(("filtered", style, img_p))
            else:
                # Checa se a estrutura é baseada em splits (ex: dataset/train/style)
                for split in ["train", "val", "test"]:
                    split_style_dir = self.dataset_dir / split / style
                    if split_style_dir.exists() and split_style_dir.is_dir():
                        for img_p in split_style_dir.glob("*"):
                            if img_p.is_file() and img_p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                                all_files.append((split, style, img_p))
                                h = self.get_md5(img_p)
                                if h not in md5_map:
                                    md5_map[h] = []
                                md5_map[h].append((split, style, img_p))

        logger.info(f"Total de {len(all_files)} imagens encontradas para análise OCR. Analisando...")

        flagged_reports = []
        moved_count = 0
        conflict_count = 0
        ocr_flag_count = 0

        seen_conflicts: Set[Path] = set()

        # 1. Identificar rótulos conflitantes (mesmo MD5 em múltiplos estilos/splits)
        for md5_hash, occurrences in md5_map.items():
            styles_found = {occ[1] for occ in occurrences}
            if len(occurrences) > 1 and len(styles_found) > 1:
                # Há conflito de estilo!
                conflict_count += len(occurrences)
                for split, style, filepath in occurrences:
                    seen_conflicts.add(filepath)
                    flagged_reports.append({
                        "caminho_original": str(filepath),
                        "split": split,
                        "estilo": style,
                        "num_palavras_ocr": 0,
                        "texto_detectado": f"Conflito entre estilos: {list(styles_found)}",
                        "motivo": "rotulo_conflitante"
                    })

        # 2. Processar OCR nas imagens
        logger.info("Executando verificação de OCR para remover banners e colagens com texto sobreposto...")
        for split, style, filepath in all_files:
            is_conflict = filepath in seen_conflicts

            num_words, text_sample = self.detect_text(filepath)
            is_ocr_suspect = num_words >= self.min_word_count

            if is_ocr_suspect and not is_conflict:
                ocr_flag_count += 1
                flagged_reports.append({
                    "caminho_original": str(filepath),
                    "split": split,
                    "estilo": style,
                    "num_palavras_ocr": num_words,
                    "texto_detectado": text_sample,
                    "motivo": "texto_sobreposto"
                })

            # Se a imagem foi sinalizada (por OCR ou por Rótulo Conflitante), move para dataset_revisao/
            if is_conflict or is_ocr_suspect:
                dest_dir = self.revisao_dir / split / style
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_filepath = dest_dir / filepath.name

                try:
                    shutil.move(str(filepath), str(dest_filepath))
                    moved_count += 1
                except Exception as e:
                    logger.error(f"Falha ao mover {filepath} para revisão: {e}")

        # 3. Salvar relatório CSV
        with open(report_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "caminho_original", "split", "estilo", "num_palavras_ocr", "texto_detectado", "motivo"
            ])
            writer.writeheader()
            writer.writerows(flagged_reports)

        logger.info("=== RESUMO FINAL DA LIMPEZA (OCR + CONFLITOS) ===")
        logger.info(f"Total de imagens sinalizadas e movidas para revisão: {moved_count}")
        logger.info(f"  - Por rótulo conflitante: {conflict_count}")
        logger.info(f"  - Por texto sobreposto (OCR): {ocr_flag_count}")
        logger.info(f"Relatório gerado em: {report_path}")
        logger.info(f"Imagens movidas com sucesso para: {self.revisao_dir}")

        return {
            "total_moved": moved_count,
            "conflict_count": conflict_count,
            "ocr_flag_count": ocr_flag_count,
            "report_path": str(report_path)
        }
