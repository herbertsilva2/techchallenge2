import pygame
from pygame.locals import *
import random
import itertools
from genetic_algorithm import mutate, order_crossover, generate_random_population, calculate_fitness, sort_population
from draw_functions import draw_paths, draw_plot, draw_cities
import sys
import numpy as np
from benchmark_att35 import *
from google import genai
import math

# Tentativa de importar folium
try:
    import folium

    TEM_FOLIUM = True
except ImportError:
    print("Aviso: Biblioteca 'folium' não instalada. O mapa HTML final não será gerado.")
    TEM_FOLIUM = False

# Define constant values
WIDTH, HEIGHT = 1400, 600
NODE_RADIUS = 5
FPS = 30
PLOT_X_OFFSET = 450

# GA
N_CITIES = 20
POPULATION_SIZE = 100
N_GENERATIONS = 500
MUTATION_PROBABILITY = 0.5

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Using benchmark (Distrito Federal)
WIDTH, HEIGHT = 1500, 800
att_cities_locations = np.array(att_35_cities_locations)

# --- LISTA COM OS NOMES DAS 35 CIDADES E TIPOS DE ATENDIMENTO (Requisito Projeto 2) ---
nomes_ras = [
    "Plano Piloto", "Gama", "Taguatinga", "Brazlândia", "Sobradinho",
    "Planaltina", "Paranoá", "N. Bandeirante", "Ceilândia", "Guará",
    "Cruzeiro", "Samambaia", "Santa Maria", "São Sebastião", "Recanto das Emas",
    "Lago Sul", "Riacho Fundo", "Lago Norte", "Candangolândia", "Águas Claras",
    "Riacho Fundo II", "Sudoeste/Octogonal", "Varjão", "Park Way", "SCIA (Estrutural)",
    "Sobradinho II", "Jardim Botânico", "Itapoã", "SIA", "Vicente Pires",
    "Fercal", "Sol Nascente", "Arniqueira", "Arapoanga", "Água Quente"
]

# Simulando dados reais para a LLM trabalhar:

# --- LISTA COM OS NOMES DAS 35 CIDADES ---
nomes_ras = [
    "Plano Piloto", "Gama", "Taguatinga", "Brazlândia", "Sobradinho",
    "Planaltina", "Paranoá", "N. Bandeirante", "Ceilândia", "Guará",
    "Cruzeiro", "Samambaia", "Santa Maria", "São Sebastião", "Recanto das Emas",
    "Lago Sul", "Riacho Fundo", "Lago Norte", "Candangolândia", "Águas Claras",
    "Riacho Fundo II", "Sudoeste/Octogonal", "Varjão", "Park Way", "SCIA (Estrutural)",
    "Sobradinho II", "Jardim Botânico", "Itapoã", "SIA", "Vicente Pires",
    "Fercal", "Sol Nascente", "Arniqueira", "Arapoanga", "Água Quente"
]

# ==============================================================================
# --- GERAÇÃO ALEATÓRIA DOS TIPOS DE ATENDIMENTO ---
# ==============================================================================
# Definimos quais são as categorias possíveis na nossa simulação
categorias_atendimento = [
    "Emergência obstétrica (Prioridade Máxima)",
    "Casos de violência doméstica (Protocolos Especiais)",
    "Medicamentos hormonais (Controle de Temperatura)",
    "Atendimento pós-parto (Janela de Tempo)",
    "Consulta de Rotina"
]

# O Python vai sortear aleatoriamente 1 categoria para cada uma das 35 RAs
tipos_atendimento = [random.choice(categorias_atendimento) for _ in range(len(nomes_ras))]

