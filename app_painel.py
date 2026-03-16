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

# Dividir os dados para as duas equipes
meio = len(dados_roteiro) // 2
equipe_azul = dados_roteiro[:meio]
equipe_laranja = dados_roteiro[meio:]


# Função auxiliar para gerar métricas visuais sem repetir código
def exibir_metricas_equipe(nome_equipe, dados, cor):
    st.markdown(f"<h4 style='color: {cor};'>{nome_equipe}</h4>", unsafe_allow_html=True)

    total_paradas = len(dados)
    total_emergencias = sum(1 for p in dados if "Emergências" in p["tipo"])
    total_violencia = sum(1 for p in dados if "violência" in p["tipo"].lower())
    total_hormonios = sum(1 for p in dados if "hormonais" in p["tipo"].lower())
    total_rotina = sum(1 for p in dados if "Rotina" in p["tipo"] or "pós-parto" in p["tipo"].lower())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total de Paradas", total_paradas)
    c2.metric("Emergências (Críticas)", total_emergencias, delta="Prioridade 1", delta_color="inverse")
    c3.metric("Casos de Violência", total_violencia)
    c4.metric("Med. Hormonais", total_hormonios)
    c5.metric("Rotina/Pós-parto", total_rotina)


# 1. Métricas Resumo por Equipe
st.subheader("📊 Resumo Operacional da Frota")

exibir_metricas_equipe("🚙 Equipe 1 (Azul)", equipe_azul, "#1f77b4")
st.markdown("<br>", unsafe_allow_html=True)  # Espaçamento elegante
exibir_metricas_equipe("🚑 Equipe 2 (Laranja)", equipe_laranja, "#ff7f0e")

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
# 4. Roteiro Detalhado com LLM (DIVIDIDO POR EQUIPES)
# ==========================================
st.subheader("📋 Roteiro Detalhado de Atendimento por Equipe")

# Filtro de Prioridade
filtro_tipo = st.selectbox(
    "🔍 Filtrar paradas por prioridade médica:",
    ["Todas as Paradas", "Emergências obstétricas", "Violência doméstica", "Medicamentos hormonais",
     "Pós-parto / Rotina"]
)

# Divide a lista de paradas exatamente ao meio, igual fizemos no mapa GPS
meio = len(dados_roteiro) // 2
equipe_azul = dados_roteiro[:meio]
equipe_laranja = dados_roteiro[meio:]


def filtrar_dados(dados):
    if filtro_tipo == "Emergências obstétricas":
        return [p for p in dados if "Emergências" in p["tipo"]]
    elif filtro_tipo == "Violência doméstica":
        return [p for p in dados if "violência" in p["tipo"].lower()]
    elif filtro_tipo == "Medicamentos hormonais":
        return [p for p in dados if "hormonais" in p["tipo"].lower()]
    elif filtro_tipo == "Pós-parto / Rotina":
        return [p for p in dados if "Rotina" in p["tipo"] or "pós-parto" in p["tipo"].lower()]
    return dados


azul_filtrado = filtrar_dados(equipe_azul)
laranja_filtrado = filtrar_dados(equipe_laranja)

st.markdown(f"Mostrando **{len(azul_filtrado) + len(laranja_filtrado)}** parada(s) no total com esta classificação.")

# Inicializar o cliente do Gemini
client = None
try:
    # Se você já configurou o st.secrets, ele puxa de lá. Se não, ponha a chave na string abaixo.
    if "GEMINI_API_KEY" in st.secrets:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        CHAVE_API_STREAMLIT = "COLOQUE_AQUI_A_SUA_CHAVE_NOVA"
        client = genai.Client(api_key=CHAVE_API_STREAMLIT)
except:
    pass

# Criar duas colunas visuais no Streamlit (Lado a Lado)
col1, col2 = st.columns(2)


def desenhar_cards(dados_equipe, coluna, nome_equipe, cor_hex, icone_veiculo):
    with coluna:
        st.markdown(f"<h4 style='color: {cor_hex};'>{icone_veiculo} {nome_equipe} ({len(dados_equipe)} paradas)</h4>",
                    unsafe_allow_html=True)
        for parada in dados_equipe:
            icone = "🟢"
            if "Emergências" in parada["tipo"]:
                icone = "🔴"
            elif "violência" in parada["tipo"].lower():
                icone = "🟠"
            elif "hormonais" in parada["tipo"].lower():
                icone = "🔵"

            with st.expander(f"{icone} Parada {parada['ordem']}: {parada['ra']} - {parada['tipo']}"):
                st.write(f"**🛣️ Trajeto:** {parada['deslocamento']}")
                st.write(f"**📌 Protocolo Padrão:** {parada['acao']}")

                # Botão do Gemini
                if st.button(f"✨ Gerar Protocolo com IA", key=f"btn_{parada['ordem']}_{parada['ra']}"):
                    if client:
                        with st.spinner("A IA está analisando os protocolos médicos..."):
                            try:
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


# Desenha as informações nas respectivas colunas
desenhar_cards(azul_filtrado, col1, "Equipe 1 (Azul)", "#1f77b4", "🚙")
desenhar_cards(laranja_filtrado, col2, "Equipe 2 (Laranja)", "#ff7f0e", "🚑")

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
        # TENTA USAR O GEMINI
        client = None
        if "GEMINI_API_KEY" in st.secrets:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

        # 1. Separar as listas para a IA entender a divisão da frota
        meio_lista = len(dados_roteiro) // 2
        rota_azul = ", ".join([f"{p['ra']} ({p['tipo']})" for p in dados_roteiro[:meio_lista]])
        rota_laranja = ", ".join([f"{p['ra']} ({p['tipo']})" for p in dados_roteiro[meio_lista:]])

        # 2. Engenharia de Prompt: Explicar o cenário logístico completo
        prompt_chat = (
            f"Você é o assistente logístico chefe de uma frota médica. "
            f"Temos duas ambulâncias em campo hoje.\n"
            f"A rota da Equipe Azul é: {rota_azul}.\n"
            f"A rota da Equipe Laranja é: {rota_laranja}.\n\n"
            f"Com base apenas nestes dados, responda de forma curta, direta e amigável à pergunta: '{pergunta}'"
        )

        resposta_ia = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_chat
        )

        resposta_final = f"☁️ **IA Online:** {resposta_ia.text}"

    except Exception as e:
        # Opcional: st.error(f"Falha na API do Google: {e}")

        # --- ADICIONE ESTAS 3 LINHAS AQUI PARA O CHATBOT VOLTAR A FUNCIONAR ---
        total_emergencias = sum(1 for p in dados_roteiro if "Emergências" in p["tipo"])
        total_violencia = sum(1 for p in dados_roteiro if "violência" in p["tipo"].lower())
        total_hormonios = sum(1 for p in dados_roteiro if "hormonais" in p["tipo"].lower())
        # ----------------------------------------------------------------------

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
            resposta_final = f"🔌 **Modo Offline Ativo**. No momento, só consigo informar sobre: **emergências, primeira parada, violência ou medicamentos**."

    with st.chat_message("assistant"):
        st.markdown(resposta_final)
    st.session_state.mensagens.append({"role": "assistant", "content": resposta_final})