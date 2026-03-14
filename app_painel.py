import streamlit as st
import re
import pandas as pd

# ==========================================
# Configuração da Página
# ==========================================
st.set_page_config(
    page_title="Dashboard - Roteamento Médico Especializado",
    page_icon="🚑",
    layout="wide"
)


# ==========================================
# Função ROBUSTA para Processar o Ficheiro TXT
# ==========================================
def processar_roteiro(caminho_ficheiro):
    paradas = []
    try:
        with open(caminho_ficheiro, "r", encoding="utf-8") as f:
            linhas = f.readlines()
    except FileNotFoundError:
        st.error(f"Ficheiro '{caminho_ficheiro}' não encontrado. Execute o tsp.py primeiro.")
        return []

    parada_atual = {}
    acao_coletando = False

    for linha in linhas:
        linha_limpa = linha.strip()

        # 1. Identifica o início de uma nova parada (Ex: "1º Parada: Sudoeste")
        match_parada = re.match(r"(\d+)º Parada:\s*(.+)", linha_limpa)
        if match_parada:
            # Salva a parada anterior na lista antes de começar a nova
            if 'ordem' in parada_atual and 'acao_llm' in parada_atual:
                paradas.append(parada_atual)

            parada_atual = {
                "ordem": int(match_parada.group(1)),
                "ra": match_parada.group(2).strip(),
                "tipo": "Não especificado",
                "acao_llm": ""
            }
            acao_coletando = False
            continue

        # 2. Identifica o Tipo de Atendimento
        match_tipo = re.match(r"-\s*Tipo de Atendimento:\s*(.+)", linha_limpa)
        if match_tipo and 'ordem' in parada_atual:
            parada_atual['tipo'] = match_tipo.group(1).strip()
            continue

        # 3. Identifica a Ação LLM
        match_acao = re.match(r"-\s*\[AÇÃO LLM\]:\s*(.*)", linha_limpa)
        if match_acao and 'ordem' in parada_atual:
            parada_atual['acao_llm'] = match_acao.group(1).strip()
            acao_coletando = True
            continue

        # 4. Captura texto extra que a IA possa ter atirado para a linha de baixo!
        if acao_coletando and linha_limpa and not linha_limpa.startswith("==") and not linha_limpa.startswith(
                "---") and not linha_limpa.startswith("ORIENTA"):
            parada_atual['acao_llm'] += " " + linha_limpa

    # Salva a última parada que ficou na memória
    if 'ordem' in parada_atual and 'acao_llm' in parada_atual:
        paradas.append(parada_atual)

    return paradas


import streamlit.components.v1 as components

# ==========================================
# Construção do Dashboard
# ==========================================
st.title("🚑 Painel Operacional: Saúde da Mulher no DF")
st.markdown("---")

# --- NOVO BLOCO: ADICIONAR O MAPA FOLIUM ---
st.subheader("🗺️ Mapa Interativo da Rota (GPS)")
try:
    # Lê o arquivo HTML gerado pelo Folium
    with open("resultado_tsp_mapa.html", "r", encoding="utf-8") as f:
        mapa_html = f.read()

    # Exibe o mapa dentro do Streamlit com uma altura de 500 pixels
    components.html(mapa_html, height=500)
except FileNotFoundError:
    st.warning("Mapa interativo ainda não foi gerado. Rode o algoritmo (tsp.py) primeiro.")

st.markdown("---")
# -------------------------------------------

dados_roteiro = processar_roteiro("roteiro_equipe_llm.txt")