# ==============================================================================
# --- FUNÇÃO FITNESS COM RESTRIÇÕES (VRP - TECH CHALLENGE) ---
# ==============================================================================
def calculate_vrp_fitness(path):
    distance = 0
    penalty = 0
    n = len(path)

    # Restrição Adicional 2: Capacidade/Distância máxima do veículo por dia
    DISTANCIA_MAXIMA = 12000

    for i in range(n):
        p1 = path[i]
        p2 = path[(i + 1) % n]
        dist_step = math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
        distance += dist_step

        # Descobre qual é a cidade atual para saber o tipo de atendimento
        orig_idx = cities_locations.index(p1)
        tipo = tipos_atendimento[orig_idx]

        # ---------------------------------------------------------
        # Restrição Obrigatória: Prioridade (Emergências e Violência)
        # ---------------------------------------------------------
        if "Emergência" in tipo or "Prioridade Máxima" in tipo:
            # Se deixar a emergência para o final (índice 'i' alto), a multa é gigantesca!
            # Multiplicamos por i^2 para que o algoritmo seja forçado a colocá-la nos primeiros lugares.
            penalty += (i ** 2) * 500

        elif "violência" in tipo.lower() or "Protocolos" in tipo:
            # Violência doméstica também tem prioridade alta, mas um pouco menor que emergência médica
            penalty += (i ** 2) * 200

        # ---------------------------------------------------------
        # Restrição Adicional 1: Tempo/Temperatura (Medicamentos)
        # ---------------------------------------------------------
        elif "hormonais" in tipo.lower() or "Temperatura" in tipo:
            # O veículo não pode rodar mais de 4000 pixels antes de fazer esta entrega,
            # senão a caixa de refrigeração perde a temperatura.
            if distance > 4000:
                penalty += (distance - 4000) * 10

    # Aplica a multa se a distância total da rota ultrapassar o limite do veículo
    if distance > DISTANCIA_MAXIMA:
        penalty += (distance - DISTANCIA_MAXIMA) * 50

    # O Fitness final é a distância real + todas as multas que a rota sofreu
    return distance + penalty


# ==============================================================================

# ==============================================================================

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TSP Solver using Pygame - Distrito Federal")
clock = pygame.time.Clock()
generation_counter = itertools.count(start=1)

pygame.font.init()
fonte_stats = pygame.font.SysFont("Arial", 16, bold=True)
fonte_lista = pygame.font.SysFont("Arial", 14)

# ADICIONE ESTA LINHA: Uma fonte menor (tamanho 12) para o botão de sair
fonte_aviso = pygame.font.SysFont("Arial", 12, bold=True)

# --- CARREGAR O MAPA ---
try:
    mapa_fundo = pygame.image.load("mapa_df.png")  # Alterado para o seu novo mapa plano!
    img_largura, img_altura = mapa_fundo.get_size()

    area_max_largura = WIDTH - PLOT_X_OFFSET
    area_max_altura = HEIGHT

    fator_escala = min(area_max_largura / img_largura, area_max_altura / img_altura)

    mapa_largura = int(img_largura * fator_escala)
    mapa_altura = int(img_altura * fator_escala)

    mapa_fundo = pygame.transform.smoothscale(mapa_fundo, (mapa_largura, mapa_altura))

    offset_x_mapa = PLOT_X_OFFSET + (area_max_largura - mapa_largura) // 2
    offset_y_mapa = (area_max_altura - mapa_altura) // 2
    tem_mapa_pygame = True
except pygame.error:
    tem_mapa_pygame = False
    mapa_largura, mapa_altura = WIDTH - PLOT_X_OFFSET, HEIGHT
    offset_x_mapa, offset_y_mapa = PLOT_X_OFFSET, 0

# Coordenadas Mapeadas do DF
cities_locations = [
    (690, 318), (573, 667), (647, 397), (532, 261), (854, 235),
    (1142, 175), (1157, 553), (785, 510), (513, 409), (767, 459),
    (825, 414), (555, 525), (770, 657), (1051, 628), (613, 558),
    (835, 501), (742, 533), (901, 352), (810, 485), (713, 463),
    (714, 571), (837, 429), (887, 321), (781, 577), (751, 397),
    (965, 318), (872, 571), (991, 357), (788, 384), (711, 421),
    (807, 120), (566, 466), (730, 503), (1118, 244), (493, 594),
]

target_solution = [cities_locations[i - 1] for i in att_35_cities_order]

population = generate_random_population(cities_locations, POPULATION_SIZE)
best_fitness_values = []
best_solutions = []

MAX_STAGNATION = 100
stagnation_counter = 0
previous_best_fitness = float('inf')
best_solution = population[0]
geracao_atual = 1


