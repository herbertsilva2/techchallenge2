# 🚑 Otimização de Roteamento Especializado: Saúde da Mulher (DF)

Este projeto foi desenvolvido como parte do **Tech Challenge (Fase 2)** e propõe uma solução logística avançada para o atendimento médico domiciliar e distribuição de medicamentos voltados à saúde da mulher no Distrito Federal.

O sistema resolve um problema complexo de **Roteamento de Veículos Múltiplos (m-VRP)** utilizando um **Algoritmo Genético** criado do zero. Além da otimização matemática, o projeto conta com um Dashboard Interativo e integração com Inteligência Artificial (Google Gemini) para apoiar as equipes médicas em tempo real.

---

## ✨ Principais Funcionalidades

* **🧬 Algoritmo Genético Avançado:** Utiliza técnicas de Elitismo, Seleção por Truncamento e *Order Crossover (OX)* para otimizar rotas de forma rápida e eficiente, fugindo de mínimos locais.
* **🚑 Frota Multi-Veículos (m-VRP):** O sistema divide o atendimento de 35 Regiões Administrativas (RAs) em duas frentes de trabalho simultâneas e balanceadas:
  * 🚙 **Equipe 1 (Azul):** Cobre a primeira metade da rota otimizada.
  * 🚑 **Equipe 2 (Laranja):** Cobre a segunda metade da rota otimizada.
* **⚖️ Restrições Médicas Reais (Fitness Function):** O algoritmo é penalizado matematicamente caso não respeite prioridades rígidas:
  1. *Emergências Obstétricas* (Prioridade Máxima).
  2. *Violência Doméstica* (Protocolos Especiais de discrição).
  3. *Medicamentos Hormonais* (Limite de distância percorrida para garantir refrigeração entre 2°C e 8°C).
  4. *Consultas de Rotina e Pós-parto* (Penalidade por atraso na janela de tempo).
* **🖥️ Simulação Visual (Pygame):** Interface em Fullscreen que exibe a evolução da Inteligência Artificial em tempo real, construindo os roteiros no mapa do DF e traçando o gráfico de evolução do custo (Step Chart).
* **📊 Dashboard Analítico (Streamlit):** Painel operacional para a coordenação médica visualizar as métricas de cada equipe lado a lado, além de um mapa interativo com rotas reais de GPS (via API OSRM e Folium).
* **🧠 Inteligência Artificial Generativa (Gemini 2.5 Flash):** Geração dinâmica de protocolos de atendimento e condutas médicas na hora, baseadas na localização e no tipo de emergência enfrentada pelas equipes (com fallback offline para áreas sem internet).

---

## 🛠️ Tecnologias Utilizadas

* **Python 3.9+**
* **Pygame:** Simulação gráfica do Algoritmo Genético.
* **Streamlit:** Criação do Dashboard Web Analítico.
* **Google GenAI (`google-genai`):** Integração com o LLM Gemini 2.5 Flash.
* **Folium & Requests:** Renderização de mapas interativos e requisições de rotas reais.
* **Pandas & CSV:** Manipulação e exportação de dados analíticos.

---

## ⚙️ Instalação e Configuração

### 1. Clonar o repositório
```bash
git clone https://github.com/herbertsilva2/techchallenge2.git
cd techchallenge2
```

### 2. Instalar as dependências
Recomenda-se o uso de um ambiente virtual (venv).

```bash
pip install pygame streamlit folium requests pandas google-genai
```

### 3. Configurar a Chave da API do Google Gemini (Segurança)
Para que os recursos de Inteligência Artificial funcionem no Dashboard **sem expor a sua chave pública no GitHub**, configure os "Secrets" do Streamlit:

1. Na raiz do projeto, crie uma pasta chamada `.streamlit` (com o ponto no início).
2. Dentro dessa pasta, crie um arquivo chamado `secrets.toml`.
3. Adicione a sua chave dentro do arquivo da seguinte forma:

```toml
GEMINI_API_KEY = "SUA_CHAVE_AQUI_AIzaSy..."
```
## 🚀 Como Executar o Projeto

Todo o fluxo de dados entre o Algoritmo Genético e o Dashboard está automatizado. Para iniciar:

1. Execute o simulador de otimização matemática:
```bash
python tsp.py
```
**Importante:** Acompanhe a evolução das rotas das duas equipes no mapa. Quando o algoritmo estabilizar (o gráfico formar uma linha reta no fundo), pressione a tecla `Q` no seu teclado.

Ao pressionar `Q`, o sistema irá:
* Exportar os dados de fitness (`.csv`).
* Gerar os relatórios de atendimento e divisão de equipes (`.txt`).
* Traçar as rotas reais de rua no mapa GPS (`.html`).
* **Abrir automaticamente o Dashboard interativo no seu navegador principal!**

*(Nota: Caso deseje fechar a simulação prematuramente sem salvar os dados ou gerar o Dashboard, pressione `ESC`).*

## 📁 Estrutura de Ficheiros

* `tsp.py`: Motor principal que executa a interface Pygame e a função de fitness (VRP).
* `genetic_algorithm.py`: Módulo matemático contendo as funções de *Crossover*, Mutação e População.
* `app_painel.py`: Código-fonte do Dashboard operacional construído em Streamlit.
* `benchmark_att35.py`: Dicionário com as coordenadas relativas das Regiões Administrativas do Distrito Federal.
* `mapa_df.png`: Imagem base utilizada na simulação gráfica do Pygame.