if dados_roteiro:
    # 1. Secção de Métricas Resumo
    st.subheader("📊 Resumo da Rota Otimizada")

    # Criamos duas linhas de colunas para caber tudo de forma organizada
    linha1_col1, linha1_col2, linha1_col3 = st.columns(3)
    linha2_col1, linha2_col2, linha2_col3 = st.columns(3)

    total_paradas = len(dados_roteiro)
    total_emergencias = sum(1 for p in dados_roteiro if "Emergência" in p['tipo'] or "Prioridade Máxima" in p['tipo'])
    total_violencia = sum(1 for p in dados_roteiro if "violência" in p['tipo'].lower() or "Protocolos" in p['tipo'])
    total_hormonais = sum(1 for p in dados_roteiro if "hormonais" in p['tipo'].lower() or "Temperatura" in p['tipo'])
    total_pos_parto = sum(1 for p in dados_roteiro if "pós-parto" in p['tipo'].lower())
    total_rotina = sum(1 for p in dados_roteiro if "Rotina" in p['tipo'])

    # Primeira linha de destaques
    with linha1_col1:
        st.metric(label="Total de Paradas (RAs)", value=total_paradas)
    with linha1_col2:
        st.metric(label="🚨 Emergências Obstétricas", value=total_emergencias, delta="Prioridade Alta",
                  delta_color="inverse")
    with linha1_col3:
        st.metric(label="🛡️ Casos Violência Doméstica", value=total_violencia)

    # Segunda linha de destaques
    with linha2_col1:
        st.metric(label="❄️ Entregas Medicamentos", value=total_hormonais)
    with linha2_col2:
        st.metric(label="🍼 Atendimentos Pós-parto", value=total_pos_parto)
    with linha2_col3:
        st.metric(label="📍 Consultas de Rotina", value=total_rotina)

    st.markdown("---")

    # 2. Secção do Roteiro Detalhado com LLM
    st.subheader("📋 Roteiro Detalhado de Atendimentos")
    st.info("As instruções abaixo foram geradas automaticamente para guiar a equipa em cada contexto específico.")

    # Adicionar um filtro opcional
    tipos_disponiveis = list(set([p['tipo'] for p in dados_roteiro]))
    tipo_filtro = st.selectbox(
        "Filtrar por Tipo de Atendimento:",
        options=["Todos"] + tipos_disponiveis
    )

    # Mostrar as paradas usando caixas expansíveis (expanders)
    for parada in dados_roteiro:
        if tipo_filtro == "Todos" or parada['tipo'] == tipo_filtro:

            # Definir a cor/ícone baseado na prioridade
            icone = "📍"
            cor_destaque = "normal"
            if "Emergência" in parada['tipo'] or "Prioridade Máxima" in parada['tipo']:
                icone = "🚨"
                cor_destaque = "error"
            elif "violência" in parada['tipo'].lower() or "Protocolos" in parada['tipo']:
                icone = "🛡️"
                cor_destaque = "warning"
            elif "hormonais" in parada['tipo'].lower() or "Temperatura" in parada['tipo']:
                icone = "❄️"
            elif "pós-parto" in parada['tipo'].lower():
                icone = "🍼"

            with st.expander(f"{icone} {parada['ordem']}º Parada: {parada['ra']} - {parada['tipo']}"):

                # Destacar a mensagem gerada pela LLM
                if cor_destaque == "error":
                    st.error(f"{parada['acao_llm']}")
                elif cor_destaque == "warning":
                    st.warning(f"{parada['acao_llm']}")
                else:
                    st.success(f"{parada['acao_llm']}")

    st.markdown("---")

    # ==========================================
    # NOVO: Gráfico de Evolução do Fitness
    # ==========================================
    import pandas as pd

    st.subheader("📉 Evolução da Rota (Algoritmo Genético)")
    try:
        df_fitness = pd.read_csv("fitness_evolution.csv")
        # O Streamlit cria um gráfico de linha interativo automaticamente!
        st.line_chart(df_fitness.set_index("Geracao"), color="#ff4b4b")
        st.caption(
            "Este gráfico mostra a 'aprendizagem' da Inteligência Artificial. O eixo vertical representa o custo (distância + multas das restrições médicas). Quanto mais baixo, mais otimizada e segura é a rota final.")
    except FileNotFoundError:
        st.warning("Ainda não há dados de evolução do fitness. Execute o tsp.py primeiro.")

    st.markdown("---")

    st.caption(
        "🤖 *Documento gerado como parte do Tech Challenge Fase 2. A ordem de visita foi otimizada por Algoritmo Genético e as instruções contextuais foram processadas via LLM.*")
else:
    st.warning(
        "Não foi possível carregar as paradas. O ficheiro roteiro_equipe_llm.txt pode estar vazio ou com formato incorreto.")