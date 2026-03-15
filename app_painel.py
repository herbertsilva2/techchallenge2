import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from google import genai
import re

# ==========================================
# Configuração da Página
# ==========================================
st.set_page_config(page_title="Dashboard - Saúde da Mulher DF", layout="wide", page_icon="🚑")


# ==========================================
# Função para processar o Roteiro
# ==========================================
def processar_roteiro(caminho_arquivo):
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        conteudo = f.read()

    padrao = r"(\d+)º Parada: (.*?)\n\s+- Tipo de Atendimento: (.*?)\n\s+- Deslocamento Estimado: (.*?)\n\s+- \[AÇÃO LLM\]: (.*?)(?=\n\d+º Parada|\Z)"
    matches = re.findall(padrao, conteudo, re.DOTALL)

    dados_roteiro = []
    for m in matches:
        dados_roteiro.append({
            "ordem": m[0].strip(),
            "ra": m[1].strip(),
            "tipo": m[2].strip(),
            "deslocamento": m[3].strip(),
            "acao": m[4].strip()
        })
    return dados_roteiro


# ==========================================
# Construção do Dashboard
# ==========================================
st.title("🚑 Painel Operacional: Saúde da Mulher no DF")
st.markdown("---")

try:
    dados_roteiro = processar_roteiro("roteiro_equipe_llm.txt")
except FileNotFoundError:
    st.error("Arquivo de roteiro não encontrado. Execute o algoritmo primeiro.")
    st.stop()

# 1. Métricas Resumo
total_paradas = len(dados_roteiro)
total_emergencias = sum(1 for p in dados_roteiro if "Emergências" in p["tipo"])
total_violencia = sum(1 for p in dados_roteiro if "violência" in p["tipo"].lower())
total_hormonios = sum(1 for p in dados_roteiro if "hormonais" in p["tipo"].lower())
total_rotina = sum(1 for p in dados_roteiro if "Rotina" in p["tipo"] or "pós-parto" in p["tipo"].lower())

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total de Paradas (RAs)", total_paradas)
col2.metric("Emergências (Críticas)", total_emergencias, delta="Prioridade 1", delta_color="inverse")
col3.metric("Casos de Violência", total_violencia)
col4.metric("Med. Hormonais", total_hormonios)
col5.metric("Atend. Rotina/Pós-parto", total_rotina)

st.markdown("---")

# 2. Gráfico de Evolução do Fitness (Algoritmo Genético)
st.subheader("📉 Evolução da Rota (Algoritmo Genético)")
try:
    df_fitness = pd.read_csv("fitness_evolution.csv")
    st.line_chart(df_fitness.set_index("Geracao"), color="#ff4b4b")
    st.caption(
        "Este gráfico mostra a otimização da Inteligência Artificial. O custo (distância + multas das restrições VRP) diminui ao longo das gerações.")
except FileNotFoundError:
    st.warning("Ainda não há dados de evolução do fitness.")

st.markdown("---")

# 3. Mapa Folium (GPS Real)
st.subheader("🗺️ Mapa Interativo da Rota (GPS)")
try:
    with open("resultado_tsp_mapa.html", "r", encoding="utf-8") as f:
        mapa_html = f.read()
    components.html(mapa_html, height=500)
except FileNotFoundError:
    st.warning("Mapa interativo ainda não foi gerado.")

st.markdown("---")

# ==========================================
# 4. Roteiro Detalhado com LLM (COM FILTRO E GERAÇÃO DINÂMICA)
# ==========================================
st.subheader("📋 Roteiro Detalhado de Atendimento")

# Filtro de Prioridade alinhado com o documento
filtro_tipo = st.selectbox(
    "🔍 Filtrar paradas por prioridade médica:",
    ["Todas as Paradas", "Emergências obstétricas", "Violência doméstica", "Medicamentos hormonais",
     "Pós-parto / Rotina"]
)

dados_filtrados = dados_roteiro
if filtro_tipo == "Emergências obstétricas":
    dados_filtrados = [p for p in dados_roteiro if "Emergências" in p["tipo"]]
elif filtro_tipo == "Violência doméstica":
    dados_filtrados = [p for p in dados_roteiro if "violência" in p["tipo"].lower()]
elif filtro_tipo == "Medicamentos hormonais":
    dados_filtrados = [p for p in dados_roteiro if "hormonais" in p["tipo"].lower()]
elif filtro_tipo == "Pós-parto / Rotina":
    dados_filtrados = [p for p in dados_roteiro if "Rotina" in p["tipo"] or "pós-parto" in p["tipo"].lower()]

st.markdown(
    f"Mostrando **{len(dados_filtrados)}** parada(s) com esta classificação. Clique para ver as orientações e tempo de viagem.")

# No seu bloco try, chame a chave de forma 100% segura!
CHAVE_API_STREAMLIT = st.secrets["GEMINI_API_KEY"]
client = None
try:
    client = genai.Client(api_key=CHAVE_API_STREAMLIT)
