import argparse
import sys
from pathlib import Path

# Add project root to sys.path
current_dir = Path(__file__).parent.resolve()
sys.path.append(str(current_dir))

from src.config.settings import STYLES
from src.crawlers.fashion_crawler import FashionCrawler
from src.processors.deduplicator import Deduplicator
from src.processors.yolo_filter import YOLOFilter
from src.processors.ocr_cleaner import OCRDatasetCleaner
from src.dataset.dataset_builder import DatasetBuilder
from src.utils.logger import setup_logger

logger = setup_logger("MainPipeline")

def run_pipeline(step: str, target_style: str = None, max_images: int = 200):
    styles_to_process = [target_style] if target_style else list(STYLES.keys())

    # Etapa A & B: Crawling (Pinterest via gallery-dl)
    if step in ["crawl", "all"]:
        logger.info("=== [ETAPAS A & B] Raspagem de Moda do Pinterest via gallery-dl ===")
        crawler = FashionCrawler(max_images_per_style=max_images)
        for style in styles_to_process:
            crawler.crawl_style(style)

    # Etapa C: Cleaning & Deduplication
    if step in ["clean", "all"]:
        logger.info("=== [ETAPA C] Sanitização e Deduplicação Global (MD5 + pHash/dHash) ===")
        deduper = Deduplicator()
        deduper.run_all()

    # Etapa D: YOLO Smart Filtering
    if step in ["filter", "all"]:
        logger.info("=== [ETAPA D] Filtragem Inteligente com YOLO (Detecção de Pessoas / Outfits) ===")
        yolo_filter = YOLOFilter()
        for style in styles_to_process:
            yolo_filter.process_style(style)

    # Etapa E: OCR & Conflict Cleaning (Quality Control / Labeling)
    if step in ["label", "all"]:
        logger.info("=== [ETAPA E] Controle de Qualidade: OCR e Rótulos Conflitantes ===")
        ocr_cleaner = OCRDatasetCleaner()
        ocr_cleaner.process_cleaning()

    # Etapa F: Dataset Splitting & Manifest
    if step in ["split", "all"]:
        logger.info("=== [ETAPA F] Organização e Divisão Estratificada do Dataset (70/15/15) ===")
        builder = DatasetBuilder()
        builder.build_dataset()

    logger.info("Pipeline concluído com sucesso!")

def main():
    parser = argparse.ArgumentParser(description="Pipeline de Visão Computacional para Dataset de Moda Real (6 Estilos)")
    parser.add_argument(
        "--step",
        type=str,
        default="all",
        choices=["crawl", "clean", "filter", "label", "split", "all"],
        help="Etapa a ser executada: crawl (A/B), clean (C), filter (D), label (E - OCR/QC), split (F) ou all."
    )
    parser.add_argument(
        "--style",
        type=str,
        default=None,
        choices=list(STYLES.keys()),
        help="Filtrar execução para um estilo específico."
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=100,
        help="Número máximo de imagens a buscar durante a raspagem por estilo."
    )

    args = parser.parse_args()
    
    try:
        run_pipeline(step=args.step, target_style=args.style, max_images=args.max_images)
    except Exception as e:
        logger.error(f"Erro na execução do pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
