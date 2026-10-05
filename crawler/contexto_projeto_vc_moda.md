
# Projeto de Visão Computacional: Classificação Automática de Estilos de Moda

**Curso:** Engenharia de Computação – IFMG Campus Bambuí
**Disciplina:** Visão Computacional
**Aluno:** César Nogueira Rodrigues
**Data:** Setembro de 2026

---

## 1. Visão Geral do Projeto

O objetivo deste projeto é desenvolver uma solução completa de Visão Computacional para **automação e padronização da classificação de estilos de vestuário** em imagens de corpo inteiro (*outfits*). A solução visa reduzir a subjetividade e a demanda de tempo na triagem manual de acervos de e-commerces, brechós digitais e monitoramento de tendências urbanas.

### Classes Selecionadas (6 Estilos)

| Estilo | Características principais |
|---|---|
| **Streetwear** | Moda urbana, modelagens oversized, marcas esportivas, tênis em destaque, elementos de skate/hip-hop |
| **Clássico** | Alfaiataria, blazers, cortes retos, peças elegantes, paleta de cores neutras, estilo old money / executivo |
| **Casual** | Roupas do dia a dia, jeans básicos, camisetas lisas, foco em conforto e simplicidade visual |
| **Alternativo** | Fusão das subculturas Punk, Grunge e Gótico; predomínio de tons escuros, calças rasgadas, xadrez, couro e coturnos |
| **Country** | Estética sertaneja/western; botas, chapéus, cintos de fivela grande, jeans lavados e elementos de couro/franjas |
| **Boho** | Estilo boêmio/romântico; estampas florais/botânicas, tecidos fluidos, saias longas, franjas e tons terrosos |

---

## 2. Estrutura do Crawler e Construção do Dataset

processo de raspagem, filtragem automatizada e rotulação dos dados.

**Etapa A — Configuração de Entrada**
- Lista de queries por classe (ex.: "streetwear outfit", "classic fashion look")
- Lista de fontes (Pinterest, Lookbook.nu, portais de street style)

**Etapa B — Execução do Crawler**
- Automação via Selenium/Playwright ou requisições HTTP (BeautifulSoup/Scrapy)
- Extração de URLs das imagens + metadados (hashtags/descrições)
- Download das imagens em alta resolução em diretórios temporários

**Etapa C — Tratamento Inicial de Dados**
- Remoção de duplicatas (hash MD5 / imagehash para similaridade visual)
- Padronização de formatos (.jpg / .png) e validação de arquivos corrompidos

**Etapa D — Filtragem Inteligente (Pré-anotação)**
- Detecção de pessoas (YOLOv8): descarta imagens sem presença humana
- Validação de bounding box: mantém apenas fotos de corpo inteiro/médio corpo
- Descarte automático de close-ups de acessórios/rosto ou imagens com texto/logo

**Etapa E — Rotulação e Controle de Qualidade**
- Organização dos diretórios por weak labels (queries de origem)
- Inspeção manual para remoção de falsos positivos e casos ambíguos
- Balanceamento de classes (~300 a 500 imagens por estilo)

**Etapa F — Estruturação do Dataset Final**
- Registro de proveniência (fontes e quantidades para o artigo)
- Divisão estratificada: treino (70%), validação (15%), teste (15%)

```
ETAPA A ──▶ ETAPA B ──▶ ETAPA C ──▶ ETAPA D ──▶ ETAPA E ──▶ ETAPA F
Config.     Crawler     Tratamento  Filtragem   Rotulação   Dataset
entrada     execução    inicial     inteligente e QC        final
```

---

## 3. Fluxograma Completo do Projeto

### 1. Definição do Problema
- Contextualização da volatilidade da moda e limitação da catalogação manual
- Motivação acadêmica/prática e definição das 6 classes de estilo

### 2. Aquisição e Construção do Dataset
- Execução da estrutura do crawler (Seção 2)
- Tratamento, filtragem e balanceamento dos dados
- Divisão em treino, validação e teste

### 3. Pré-processamento de Imagens
- Redimensionamento padronizado (ex.: 224×224 ou 384×384 pixels)
- Normalização de iluminação e cores
- Data augmentation (rotação leve, flip horizontal, ajuste de brilho/contraste)
- Experimento secundário: treinamento com fundo original vs. fundo removido (RemBG)

### 4. Desenvolvimento e Arquitetura do Sistema
- Definição do pipeline: Imagem → Pré-processamento → CNN/Backbone → Classificação
- Escolha de duas arquiteturas para comparação (ex.: ResNet-50 vs. EfficientNet-B0)
- Aplicação de transfer learning e fine-tuning

### 5. Treinamento e Validação
- Definição de hiperparâmetros (learning rate, optimizer, batch size, epochs)
- Monitoramento de overfitting através das curvas de loss/accuracy

### 6. Experimentação e Avaliação de Resultados
- Teste cego do modelo no conjunto de teste
- Cálculo de métricas: acurácia, precisão, recall, F1-score (macro e per-class)
- Matriz de confusão para análise de intersecções entre estilos

### 7. Análise Qualitativa e de Erros
- Mapeamento visual de acertos com alta confiança
- Mapeamento de falsos positivos e falsos negativos
- Discussão das causas de erro (ambiguidade de estilo, iluminação, pose, fundo)

### 8. Escrita do Artigo Científico (5 seções)
1. Introdução
2. Trabalhos Relacionados (5 a 8 artigos mapeados)
3. Materiais e Métodos (descrição do hardware, software e diagrama do pipeline)
4. Resultados e Discussão (tabelas, gráficos, matriz de confusão e erros)
5. Considerações Finais (conclusão, limitações e trabalhos futuros)

### 9. Entregáveis
- Código-fonte documentado
- Dataset preparado
- Artigo científico no template do evento/disciplina
- Apresentação/demonstração prática do sistema

---

## 4. Estrutura do Artigo Científico (Detalhamento)

1. **Introdução** — Apresentação da relevância da indústria da moda e e-commerce, justificativa para a automação da classificação visual de roupas e especificação do objetivo do projeto.
2. **Trabalhos Relacionados** — Revisão bibliográfica baseada em 5 a 8 artigos da área de Visão Computacional aplicada à moda, destacando o diferencial da proposta (dataset próprio com filtragem automática por detecção humana).
3. **Materiais e Métodos** — Descrição do ambiente computacional, técnicas de raspagem, critérios de rotulação, pipeline de pré-processamento, arquiteturas neurais comparadas e estratégia experimental.
4. **Resultados e Discussão** — Exposição quantitativa das métricas de desempenho, comparação entre modelos/pré-processamentos, matriz de confusão e análise detalhada dos casos de erro.
5. **Considerações Finais** — Síntese das conclusões alcançadas, resposta à pergunta central do trabalho, identificação de limitações e sugestões de evoluções futuras.