except:
    pass

# Desenha as paradas com o botão interativo de IA
for parada in dados_filtrados:
    icone = "🟢"
    if "Emergências" in parada["tipo"]:
        icone = "🔴"
    elif "violência" in parada["tipo"].lower():
        icone = "🟠"
    elif "hormonais" in parada["tipo"].lower():
        icone = "🔵"

    with st.expander(f"{icone} {parada['ordem']}º Parada: {parada['ra']} - {parada['tipo']}"):
        st.write(f"**🛣️ Trajeto:** {parada['deslocamento']}")
        st.write(f"**📌 Protocolo Padrão (Offline):** {parada['acao']}")

        # O grande diferencial: Botão que chama o Gemini em tempo real!
        if st.button(f"✨ Gerar Protocolo Específico com IA", key=f"btn_{parada['ordem']}_{parada['ra']}"):
            if client:
                with st.spinner("A IA está analisando os protocolos médicos..."):
                    try:
                        # Prompt de Engenharia (Prompt Engineering) exigido no Edital
                        prompt_acao = f"Você é um médico coordenador orientando a equipe de ambulância que acaba de chegar em {parada['ra']} para um caso de: '{parada['tipo']}'. Escreva 3 bullet points curtos, diretos e sensíveis à saúde da mulher, com a conduta médica imediata a ser tomada pela equipe no local."

                        resposta_ia = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt_acao
                        )
                        st.info(f"**🤖 Conduta Médica Gerada pelo Gemini:**\n\n{resposta_ia.text}")
                    except Exception as e:
                        st.error(f"Erro de conexão com a IA: {e}")
            else:
                st.warning("Verifique a sua chave de API para usar esta função.")

# ==========================================
# 5. Assistente Virtual (Híbrido: Nuvem/Offline)
# ==========================================
st.markdown("---")
st.header("💬 Assistente Virtual da Equipe")
st.markdown(
    "Faça perguntas sobre a rota atual (Ex: *'Quantas emergências temos hoje?'*). O sistema possui tolerância a falhas (Fallback Offline).")

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

pergunta = st.chat_input("Pergunte algo sobre a rota...")

if pergunta:
    with st.chat_message("user"):
        st.markdown(pergunta)
    st.session_state.mensagens.append({"role": "user", "content": pergunta})

    resposta_final = ""
    try:
        # No seu bloco try, chame a chave de forma 100% segura!
        CHAVE_API_STREAMLIT = st.secrets["GEMINI_API_KEY"]

        # 1. Cria o Cliente com a sua chave
        client = genai.Client(api_key=CHAVE_API_STREAMLIT)

        resumo_rota = ", ".join([f"{p['ra']} ({p['tipo']})" for p in dados_roteiro])
        prompt_chat = f"Você é o assistente logístico. A rota de hoje tem: {resumo_rota}. Responda de forma curta e amigável: {pergunta}"

        # 2. Chama a geração de conteúdo usando o modelo mais recente!
        resposta_ia = client.models.generate_content(
            model='gemini-2.5-flash',  # <--- MUDE APENAS ESTA LINHA (DE 1.5 PARA 2.5)
            contents=prompt_chat
        )

        resposta_final = f"☁️ **IA Online:** {resposta_ia.text}"

    except Exception as e:

        # VAI MOSTRAR O ERRO REAL A VERMELHO NO ECRÃ PARA SABERMOS O QUE SE PASSA
        st.error(f"Falha na API do Google: {e}")

        # FALLBACK OFFLINE AUTOMÁTICO SE A IA FALHAR
        pergunta_lower = pergunta.lower()
        if "emergência" in pergunta_lower or "emergencia" in pergunta_lower:
            resposta_final = f"🔌 **Modo Offline:** Temos **{total_emergencias} paradas de emergência**. Elas foram alocadas no início da nossa rota!"
        elif "próximo" in pergunta_lower or "primeira" in pergunta_lower:
            primeira = dados_roteiro[0]
            resposta_final = f"🔌 **Modo Offline:** A primeira parada será em **{primeira['ra']}** ({primeira['tipo']})."
        elif "violência" in pergunta_lower or "violencia" in pergunta_lower:
            resposta_final = f"🔌 **Modo Offline:** Temos **{total_violencia} casos** de violência doméstica na rota. Mantenha a discrição."
        elif "hormon" in pergunta_lower or "medicamento" in pergunta_lower:
            resposta_final = f"🔌 **Modo Offline:** Temos **{total_hormonios} entregas de medicamentos**. Mantenha a caixa refrigerada."
        else:
            resposta_final = f"🔌 **Modo Offline Ativo**. No momento, só consigo informar sobre: **emergências, primeira parada, violência ou medicamentos**. Pergunte, por exemplo, 'Quantas emergências?'"

    with st.chat_message("assistant"):
        st.markdown(resposta_final)
    st.session_state.mensagens.append({"role": "assistant", "content": resposta_final})