def draw_side_panel(screen, generation, best_fitness, stagnation_counter, best_solution, cities_locations, nomes_ras):
    y_start = 400
    x_start = 20
    col2_x = 220

    text_ras = fonte_stats.render(f"RAs: {len(cities_locations)}", True, BLACK)
    text_gen = fonte_stats.render(f"Geração: {generation}", True, BLACK)
    text_dist = fonte_stats.render(f"Melhor distância: {best_fitness:.1f}", True, BLACK)
    text_stag = fonte_stats.render(f"Estagnação: {stagnation_counter}/{MAX_STAGNATION}", True, BLACK)
    text_sair = fonte_aviso.render("Aperte 'Q' para sair e gerar LLM", True, (150, 0, 0))
    text_titulo_rota = fonte_stats.render("Ordem da rota atual:", True, BLACK)

    screen.blit(text_ras, (x_start, y_start))
    screen.blit(text_gen, (x_start, y_start + 25))
    screen.blit(text_dist, (x_start, y_start + 50))
    screen.blit(text_stag, (col2_x, y_start))
    screen.blit(text_sair, (col2_x, y_start + 25))
    screen.blit(text_titulo_rota, (x_start, y_start + 85))

    ordem_atual_indices = [cities_locations.index(cidade) for cidade in best_solution]
    y_lista_start = y_start + 115
    espacamento_linha = 15

    for i, idx in enumerate(ordem_atual_indices):
        nome_cidade = nomes_ras[idx]
        texto_cidade = fonte_lista.render(f"{i + 1:02d}. {nome_cidade}", True, BLACK)
        if i < 18:
            screen.blit(texto_cidade, (x_start, y_lista_start + (i * espacamento_linha)))
        else:
            screen.blit(texto_cidade, (x_start + 200, y_lista_start + ((i - 18) * espacamento_linha)))


# Main game loop
evolving = True
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False

    if evolving:
        geracao_atual = next(generation_counter)
        screen.fill(WHITE)
        if tem_mapa_pygame:
            screen.blit(mapa_fundo, (offset_x_mapa, offset_y_mapa))

        population_fitness = [calculate_vrp_fitness(individual) for individual in population]
        population, population_fitness = sort_population(population, population_fitness)
        best_fitness = calculate_vrp_fitness(population[0])

        if best_fitness < previous_best_fitness:
            previous_best_fitness = best_fitness
            stagnation_counter = 0
        else:
            stagnation_counter += 1

        if stagnation_counter >= MAX_STAGNATION:
            evolving = False

        best_solution = population[0]
        best_fitness_values.append(best_fitness)
        best_solutions.append(best_solution)

        draw_plot(screen, list(range(len(best_fitness_values))), best_fitness_values, y_label="Fitness")

        draw_side_panel(screen, geracao_atual, best_fitness, stagnation_counter, best_solution, cities_locations,
                        nomes_ras)

        # ==============================================================================
        # --- DESENHO PADRÃO COM DESTAQUE APENAS NA RA INICIAL ---
        # ==============================================================================
        # 1. Desenha todas as cidades como pontos vermelhos padrão
        draw_cities(screen, cities_locations, RED, NODE_RADIUS)

        # 2. Desenha a linha da rota principal em azul
        if len(best_solution) > 0:
            draw_paths(screen, best_solution, BLUE, width=3)

            # 3. Destacar apenas o Ponto Inicial (Origem)
            origem = best_solution[0]
            # Desenha um círculo verde maior por cima da primeira cidade
            pygame.draw.circle(screen, (0, 200, 0), origem, NODE_RADIUS + 4)
            # Desenha um ponto branco no meio para dar um efeito de "alvo"
            pygame.draw.circle(screen, (255, 255, 255), origem, NODE_RADIUS - 1)

        # Desenhar uma rota secundária mais fraca (opcional)
        if len(population) > 1:
            draw_paths(screen, population[1], rgb_color=(128, 128, 128), width=1)
        # ==============================================================================

        if evolving:
            new_population = [population[0]]
            while len(new_population) < POPULATION_SIZE:
                probability = 1 / np.array(population_fitness)
                parent1, parent2 = random.choices(population, weights=probability, k=2)
                child1 = order_crossover(parent1, parent2)
                child1 = mutate(child1, MUTATION_PROBABILITY)
                new_population.append(child1)
            population = new_population
    else:
        screen.fill(WHITE)
        if tem_mapa_pygame:
            screen.blit(mapa_fundo, (offset_x_mapa, offset_y_mapa))
        if len(best_fitness_values) > 0:
            draw_plot(screen, list(range(len(best_fitness_values))), best_fitness_values, y_label="Fitness")
            draw_side_panel(screen, geracao_atual, best_fitness, stagnation_counter, best_solution, cities_locations,
                            nomes_ras)
            # ==============================================================================
            # --- DESENHO PADRÃO COM DESTAQUE APENAS NA RA INICIAL ---
            # ==============================================================================
            # 1. Desenha todas as cidades como pontos vermelhos padrão
            draw_cities(screen, cities_locations, RED, NODE_RADIUS)

            # 2. Desenha a linha da rota principal em azul
            if len(best_solution) > 0:
                draw_paths(screen, best_solution, BLUE, width=3)

                # 3. Destacar apenas o Ponto Inicial (Origem)
                origem = best_solution[0]
                # Desenha um círculo verde maior por cima da primeira cidade
                pygame.draw.circle(screen, (0, 200, 0), origem, NODE_RADIUS + 4)
                # Desenha um ponto branco no meio para dar um efeito de "alvo"
                pygame.draw.circle(screen, (255, 255, 255), origem, NODE_RADIUS - 1)

            # Desenhar uma rota secundária mais fraca (opcional)
            if len(population) > 1:
                draw_paths(screen, population[1], rgb_color=(128, 128, 128), width=1)
            # ==============================================================================

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

