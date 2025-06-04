# Documentação Técnica do Pacote `agents.scrapers`

Este documento fornece uma visão geral técnica dos módulos de scraping encontrados no pacote `agents.scrapers`. Cada scraper é responsável por extrair informações de eventos culturais, museus ou outras atividades de fontes web específicas.

---

## `__init__.py`

### Propósito
Este arquivo marca o diretório `scrapers/` como um pacote Python. Isso permite que os módulos de scraper individuais sejam importados usando a sintaxe de pacote (por exemplo, `from agents.scrapers import fablab_scraper`).

### Conteúdo Principal
- O arquivo contém um comentário indicando sua finalidade. Este conteúdo é suficiente para sua função como inicializador de pacote.

### Exports
- N/A (não define `__all__` e não tem código funcional para exportar).

---

## `fablab_scraper.py`

### Propósito
Este módulo implementa um scraper para extrair informações sobre cursos e eventos do site FabLab Livre SP (`www.fablablivresp.prefeitura.sp.gov.br`). Ele navega pela página de busca de cursos e coleta detalhes sobre cada evento listado.

### Principais Componentes

1.  **`scrape_fablab_events() -> List[Dict[str, Any]]`**:
    *   **Propósito**: Função principal que orquestra o processo de scraping.
    *   **Funcionamento**:
        *   Faz uma requisição HTTP GET para a `FABLAB_URL` (página de busca de cursos).
        *   Parseia o HTML da resposta usando `BeautifulSoup`.
        *   Identifica os "cards" de eventos na página usando uma lista de seletores CSS (`SELECTORS['event_cards']`).
        *   Para cada card, chama funções auxiliares para extrair título, link, data, hora, localização e categorias.
        *   Formata os dados extraídos em um dicionário para cada evento e os adiciona a uma lista.
    *   **Retorno**: Uma lista de dicionários, onde cada dicionário representa um evento e contém chaves como `id`, `name`, `location_details`, `type`, `date_info`, `time_info`, `details_link`, `source`, `description`.
    *   **Tratamento de Erros**: Registra erros durante a requisição HTTP ou parsing e retorna uma lista vazia em caso de falha.

2.  **Funções Auxiliares (`_extract_title_and_link`, `_extract_datetime`, `_extract_location`, `_extract_categories`)**:
    *   **Propósito**: Responsáveis por extrair pedaços específicos de informação de um elemento HTML (`card`) do evento.
    *   **Funcionamento**: Utilizam seletores CSS e heurísticas para encontrar os dados relevantes dentro da estrutura HTML do card. Possuem lógicas de fallback para tentar diferentes métodos de extração caso a estrutura da página varie.

### Dependências Chave
-   `requests`: Para realizar requisições HTTP.
-   `BeautifulSoup4` (bs4): Para parsear o conteúdo HTML.
-   `sys`, `os`: Para manipulação de caminhos (para importação do logger).
-   `logging` (através de `utils.logger`): Para registrar informações e erros durante o processo.

### Configuração e Uso
-   **`FABLAB_URL`**: Constante que define a URL base para a busca de cursos.
-   **`FABLAB_BASE_URL`**: Constante para construir URLs absolutas a partir de links relativos.
-   **`SELECTORS`**: Dicionário de seletores CSS usados para encontrar elementos específicos na página. Pode precisar de atualização se a estrutura do site FabLab mudar.
-   O scraper é projetado para ser chamado pela função `scrape_fablab_events()`.

### Bloco de Testes (`if __name__ == '__main__':`)
-   O módulo inclui um bloco de execução que chama `scrape_fablab_events()` e imprime os detalhes dos primeiros eventos encontrados, permitindo testar o scraper de forma isolada.

### Exports
-   A principal função exportada implicitamente (por não ter `__all__`) é `scrape_fablab_events`.

---

## `wikipedia_museus_scraper.py`

### Propósito
Este módulo é responsável por extrair uma lista de museus da cidade de São Paulo a partir de uma página específica da Wikipédia (`pt.wikipedia.org/wiki/Lista_de_museus_da_cidade_de_S%C3%A3o_Paulo`). Ele parseia a tabela de museus contida na página.

### Principais Componentes

1.  **`scrape_wikipedia_museus_info() -> List[Dict[str, Any]]`**:
    *   **Propósito**: Função principal que realiza o scraping da página da Wikipédia.
    *   **Funcionamento**:
        *   Faz uma requisição HTTP GET para a `WIKIPEDIA_MUSEUS_URL` com headers customizados.
        *   Parseia o HTML usando `BeautifulSoup`.
        *   Encontra a tabela de museus (classe `wikitable sortable`).
        *   Itera sobre as linhas da tabela (pulando o cabeçalho).
        *   Para cada linha, chama `_extract_museum_info` para extrair nome e distrito do museu.
    *   **Retorno**: Uma lista de dicionários, onde cada dicionário representa um museu com as chaves `title` (nome do museu), `district` (distrito onde se localiza) e `source_site`.
    *   **Tratamento de Erros**: Registra erros e retorna uma lista vazia se a URL não puder ser acessada ou a tabela não for encontrada.

