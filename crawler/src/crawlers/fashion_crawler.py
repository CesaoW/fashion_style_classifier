import os
import re
import json
import uuid
import time
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import quote_plus

from src.config.settings import RAW_DIR, STYLES, TIMEOUT, STYLES_CONFIG
from src.utils.logger import setup_logger

logger = setup_logger("FashionCrawler")

def slugify(text: str) -> str:
    """Converte texto de busca em um slug limpo para nomes de arquivo."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')

class FashionCrawler:
    """
    Etapa A e B (Raspagem de Moda do Pinterest via gallery-dl):
    Coleta fotos de roupas e outfits autênticos usando gallery-dl no Pinterest.
    Nomeia os arquivos com um padrão semântico descritivo:
        <estilo>_pinterest_<query_slug>_<index>.<ext>
    """
    def __init__(self, max_images_per_style: int = 100):
        self.max_images_per_style = max_images_per_style
        self.gallery_dl_config = STYLES_CONFIG.get("gallery_dl", {})
        self.delay_between_searches = self.gallery_dl_config.get("delay_seconds", 5)
        self.cookies_file = self.gallery_dl_config.get("cookies_file", None)

        self._check_gallery_dl_installed()

    def _check_gallery_dl_installed(self):
        if not shutil.which("gallery-dl"):
            logger.warning(
                "Ferramenta 'gallery-dl' não foi encontrada no sistema PATH! "
                "Para instalá-la, rode: pip install gallery-dl"
            )

    def fetch_pinterest_gallery_dl(self, query: str, output_dir: Path, max_count: int = 30) -> List[Path]:
        """
        Executa a coleta de pins do Pinterest via gallery-dl para uma query específica.
        """
        url_busca = f"https://www.pinterest.com/search/pins/?q={quote_plus(query)}"
        
        # Subdiretório temporário para esta query
        temp_query_dir = output_dir / f"temp_{uuid.uuid4().hex[:8]}"
        temp_query_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            "gallery-dl",
            "--range", f"1-{max_count}",
            "-d", str(temp_query_dir),
            url_busca,
        ]

        if self.cookies_file and os.path.exists(self.cookies_file):
            cmd.insert(1, "--cookies")
            cmd.insert(2, str(self.cookies_file))

        downloaded_files = []
        try:
            logger.info(f"Executando gallery-dl (Max {max_count} imagens): {query}")
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Encontra todas as imagens baixadas no subdiretório temporário
            for p in temp_query_dir.rglob("*"):
                if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    downloaded_files.append(p)

        except Exception as e:
            logger.error(f"Erro ao executar gallery-dl para query '{query}': {e}")

        return downloaded_files

    def crawl_style(self, style_name: str) -> List[Dict[str, Any]]:
        style_info = STYLES.get(style_name)
        if not style_info:
            logger.error(f"Estilo '{style_name}' não encontrado no arquivo de configuração!")
            return []

        out_dir = RAW_DIR / style_name
        out_dir.mkdir(parents=True, exist_ok=True)

        metadata_file = out_dir / "metadata.json"
        existing_metadata = []
        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    existing_metadata = json.load(f)
            except Exception:
                existing_metadata = []

        new_metadata = list(existing_metadata)
        downloaded_count = 0

        queries = style_info.get("search_queries", [])
        if not queries:
            logger.warning(f"Nenhuma query configurada para o estilo '{style_name}'.")
            return []

        per_query_target = max(10, self.max_images_per_style // len(queries))
        
        # Descobre o maior índice numérico já existente para esse estilo para manter a sequência
        current_index = len(existing_metadata) + 1

        for query in queries:
            query_slug = slugify(query)
            logger.info(f"[{style_name}] Iniciando busca Pinterest por termo: '{query}'...")
            downloaded_files = self.fetch_pinterest_gallery_dl(query, out_dir, max_count=per_query_target)
            
            logger.info(f"  -> {len(downloaded_files)} arquivos baixados por gallery-dl.")

            for temp_file in downloaded_files:
                ext = temp_file.suffix.lower()
                # Padrão de Nomenclatura Semântica: <estilo>_pinterest_<index>.<ext>
                img_name = f"{style_name}_pinterest_{current_index:04d}{ext}"
                final_filepath = out_dir / img_name

                try:
                    # Move o arquivo temporário para a pasta raw final com nome semântico
                    shutil.move(str(temp_file), str(final_filepath))
                    
                    metadata_entry = {
                        "id": Path(img_name).stem,
                        "filename": img_name,
                        "style": style_name,
                        "source": "Pinterest",
                        "query": query,
                        "local_path": str(final_filepath),
                    }
                    new_metadata.append(metadata_entry)
                    downloaded_count += 1
                    current_index += 1
                except Exception as e:
                    logger.debug(f"Erro ao mover arquivo baixado {temp_file}: {e}")

            # Limpa diretórios temporários vazios
            for p in out_dir.glob("temp_*"):
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)

            time.sleep(self.delay_between_searches)

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(new_metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Estilo '{style_name}': Total de {downloaded_count} novas fotos salvas com nomenclatura padronizada em {out_dir}.")
        return new_metadata

    def run_all(self):
        for style_name in STYLES.keys():
            self.crawl_style(style_name)