# ==============================================================================
# --- INTEGRAÇÃO LLM REAL: API DO GOOGLE GEMINI (NOVA BIBLIOTECA) ---
# ==============================================================================

print("\nA conectar à Inteligência Artificial (Google Gemini)...")

# COLOCAR A SUA CHAVE DE API AQUI (Mantenha as aspas)
CHAVE_API = "AIzaSyDII1zx2FfWsjr3eGLFPk9sudEmxrKJdYM"

try:
    # Nova forma de inicializar o cliente do Gemini
    client = genai.Client(api_key=CHAVE_API)

    ordem_final_indices = [cities_locations.index(cidade) for cidade in best_solution]

    # 1. Preparar a lista base para enviar à IA
    roteiro_base_para_ia = ""
    for i, idx in enumerate(ordem_final_indices):
        roteiro_base_para_ia += f"{i + 1}º Parada: {nomes_ras[idx]} | Tipo: {tipos_atendimento[idx]}\n"

    # 2. O Prompt de Engenharia (Few-Shot)
    prompt = f"""
    Atue como um especialista em logística médica e saúde da mulher. 
    Recebeu uma rota otimizada (via Algoritmo Genético) para uma equipa médica móvel no Distrito Federal.
    A sua tarefa é gerar um manual de instruções curtas, operacionais, seguras e sensíveis para a equipa em cada paragem.

    REGRA ESTRITA DE FORMATAÇÃO (O nosso sistema de Dashboard depende deste formato exato, não o altere):
    Xº Parada: [Nome da RA]
       - Tipo de Atendimento: [Tipo exato que foi enviado]
       - [AÇÃO LLM]: [A sua instrução aqui. Seja direto, cite a temperatura se for hormonas, discrição se for violência, ou urgência se for emergência.]

    ROTA A PROCESSAR:
    {roteiro_base_para_ia}

    Gere o relatório completo agora, começando com um cabeçalho de 'MANUAL DE INSTRUÇÕES E ROTEIRO DE EQUIPE'.
    """

    # 3. Chamar a IA para gerar o texto
    print("A gerar as instruções contextuais. Aguarde uns segundos...")

    # Nova forma de chamar o modelo
    resposta_ia = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    relatorio_llm = resposta_ia.text

    # 4. Guardar o ficheiro
    with open("roteiro_equipe_llm.txt", "w", encoding="utf-8") as f:
        f.write(relatorio_llm)

    print("\n--- SUCESSO! ---")
    print("A Inteligência Artificial gerou o manual!")
    print("Pode agora abrir o seu Dashboard no Streamlit para ver o resultado real.")

except Exception as e:
    print(f"\nOcorreu um erro ao contactar a API da IA: {e}")
    print("Verifique se colocou a sua CHAVE_API corretamente.")
# ==============================================================================