2.  **`_extract_museum_info(cols: List) -> Optional[Dict[str, Any]]`**:
    *   **Propósito**: Extrai o nome e o distrito de um museu a partir das colunas (`<td>`) de uma linha da tabela.
    *   **Funcionamento**: Acessa o texto da segunda coluna (nome) e da terceira coluna (distrito).
    *   **Retorno**: Um dicionário com os dados do museu ou `None` se a extração falhar.

### Dependências Chave
-   `requests`: Para requisições HTTP.
-   `BeautifulSoup4` (bs4): Para parsing de HTML.
-   `sys`, `os`: Para manipulação de caminhos (importação do logger).
-   `logging` (através de `utils.logger`): Para logging.

### Configuração e Uso
-   **`WIKIPEDIA_MUSEUS_URL`**: URL da página da Wikipédia a ser scrapeada.
-   **`HEADERS`**: Cabeçalhos HTTP para simular um navegador.
-   A função `scrape_wikipedia_museus_info()` é o ponto de entrada.

### Bloco de Testes (`if __name__ == '__main__':`)
-   Permite executar o scraper isoladamente, imprimindo o número de museus encontrados e os detalhes dos primeiros cinco.

### Exports
-   A função principal exportada é `scrape_wikipedia_museus_info`.

---

## `visite_sao_paulo_scraper.py`

### Propósito
Este scraper extrai informações de eventos do site Visite São Paulo (`visitesaopaulo.com`), focando na seção "Calendário de Eventos".

### Principais Componentes

1.  **`scrape_visite_sao_paulo_events() -> List[Dict[str, Any]]`**:
    *   **Propósito**: Função principal que executa o scraping.
    *   **Funcionamento**:
        *   Faz uma requisição HTTP GET para a `EVENTS_URL`.
        *   Parseia o HTML com `BeautifulSoup`.
        *   Encontra todos os elementos `<h3>`, que são assumidos como possíveis títulos de eventos.
        *   Para cada `<h3>`, tenta extrair:
            *   Título do evento.
            *   Data: procura nos elementos irmãos seguintes (`<p>`, `<span>`, `<div>`) por texto que corresponda a um padrão de data.
            *   Link oficial do evento: procura por links (`<a>`) com texto "detalhes" ou verifica se o elemento pai é um link.
            *   Categoria: tenta inferir a partir do `<h2>` anterior ao `<h3>`.
        *   Armazena os dados em um dicionário se informações mínimas (título, link, data) forem encontradas.
    *   **Retorno**: Uma lista de dicionários, cada um representando um evento com chaves como `title`, `description`, `date`, `time`, `location`, `category`, `official_event_link`, `source_site`.
    *   **Tratamento de Erros**: Registra erros durante a requisição ou parsing e continua para o próximo elemento se possível.

2.  **Funções Auxiliares (`_extract_date_from_text`, `_find_details_link`, `_find_section_category`)**:
    *   **`_extract_date_from_text(text: str) -> str`**: Tenta extrair uma data de uma string usando regex e verificação de padrões textuais.
    *   **`_find_details_link(element: BeautifulSoup) -> str`**: Procura por um link de "detalhes" em um elemento ou em seus pais.
    *   **`_find_section_category(h3_element: BeautifulSoup) -> str`**: Tenta encontrar o título da seção (`<h2>`) que precede o título do evento (`<h3>`) para usar como categoria.

### Dependências Chave
-   `requests`: Para requisições HTTP.
-   `BeautifulSoup4` (bs4): Para parsing de HTML.
-   `urllib.parse.urljoin`: Para construir URLs absolutas.
-   `re`: Para correspondência de padrões em datas.
-   `sys`, `os`: Para manipulação de caminhos (importação do logger).
-   `logging` (através de `utils.logger`): Para logging.

### Configuração e Uso
-   **`BASE_URL`**: URL base do site Visite São Paulo.
-   **`EVENTS_URL`**: URL específica da página de calendário de eventos.
-   **`HEADERS`**: Cabeçalhos HTTP.
-   A função `scrape_visite_sao_paulo_events()` é o ponto de entrada.

### Bloco de Testes (`if __name__ == '__main__':`)
-   Executa o scraper e imprime os eventos encontrados, facilitando testes isolados.

### Exports
-   A função principal exportada é `scrape_visite_sao_paulo_events`.

---
