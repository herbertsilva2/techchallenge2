import streamlit as st
import re

# ==========================================
# Configuração da Página
# ==========================================
st.set_page_config(
    page_title="Dashboard - Roteamento Médico Especializado",
    page_icon="🚑",
    layout="wide"
)


# ==========================================
# Função para Processar o Ficheiro TXT
# ==========================================
def processar_roteiro(caminho_ficheiro):
    """Lê e estrutura os dados do ficheiro gerado pela LLM."""
    try:
        with open(caminho_ficheiro, "r", encoding="utf-8") as f:
            conteudo = f.read()
    except FileNotFoundError:
        st.error(f"Ficheiro '{caminho_ficheiro}' não encontrado. Por favor, execute primeiro a otimização de rotas.")
        return None, None

    # Extrair as paragens usando expressões regulares
    padrao_paragem = r"(\d+º Parada:.*?)(?=\n\n\d+º Parada:|\n\n=========================================================)"
    paragens_raw = re.findall(padrao_paragem, conteudo, re.DOTALL)

    paragens_estruturadas = []

    for bloco in paragens_raw:
        # Extrair dados de cada bloco
        match_numero_ra = re.search(r"(\d+)º Parada: (.+)", bloco)
        match_tipo = re.search(r"- Tipo de Atendimento: (.+)", bloco)
        match_acao = re.search(r"- \[AÇÃO LLM\]: (.+)", bloco)

        if match_numero_ra and match_tipo and match_acao:
            # Combinar ação com linhas seguintes se existirem
            acao = match_acao.group(1).strip()
            # Procurar se há texto adicional na ação LLM na linha seguinte (como os 15 min de paragem)
            linhas_bloco = bloco.split('\n')
            for i, linha in enumerate(linhas_bloco):
                if "- [AÇÃO LLM]:" in linha and i + 1 < len(linhas_bloco):
                    proxima_linha = linhas_bloco[i + 1].strip()
                    if proxima_linha and not proxima_linha.startswith("-"):
                        acao += " " + proxima_linha

            paragens_estruturadas.append({
                "ordem": int(match_numero_ra.group(1)),
                "ra": match_numero_ra.group(2).strip(),
                "tipo": match_tipo.group(1).strip(),
                "acao_llm": acao
            })

    return paragens_estruturadas


# ==========================================
# Construção do Dashboard
# ==========================================
st.title("🚑 Painel Operacional: Saúde da Mulher no DF")
st.markdown("---")

dados_roteiro = processar_roteiro("roteiro_equipe_llm.txt")

if dados_roteiro:
    # 1. Secção de Métricas Resumo
    st.subheader("📊 Resumo da Rota Otimizada")
    col1, col2, col3, col4 = st.columns(4)

    total_paragens = len(dados_roteiro)
    total_emergencias = sum(1 for p in dados_roteiro if "Emergência" in p['tipo'])
    total_violencia = sum(1 for p in dados_roteiro if "violência doméstica" in p['tipo'])
    total_hormonais = sum(1 for p in dados_roteiro if "hormonais" in p['tipo'])

    with col1:
        st.metric(label="Total de Paragens", value=total_paragens)
    with col2:
        st.metric(label="Emergências Obstétricas", value=total_emergencias, delta="Prioridade Alta",
                  delta_color="inverse")
    with col3:
        st.metric(label="Casos Violência Doméstica", value=total_violencia)
    with col4:
        st.metric(label="Entregas Medicamentos", value=total_hormonais)

    st.markdown("---")

    # 2. Secção do Roteiro Detalhado com LLM
    st.subheader("📋 Roteiro Detalhado de Atendimentos")
    st.info("As instruções abaixo foram geradas automaticamente para guiar a equipa em cada contexto específico.")

    # Adicionar um filtro opcional
    tipo_filtro = st.selectbox(
        "Filtrar por Tipo de Atendimento:",
        options=["Todos"] + list(set([p['tipo'] for p in dados_roteiro]))
    )

    # Mostrar as paragens usando caixas expansíveis (expanders)
    for parada in dados_roteiro:
        if tipo_filtro == "Todos" or parada['tipo'] == tipo_filtro:

            # Definir a cor/ícone baseado na prioridade
            icone = "📍"
            cor_destaque = "normal"
            if "Emergência" in parada['tipo']:
                icone = "🚨"
                cor_destaque = "error"
            elif "violência" in parada['tipo']:
                icone = "🛡️"
                cor_destaque = "warning"
            elif "hormonais" in parada['tipo']:
                icone = "❄️"
            elif "pós-parto" in parada['tipo']:
                icone = "🍼"

            with st.expander(f"{icone} {parada['ordem']}º Paragem: {parada['ra']} - {parada['tipo']}"):

                # Destacar a mensagem gerada pela LLM
                if cor_destaque == "error":
                    st.error(f"**Instrução da LLM:** {parada['acao_llm']}")
                elif cor_destaque == "warning":
                    st.warning(f"**Instrução da LLM:** {parada['acao_llm']}")
                else:
                    st.success(f"**Instrução da LLM:** {parada['acao_llm']}")

    st.markdown("---")
    st.caption(
        "🤖 *Documento gerado como parte do Tech Challenge Fase 2. A ordem de visita foi otimizada por Algoritmo Genético e as instruções contextuais foram processadas via LLM.*")