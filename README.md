# 🚑 Sistema de Roteamento Dinâmico de Equipes Médicas - Saúde da Mulher (DF)

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![GenAI](https://img.shields.io/badge/Google%20Gemini-LLM-orange)

## 📌 Sobre o Projeto
Este projeto foi desenvolvido como parte do **Tech Challenge (Fase 2)**. O objetivo é otimizar a logística de atendimento médico especializado em Saúde da Mulher no Distrito Federal, abrangendo 35 Regiões Administrativas (RAs).

O desafio transcende o clássico Problema do Caixeiro Viajante (TSP), evoluindo para um **Problema de Roteamento de Veículos (VRP) com Restrições**. O sistema não busca apenas a rota mais curta, mas a rota mais eficiente e segura, respeitando prioridades médicas rígidas.

## 🚀 Principais Funcionalidades

1. **Algoritmo Genético Customizado (VRP):** - População evolutiva com taxas de mutação e crossover.
   - **Função de Fitness com Penalidades:** O algoritmo é penalizado caso não priorize Urgências Obstétricas, se ultrapassar o limite diário de distância do veículo, ou se violar o tempo máximo de transporte para medicamentos hormonais refrigerados.
2. **Integração com LLM (Inteligência Artificial Generativa):**
   - Utilização de engenharia de prompt para processar a rota matemática e gerar um "Manual de Instruções" contextualizado para a equipe da ambulância.
   - O sistema gera alertas de urgência, protocolos de discrição (violência doméstica) e cuidados de temperatura.
3. **Dashboard Gerencial (Streamlit):**
   - Painel interativo com o resumo das métricas diárias, separando os chamados por gravidade.
   - Leitura dinâmica do relatório gerado pela Inteligência Artificial.
4. **Mapeamento Interativo com GPS (Folium + OSRM):**
   - Geração de mapa HTML interativo onde a rota desenhada acompanha o traçado real das ruas e rodovias do DF, com marcação numerada e tooltips informativos.

## 🛠️ Tecnologias Utilizadas
* **Linguagem:** Python 3.13
* **Interface Visual (Evolução do Algoritmo):** Pygame
* **Dashboard:** Streamlit
* **Mapas e Geolocalização:** Folium, API OSRM (Open Source Routing Machine)
* **Inteligência Artificial:** Google Gemini API (com fallback offline para simulação)

## ⚙️ Como Executar o Projeto

**1. Clone o repositório e acesse a pasta:**
```bash
git clone [https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git](https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git)
cd NOME_DO_REPOSITORIO
```
2. Instale as dependências necessárias:
```bash
pip install pygame folium streamlit google-genai requests
```
3. Execute a otimização da rota (Algoritmo Genético):
```bash
python tsp.py
```

Nota: Uma janela do Pygame se abrirá mostrando a evolução da rota. Pressione a tecla Q a qualquer momento 
para interromper a evolução, gerar os relatórios da LLM e fechar o mapa e abrir automaticamente o navegador
exibindo as métricas, os guias de ação da IA e o mapa interativo.

📂 Estrutura de Arquivos

tsp.py: Motor principal do Algoritmo Genético, regras do VRP, integração com a LLM e geração de mapas.

app_painel.py: Aplicação Streamlit que renderiza o painel gerencial.

roteiro_equipe_llm.txt: Arquivo de texto gerado dinamicamente contendo as instruções da IA.

resultado_tsp_mapa.html: Mapa interativo gerado via Folium.