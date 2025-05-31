# Agente Cultural Inteligente de São Paulo

## Overview

O Agente Cultural Inteligente de São Paulo é um projeto de IA generativa projetado para ajudar os usuários a descobrir eventos culturais, oficinas, exposições e outras atividades acontecendo na cidade de São Paulo. Ele combina raspagem de dados de várias fontes, integração com o Google Maps para geolocalização e uma interface de chat interativa construída com Streamlit e o Agent Development Kit (ADK) do Google.

O objetivo principal é fornecer uma maneira centralizada e fácil de usar para explorar a vibrante cena cultural de São Paulo.

## Features

- **Raspagem de Eventos (Event Scraping):** Coleta dados de eventos de diversas fontes online.
  - Atualmente implementado para FabLab Livre SP (dados reais).
  - Raspador para Cultura SP (Secretaria Municipal de Cultura) está atualmente em modo mock due à complexidade do site (heavy JavaScript).
- **Integração com Google Maps:**
  - Geocodificação de endereços de eventos para obter coordenadas (latitude/longitude).
  - Busca de detalhes de locais (a ser totalmente integrado na interface).
- **Agente Conversacional (ADK):**
  - Lógica de agente definida usando o Agent Development Kit (ADK), atualmente com handlers mock para:
    - Boas-vindas.
    - Busca de eventos por tipo e data.
    - Busca de eventos por proximidade (localização textual).
- **Interface Web Interativa (Streamlit):**
  - Interface amigável para visualizar eventos, aplicar filtros e interagir com o agente.
  - Exibição de eventos em formato de "cards".
  - Mapa interativo para visualização de eventos geolocalizados.
- **Filtragem de Eventos:**
  - Filtros por tipo de evento (categoria), data e busca textual por localização.
- **Chat com o Agente:**
  - Interface de chat na barra lateral para interagir com o agente cultural usando linguagem natural (atualmente processado por um dispatcher mock).

## Project Structure

```
.
├── agents/               # Lógica do Agente Conversacional (ADK)
│   └── cultural_agent.py
├── interface/            # Interface do usuário Streamlit
│   └── app.py
├── scrapers/             # Scripts de raspagem de dados (web scrapers)
│   ├── fablab_scraper.py
│   └── cultura_sp_scraper.py (atualmente mock)
├── tests/                # Testes unitários
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_scrapers.py
│   └── test_utils.py
├── utils/                # Módulos utilitários (config, maps, logger)
│   ├── config.py
│   ├── logger.py
│   └── maps.py
├── config.yaml           # Arquivo de configuração (chaves de API, etc.)
├── requirements.txt      # Dependências do projeto Python
└── README.md             # Este arquivo
```

- **`agents/`**: Contém a lógica do agente conversacional construído com o ADK, incluindo handlers de intenção.
- **`interface/`**: Código da interface do usuário web desenvolvida com Streamlit.
- **`scrapers/`**: Scripts responsáveis por extrair dados de eventos de diferentes sites.
- **`tests/`**: Testes unitários para garantir a qualidade e o correto funcionamento dos componentes.
- **`utils/`**: Módulos utilitários usados em todo o projeto, como carregamento de configuração, integração com Google Maps e logging.

## Setup Instructions

### 1. Python Version
Este projeto requer Python 3.11 ou superior.

### 2. Virtual Environment (Recomendado)
É altamente recomendável criar e ativar um ambiente virtual para isolar as dependências do projeto:
```bash
python3 -m venv .venv
source .venv/bin/activate  # No Linux/macOS
# Ou .venv\Scripts\activate   # No Windows
```

### 3. Instalar Dependências
Instale todas as dependências listadas no arquivo `requirements.txt`:
```bash
pip install -r requirements.txt
```
Se você planeja usar o Playwright para raspagem de dados (por exemplo, para uma futura implementação do scraper Cultura SP), você também precisará instalar os navegadores para o Playwright:
```bash
python -m playwright install --with-deps chromium
```

### 4. API Key Configuration
Este projeto utiliza APIs do Google Maps, que requerem uma chave de API.

- **Localize o arquivo `config.yaml`** na raiz do projeto.
- **Edite o arquivo `config.yaml`** e adicione sua chave de API do Google Maps:
  ```yaml
  api_keys:
    google_maps: "SUA_CHAVE_DE_API_DO_GOOGLE_MAPS_AQUI"
    # Outras chaves, como para Google Cloud (para um ADK deployado), podem ser adicionadas aqui.
  ```
- **Importante:** Certifique-se de que a chave de API do Google Maps tenha as APIs "Geocoding API" e "Places API" ativadas no Google Cloud Console.
- **Não compartilhe sua chave de API publicamente nem a envie para sistemas de controle de versão.**

## Running the Application

Para iniciar a interface do usuário Streamlit:
```bash
streamlit run interface/app.py
```
A aplicação deverá abrir em seu navegador web.

## Running Tests

Para executar todos os testes unitários, navegue até o diretório raiz do projeto e execute:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

**Nota sobre Testes no Ambiente de Desenvolvimento Fornecido:**
Ao executar testes individuais (ex: `python tests/test_scrapers.py`) no ambiente de desenvolvimento específico desta ferramenta, foi observado um problema de timeout (aproximadamente 400s). Isso parece ser um artefato do ambiente de execução com o `unittest` ou scripts que produzem saída no console, e não necessariamente um erro nos testes em si. A execução via `python -m unittest discover` pode se comportar de maneira diferente e é a forma recomendada para rodar a suíte de testes.

## Future Improvements

- **Deployment do Agente ADK:** Publicar o agente ADK em uma plataforma como o Google Cloud para permitir interações via Dialogflow CX ou similar.
- **Raspador Avançado para Cultura SP:** Reimplementar o scraper `cultura_sp_scraper.py` usando Playwright para lidar com o conteúdo carregado dinamicamente via JavaScript.
- **Geocodificação e Filtro de Proximidade:**
    - Implementar a geocodificação dos endereços dos eventos FabLab.
    - Adicionar filtro de proximidade real (ex: eventos dentro de um raio de X km de um ponto/endereço geocodificado).
- **Cache de Raspagem:** Implementar caching para os dados raspados para reduzir a carga nos sites de origem e acelerar o carregamento da interface.
- **Processamento de Linguagem Natural (PLN) Avançado:** Melhorar o dispatcher de intenções no Streamlit ou integrar com o NLU do ADK/Dialogflow CX de forma mais robusta.
- **Interface do Usuário Aprimorada:** Melhorar os cards de eventos, adicionar mais opções de visualização e filtros.
- **Persistência de Dados:** Salvar eventos em um banco de dados para análise histórica e para evitar raspagem excessiva.
- **Cobertura de Testes:** Expandir a cobertura dos testes unitários.
- **Logging Detalhado:** Aprimorar a configuração de logging para diferentes ambientes (dev, prod).

```
