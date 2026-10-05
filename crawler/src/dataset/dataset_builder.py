import os
import json
import random
import shutil
from pathlib import Path
from typing import Dict, List, Any

from src.config.settings import FILTERED_DIR, DATASET_DIR, STYLES
from src.utils.logger import setup_logger

logger = setup_logger("DatasetBuilder")

class DatasetBuilder:
    """
    Etapa E e F — Rotulação e Estruturação do Dataset Final:
    - Organiza as imagens filtradas por estilo (weak labels).
    - Divisão estratificada das imagens:
        - Treino (70%)
        - Validação (15%)
        - Teste (15%)
    - Salva em data/dataset/train, val, test.
    - Gera dataset_manifest.json com a contagem final e dados de proveniência.
    """
    def __init__(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42
    ):
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

    def build_dataset(self) -> Dict[str, Any]:
        random.seed(self.seed)

        # Clear/Create target dataset folders
        for split in ["train", "val", "test"]:
            split_dir = DATASET_DIR / split
            split_dir.mkdir(parents=True, exist_ok=True)
            for style in STYLES.keys():
                (split_dir / style).mkdir(parents=True, exist_ok=True)

        manifest = {
            "splits": {"train": 0, "val": 0, "test": 0},
            "styles": {},
            "total_images": 0
        }

        logger.info("Iniciando divisão estratificada do dataset (70% Treino / 15% Val / 15% Teste)...")

        for style_name in STYLES.keys():
            filtered_style_dir = FILTERED_DIR / style_name
            if not filtered_style_dir.exists():
                logger.warning(f"Diretório filtrado {filtered_style_dir} não encontrado. Ignorando...")
                continue

            meta_file = filtered_style_dir / "metadata.json"
            items = []
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        items = json.load(f)
                except Exception:
                    pass

            if not items:
                for p in filtered_style_dir.glob("*.jpg"):
                    items.append({"id": p.stem, "style": style_name, "filtered_path": str(p)})

            images = [item for item in items if Path(item.get("filtered_path", "")).exists()]
            random.shuffle(images)

            n_total = len(images)
            if n_total == 0:
                logger.warning(f"Nenhuma imagem válida para estilo '{style_name}'.")
                continue

            n_train = int(n_total * self.train_ratio)
            n_val = int(n_total * self.val_ratio)
            # Remaining goes to test to preserve exact total
            n_test = n_total - n_train - n_val

            train_imgs = images[:n_train]
            val_imgs = images[n_train:n_train + n_val]
            test_imgs = images[n_train + n_val:]

            splits_data = {
                "train": train_imgs,
                "val": val_imgs,
                "test": test_imgs
            }

            manifest["styles"][style_name] = {
                "train": len(train_imgs),
                "val": len(val_imgs),
                "test": len(test_imgs),
                "total": n_total
            }

            for split_name, img_list in splits_data.items():
                dest_dir = DATASET_DIR / split_name / style_name
                for item in img_list:
                    src_path = Path(item["filtered_path"])
                    dst_path = dest_dir / src_path.name
                    shutil.copy2(src_path, dst_path)
                    manifest["splits"][split_name] += 1
                    manifest["total_images"] += 1

            logger.info(
                f"Estilo '{style_name}': {n_total} imagens -> "
                f"Treino: {len(train_imgs)}, Val: {len(val_imgs)}, Teste: {len(test_imgs)}"
            )

        manifest_path = DATASET_DIR / "dataset_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info(f"Dataset construído com sucesso! Manifesto salvo em {manifest_path}.")
        return manifest
