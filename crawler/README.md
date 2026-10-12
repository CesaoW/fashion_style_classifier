# Crawler e Pipeline de Dataset para Visão Computacional de Moda

Projeto de Visão Computacional para **classificação automática de 6 estilos de vestuário** (*Streetwear, Clássico, Casual, Alternativo, Country, Boho*).

## 📌 Estrutura do Projeto

```
crawler/
├── data/
│   ├── raw/                 # Download bruto das imagens por classe (Etapas A e B)
│   ├── cleaned/             # Imagens sem duplicatas MD5/ImageHash (Etapa C)
│   ├── filtered/            # Imagens validadas por YOLOv8 (corpo inteiro/médio) (Etapa D)
│   └── dataset/             # Dataset final dividido em train/val/test (Etapa F)
│       ├── train/
│       ├── val/
│       └── test/
├── src/
│   ├── config/
│   │   ├── settings.py      # Configurações globais e caminhos
│   │   └── styles_config.yaml # Mapeamento dos 6 estilos e queries de busca
│   ├── crawlers/
│   │   └── search_crawler.py # Raspagem por motores de busca (DuckDuckGo Images)
│   ├── processors/
│   │   ├── deduplicator.py  # Tratamento inicial, MD5 e Perceptual Hashing
│   │   └── yolo_filter.py   # Detecção de pessoas com YOLOv8 e bounding box
│   ├── dataset/
│   │   └── dataset_builder.py # Organização e divisão estratificada (70/15/15)
│   └── utils/
│       └── logger.py        # Logger centralizado
├── main.py                  # CLI principal do pipeline
└── requirements.txt         # Dependências do projeto
```

## 🚀 Como Executar

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Executar o Pipeline Completo (Etapas A a F)
```bash
python main.py --step all --max-images 50
```

### 3. Executar Etapas Individuais
- **Raspagem (Etapas A/B)**: `python main.py --step crawl`
- **Deduplicação (Etapa C)**: `python main.py --step clean`
- **Filtragem YOLO (Etapa D)**: `python main.py --step filter`
- **Controle de Qualidade OCR (Etapa E)**: `python main.py --step label`
- **Divisão do Dataset (Etapa F)**: `python main.py --step split`
- **Processar um estilo específico**: `python main.py --step all --style streetwear`
