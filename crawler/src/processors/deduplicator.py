import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Set
from PIL import Image
import imagehash   

from src.config.settings import RAW_DIR, CLEANED_DIR, STYLES
from src.utils.logger import setup_logger

logger = setup_logger("Deduplicator")

class Deduplicator:
    """
    Etapa C — Tratamento Inicial de Dados:
    - Validação de integridade do arquivo de imagem (Pillow).
    - Conversão para formato padronizado JPG (RGB).
    - Remoção de duplicatas exatas via MD5.
    - Remoção de duplicatas perceptuais visuais via ImageHash (pHash / dHash).
    - Salva resultados em data/cleaned/<style>/.
    """
    def __init__(self, max_hash_distance: int = 5):
        self.max_hash_distance = max_hash_distance

    @staticmethod
    def get_md5(filepath: Path) -> str:
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def get_phash(img: Image.Image):
        if imagehash is None:
            return None
        return imagehash.phash(img)

    def process_style(self, style_name: str, global_md5: Set[str] = None, global_hashes: List = None) -> List[Dict[str, Any]]:
        if global_md5 is None:
            global_md5 = set()
        if global_hashes is None:
            global_hashes = []

        raw_style_dir = RAW_DIR / style_name
        cleaned_style_dir = CLEANED_DIR / style_name
        cleaned_style_dir.mkdir(parents=True, exist_ok=True)

        if not raw_style_dir.exists():
            logger.warning(f"Diretório bruto {raw_style_dir} não encontrado. Pulei o estilo '{style_name}'.")
            return []

        raw_metadata_path = raw_style_dir / "metadata.json"
        raw_items = []
        if raw_metadata_path.exists():
            try:
                with open(raw_metadata_path, "r", encoding="utf-8") as f:
                    raw_items = json.load(f)
            except Exception as e:
                logger.error(f"Erro ao ler metadata de {raw_style_dir}: {e}")

        # If metadata missing, scan raw_style_dir for image files
        if not raw_items:
            for p in raw_style_dir.glob("*"):
                if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    raw_items.append({
                        "id": p.stem,
                        "style": style_name,
                        "local_path": str(p)
                    })

        logger.info(f"Processando {len(raw_items)} imagens brutos para estilo '{style_name}'...")

        cleaned_metadata = []
        valid_count = 0
        duplicate_count = 0
        corrupt_count = 0

        for item in raw_items:
            img_path = Path(item["local_path"])
            if not img_path.exists():
                continue

            # Check MD5
            md5_hash = self.get_md5(img_path)
            if md5_hash in global_md5:
                duplicate_count += 1
                continue

            # Open and validate image
            try:
                with Image.open(img_path) as img:
                    img.verify()
                
                with Image.open(img_path) as img:
                    img = img.convert("RGB")
                    phash = self.get_phash(img)
                    dhash = imagehash.dhash(img) if imagehash else None

                    # Check perceptual hash distance if imagehash available
                    is_visual_duplicate = False
                    if phash is not None:
                        for existing_phash, existing_dhash in global_hashes:
                            p_dist = phash - existing_phash
                            d_dist = dhash - existing_dhash if dhash and existing_dhash else 99
                            if p_dist <= self.max_hash_distance or d_dist <= self.max_hash_distance:
                                is_visual_duplicate = True
                                break

                    if is_visual_duplicate:
                        duplicate_count += 1
                        continue

                    # Save cleaned image
                    out_filename = f"{item['id']}.jpg"
                    out_filepath = cleaned_style_dir / out_filename
                    img.save(out_filepath, "JPEG", quality=95)

                    global_md5.add(md5_hash)
                    if phash is not None:
                        global_hashes.append((phash, dhash))

                    cleaned_item = dict(item)
                    cleaned_item["cleaned_path"] = str(out_filepath)
                    cleaned_item["md5"] = md5_hash
                    cleaned_item["phash"] = str(phash)
                    cleaned_metadata.append(cleaned_item)

                    valid_count += 1

            except Exception as e:
                logger.debug(f"Arquivo corrompido ou inválido {img_path}: {e}")
                corrupt_count += 1

        cleaned_meta_file = cleaned_style_dir / "metadata.json"
        with open(cleaned_meta_file, "w", encoding="utf-8") as f:
            json.dump(cleaned_metadata, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Estilo '{style_name}': {valid_count} imagens limpas salvas, "
            f"{duplicate_count} duplicatas descartadas, {corrupt_count} corrompidas descartadas."
        )
        return cleaned_metadata

    def run_all(self):
        global_md5: Set[str] = set()
        global_hashes: List = []
        for style_name in STYLES.keys():
            self.process_style(style_name, global_md5, global_hashes)