# --- FORMA 2: GERAR MAPA INTERATIVO NO FOLIUM (COM ROTAS REAIS POR GPS) ---
if TEM_FOLIUM:
    import requests
    import time

    print("\n🗺️ A gerar o mapa interativo no Folium (Calculando rotas reais pelas ruas, aguarde)...")

    # Coordenadas reais das 35 RAs
    coords_df = [
        (-15.7795, -47.9296), (-16.0160, -48.0682), (-15.8333, -48.0563), (-15.6103, -48.1200), (-15.6580, -47.7925),
        (-15.6216, -47.6521), (-15.7757, -47.7799), (-15.8711, -47.9709), (-15.8127, -48.1038), (-15.8102, -47.9713),
        (-15.7950, -47.9267), (-15.8705, -48.0902), (-16.0036, -47.9872), (-15.9028, -47.7760), (-15.9150, -48.0999),
        (-15.9064, -47.8624), (-15.8814, -48.0169), (-15.7212, -47.8328), (-15.8500, -47.9469), (-15.8394, -48.0289),
        (-15.9039, -48.0381), (-15.8028, -47.9250), (-15.7078, -47.8761), (-15.8864, -47.9542), (-15.7761, -47.9961),
        (-15.6200, -47.8181), (-15.8672, -47.7753), (-15.7483, -47.7633), (-15.8078, -47.9572), (-15.8117, -48.0211),
        (-15.5869, -47.8703), (-15.8203, -48.1364), (-15.8500, -48.0200), (-15.5900, -47.6400), (-15.9189, -48.2436)
    ]

    mapa_folium = folium.Map(location=[-15.7950, -47.9296], zoom_start=10)

    # 1. Traçar as rotas reais usando a API OSRM (GPS)
    for i in range(len(ordem_final_indices)):
        idx_atual = ordem_final_indices[i]
        # O último ponto conecta de volta ao primeiro (fechar o ciclo)
        idx_prox = ordem_final_indices[(i + 1) % len(ordem_final_indices)]

        lat1, lon1 = coords_df[idx_atual]
        lat2, lon2 = coords_df[idx_prox]

        # Chamada à API pública de GPS (OSRM)
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"

        try:
            resposta = requests.get(url)
            if resposta.status_code == 200:
                dados = resposta.json()
                # A API devolve [Longitude, Latitude], o Folium precisa de [Latitude, Longitude]
                coordenadas_rota = dados['routes'][0]['geometry']['coordinates']
                rota_folium = [[lat, lon] for lon, lat in coordenadas_rota]

                # Desenha o caminho exato da rua
                folium.PolyLine(rota_folium, color="blue", weight=3.5, opacity=0.8).add_to(mapa_folium)
            else:
                # Se a API falhar (limite de uso rápido), desenha linha reta como plano B
                folium.PolyLine([(lat1, lon1), (lat2, lon2)], color="blue", weight=3.5, opacity=0.8).add_to(mapa_folium)
        except Exception as e:
            folium.PolyLine([(lat1, lon1), (lat2, lon2)], color="blue", weight=3.5, opacity=0.8).add_to(mapa_folium)

        # Pausa muito breve para não sobrecarregar a API pública
        time.sleep(0.1)

    # 2. Iterar sobre a ordem final para criar os marcadores numerados (mantém o que fizemos antes!)
    for ordem, idx in enumerate(ordem_final_indices):
        lat, lon = coords_df[idx]
        nome_ra = nomes_ras[idx]
        tipo_atendimento = tipos_atendimento[idx]

        cor_fundo = "green"
        if "Emergência" in tipo_atendimento or "Prioridade Máxima" in tipo_atendimento:
            cor_fundo = "darkred"
        elif "violência" in tipo_atendimento.lower():
            cor_fundo = "darkorange"

        tamanho = "28px" if ordem == 0 else "22px"
        borda = "3px solid black" if ordem == 0 else "2px solid white"
        z_index = "1000" if ordem == 0 else "auto"

        html_num = f'''
            <div style="
                font-family: Arial; color: white; background-color: {cor_fundo}; 
                border-radius: 50%; width: {tamanho}; height: {tamanho}; 
                display: flex; justify-content: center; align-items: center; 
                font-weight: bold; font-size: 12px; border: {borda};
                box-shadow: 2px 2px 4px rgba(0,0,0,0.5); z-index: {z_index};
            ">{ordem + 1}</div>
        '''

        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=html_num, icon_anchor=(12, 12)),
            tooltip=f"<b>{ordem + 1}º Parada: {nome_ra}</b><br>{tipo_atendimento}"
        ).add_to(mapa_folium)

    mapa_folium.save("resultado_tsp_mapa.html")


# ==============================================================================
# --- GUARDAR HISTÓRICO DE EVOLUÇÃO (FITNESS) PARA O DASHBOARD ---
# ==============================================================================
print("📊 A exportar dados de evolução do Algoritmo Genético...")
import csv

with open("fitness_evolution.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Geracao", "Fitness"])
    # best_fitness_values é a lista que o seu código já usava para o gráfico do Pygame!
    for geracao, valor_fitness in enumerate(best_fitness_values):
        writer.writerow([geracao, valor_fitness])
# ==============================================================================

# ==============================================================================
# --- AUTO-INICIALIZAÇÃO DO DASHBOARD (STREAMLIT) ---
# ==============================================================================
import os

print("\n🚀 A iniciar o Dashboard Interativo (Streamlit)...")
print("O navegador deve abrir automaticamente. Para fechar o servidor depois, prima Ctrl+C no terminal.")
os.system("streamlit run app_painel.py")

sys.exit()