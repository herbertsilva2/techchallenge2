import pygame
import random
import math
import sys
import os
import time
import requests
import folium
import csv

from benchmark_att35 import *

# IMPORTAÇÃO DOS MÉTODOS DO SEU MÓDULO (genetic_algorithm.py)
from genetic_algorithm import generate_random_population, order_crossover, mutate, sort_population

# ==============================================================================
# --- CONFIGURAÇÕES INICIAIS DO PYGAME ---
# ==============================================================================
pygame.init()

# 1. Obter a resolução real do monitor do utilizador
info = pygame.display.Info()
WIDTH = info.current_w
HEIGHT = info.current_h

# 2. Definir o layout dinâmico (Painel de Controlo ocupa 30% do ecrã)
PANEL_WIDTH = int(WIDTH * 0.3)
MAP_WIDTH = WIDTH - PANEL_WIDTH

NODE_RADIUS = 5
POPULATION_SIZE = 100
MUTATION_RATE = 0.3 # Taxa ideal para o novo método de mutação
MAX_STAGNATION = 50
FPS = 10

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 200, 0)

# Criar a janela em Fullscreen
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("TSP Solver using Pygame - Saúde da Mulher DF")
font_small = pygame.font.SysFont("Arial", 14)
font_medium = pygame.font.SysFont("Arial", 16, bold=True)
font_large = pygame.font.SysFont("Arial", 18, bold=True)

# ==============================================================================
# --- CARREGAR IMAGEM E AJUSTAR PROPORÇÃO (SEM DISTORCER) ---
# ==============================================================================
try:
    bg_original = pygame.image.load("mapa_df.png")
    img_w, img_h = bg_original.get_size()

    scale = min(MAP_WIDTH / img_w, HEIGHT / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    background_image = pygame.transform.scale(bg_original, (new_w, new_h))

    map_x = PANEL_WIDTH + (MAP_WIDTH - new_w) // 2
    map_y = (HEIGHT - new_h) // 2

except Exception as e:
    print(f"Aviso: Não foi possível carregar 'mapa_df.png'. Erro: {e}")
    background_image = None
    map_x, map_y, new_w, new_h = PANEL_WIDTH, 0, MAP_WIDTH, HEIGHT

# ==============================================================================
# --- DADOS DO DISTRITO FEDERAL E PRIORIDADES DO EDITAL ---
# ==============================================================================
nomes_ras = [
    "Plano Piloto", "Gama", "Taguatinga", "Brazlândia", "Sobradinho",
    "Planaltina", "Paranoá", "N. Bandeirante", "Ceilândia", "Guará",
    "Cruzeiro", "Samambaia", "Santa Maria", "São Sebastião", "Recanto das Emas",
    "Lago Sul", "Riacho Fundo", "Lago Norte", "Candangolândia", "Águas Claras",
    "Riacho Fundo II", "Sudoeste/Octogonal", "Varjão", "Park Way", "SCIA (Estrutural)",
    "Sobradinho II", "Jardim Botânico", "Itapoã", "SIA", "Vicente Pires",
    "Fercal", "Sol Nascente", "Arniqueira", "Arapoanga", "Água Quente"
]

categorias_atendimento = [
    "Emergências obstétricas (prioridade máxima)",
    "Casos de violência doméstica (protocolos especiais)",
    "Medicamentos hormonais (temperatura controlada)",
    "Atendimento pós-parto (janelas de tempo específicas)",
    "Consulta de Rotina"
]
tipos_atendimento = [random.choice(categorias_atendimento) for _ in range(len(nomes_ras))]

cities_locations = []
for nome in nomes_ras:
    rel_x, rel_y = att_35_cities_locations[nome]
    x = int(map_x + (rel_x * new_w))
    y = int(map_y + (rel_y * new_h))
    cities_locations.append((x, y))

# ==============================================================================
# --- FUNÇÃO FITNESS ESPECÍFICA DESTE PROJETO (VRP) ---
# ==============================================================================
def calculate_vrp_fitness(path):
    distance = 0
    penalty = 0
    n = len(path)
    DISTANCIA_MAXIMA = 24000

    for i in range(n):
        p1 = path[i]
        p2 = path[(i + 1) % n]
        dist_step = math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
        distance += dist_step

        orig_idx = cities_locations.index(p1)
        tipo = tipos_atendimento[orig_idx]

        # Multas muito mais suaves (escala de milhares em vez de bilhões)
        if "Emergências" in tipo:
            penalty += (i ** 2) * 200     # Multa moderada (força a ir para o início)
        elif "violência" in tipo.lower():
            penalty += (i ** 2) * 100     # Segunda maior prioridade
        elif "hormonais" in tipo.lower():
            if distance > 8000:
                penalty += (distance - 8000) * 5  # Suavizada a multa de temperatura
            penalty += (i * 50)           # Pressão leve (linear) para vir antes
        elif "pós-parto" in tipo.lower():
            if i > 20:
                penalty += (i - 20) * 100 # Penalidade leve por atraso

    # Multa de distância total máxima também suavizada
    if distance > DISTANCIA_MAXIMA:
        penalty += (distance - DISTANCIA_MAXIMA) * 10

    return distance + penalty

def draw_paths(surface, path, color, width=2):
    if len(path) > 1:
        pygame.draw.lines(surface, color, True, path, width)

# ==============================================================================
# --- LOOP PRINCIPAL (PYGAME) ---
# ==============================================================================
# Utilizando as funções limpas do módulo importado
population = generate_random_population(cities_locations, POPULATION_SIZE)
best_solution = None
best_fitness = float('inf')
generation = 0
best_fitness_values = []
stagnation_counter = 0

clock = pygame.time.Clock()

running = True
evolving = True

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    if evolving:
        population_fitness = [calculate_vrp_fitness(individual) for individual in population]

        population, population_fitness = sort_population(population, population_fitness)

        current_best_fitness = population_fitness[0]
        if current_best_fitness < best_fitness:
            best_fitness = current_best_fitness
            best_solution = population[0]
            stagnation_counter = 0
        else:
            stagnation_counter += 1

        best_fitness_values.append(best_fitness)

        if stagnation_counter >= MAX_STAGNATION:
            evolving = False

        new_population = [population[0]]

        while len(new_population) < POPULATION_SIZE:
            parent1, parent2 = random.choices(population[:10], k=2)
            child1 = order_crossover(parent1, parent2)
            child1 = mutate(child1, MUTATION_RATE)
            new_population.append(child1)

        population = new_population
        generation += 1

    # ==========================================================================
    # DESENHO DA TELA (FULLSCREEN & RESPONSIVO)
    # ==========================================================================
    screen.fill(WHITE)

    if background_image:
        screen.blit(background_image, (map_x, map_y))

    if best_solution and len(best_solution) > 0:
        draw_paths(screen, best_solution, BLUE, width=2)
        origem = best_solution[0]
        pygame.draw.circle(screen, GREEN, origem, NODE_RADIUS + 3)
        pygame.draw.circle(screen, WHITE, origem, NODE_RADIUS)

    for city in cities_locations:
        pygame.draw.circle(screen, RED, city, NODE_RADIUS)

    # ==========================================================================
    # DESENHO DO GRÁFICO DE FITNESS (ESCADA COM NÚMEROS)
    # ==========================================================================
    GRAPH_X = 70  # Afastado da borda para caberem os números
    GRAPH_Y = 20
    GRAPH_W = PANEL_WIDTH - 100
    GRAPH_H = 200
    graph_rect = pygame.Rect(GRAPH_X, GRAPH_Y, GRAPH_W, GRAPH_H)
    pygame.draw.rect(screen, BLACK, graph_rect, 1)
    # Títulos dos Eixos
    texto_y = font_small.render("Fitness", True, BLACK)
    texto_y = pygame.transform.rotate(texto_y, 90)
    screen.blit(texto_y, (10, GRAPH_Y + GRAPH_H // 2 - texto_y.get_height() // 2))
    texto_x = font_small.render("Generation", True, BLACK)
    screen.blit(texto_x, (GRAPH_X + GRAPH_W // 2 - texto_x.get_width() // 2, GRAPH_Y + GRAPH_H + 25))
    if len(best_fitness_values) > 1:
        # Ignora as gerações iniciais caóticas para não amassar o gráfico
        valores_visiveis = best_fitness_values[15:] if len(best_fitness_values) > 20 else best_fitness_values

        # 1. Encontra os valores reais
        max_real = max(valores_visiveis)
        min_real = min(valores_visiveis)
        diff_real = max_real - min_real if max_real != min_real else 1

        # 2. Cria uma "margem de respiro" de 10% em cima e em baixo
        margem = diff_real * 0.1
        max_f = max_real + margem
        min_f = min_real - margem
        diff_f = max_f - min_f

        # Desenhar marcações e números do Eixo Y (Vertical)
        num_y_ticks = 5
        for i in range(num_y_ticks):
            val = max_f - i * (diff_f / (num_y_ticks - 1))
            y_pos = GRAPH_Y + i * (GRAPH_H / (num_y_ticks - 1))
            pygame.draw.line(screen, BLACK, (GRAPH_X - 5, y_pos), (GRAPH_X, y_pos), 1)
            lbl = font_small.render(f"{int(val)}", True, BLACK)
            screen.blit(lbl, (GRAPH_X - lbl.get_width() - 8, y_pos - lbl.get_height() // 2))

        # Desenhar marcações e números do Eixo X (Horizontal)
        num_x_ticks = 5
        max_gen = max(1, len(best_fitness_values) - 1)
        for i in range(num_x_ticks):
            gen_val = int(i * (max_gen / (num_x_ticks - 1)))
            x_pos = GRAPH_X + i * (GRAPH_W / (num_x_ticks - 1))
            pygame.draw.line(screen, BLACK, (x_pos, GRAPH_Y + GRAPH_H), (x_pos, GRAPH_Y + GRAPH_H + 5), 1)
            lbl = font_small.render(f"{gen_val}", True, BLACK)
            screen.blit(lbl, (x_pos - lbl.get_width() // 2, GRAPH_Y + GRAPH_H + 8))

        # Desenhar a linha em formato de "Escada" (Step Chart)
        points = []
        prev_x, prev_y = None, None
        for i, val in enumerate(best_fitness_values):
            # Usamos o max_real para não cortar a linha se ela passar a margem superior inicial
            val_limitado = min(val, max_real)
            x_pos = GRAPH_X + (i / max_gen) * GRAPH_W
            y_pos = GRAPH_Y + GRAPH_H - ((val_limitado - min_f) / diff_f) * GRAPH_H

            if prev_x is not None:
                points.append((x_pos, prev_y))

            points.append((x_pos, y_pos))
            prev_x, prev_y = x_pos, y_pos

        if len(points) >= 2:
            pygame.draw.lines(screen, BLUE, False, points, 2)

    y_text = 270
    screen.blit(font_large.render("RAs: 35", True, BLACK), (20, y_text))
    screen.blit(font_large.render(f"Geração: {generation}", True, BLACK), (20, y_text + 30))
    screen.blit(font_large.render(f"Melhor distância: {best_fitness:.1f}", True, BLACK), (20, y_text + 60))

    screen.blit(font_large.render(f"Estagnação: {stagnation_counter}/{MAX_STAGNATION}", True, BLACK),
                (PANEL_WIDTH // 2, y_text))
    texto_aviso = font_small.render("Aperte 'Q' para sair e gerar LLM", True, RED)
    screen.blit(texto_aviso, (PANEL_WIDTH // 2, y_text + 30))

    screen.blit(font_large.render("Ordem da rota atual:", True, BLACK), (20, y_text + 110))

    if best_solution:
        y_list = y_text + 140
        for i, city_pos in enumerate(best_solution):
            idx = cities_locations.index(city_pos)
            nome_cidade = nomes_ras[idx]
            texto_lista = font_small.render(f"{i + 1:02d}. {nome_cidade}", True, BLACK)

            max_lines = (HEIGHT - y_list - 20) // 20

            if i < max_lines:
                screen.blit(texto_lista, (20, y_list + (i * 20)))
            else:
                screen.blit(texto_lista, (PANEL_WIDTH // 2, y_list + ((i - max_lines) * 20)))

    pygame.display.flip()

pygame.quit()

# ==============================================================================
# --- EXPORTAÇÃO DE DADOS E CHAMADA DO STREAMLIT ---
# ==============================================================================
print("\n[1/4] A exportar dados de evolução do Algoritmo Genético...")
with open("fitness_evolution.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Geracao", "Fitness"])
    for g, valor_fitness in enumerate(best_fitness_values):
        writer.writerow([g, valor_fitness])

ordem_final_indices = [cities_locations.index(cidade) for cidade in best_solution]

print("[2/4] A gerar o Manual de Instruções e estimativas de deslocamento...")
relatorio_mock = "MANUAL DE INSTRUÇÕES E ROTEIRO DE EQUIPE\n\n"
for i, idx in enumerate(ordem_final_indices):
    nome_ra = nomes_ras[idx]
    tipo = tipos_atendimento[idx]

    distancia_estimada = random.randint(5, 25)
    tempo_estimado = int(distancia_estimada * 1.5)

    if "Emergências" in tipo:
        acao_llm = "Urgência! Avaliar estado materno-fetal imediatamente e estabilizar para transporte urgente se necessário."
    elif "violência" in tipo.lower():
        acao_llm = "Discrição. Abordagem sensível e discreta. Assegurar privacidade e ativar protocolo de apoio psicossocial."
    elif "hormonais" in tipo.lower():
        acao_llm = "Medicamentos hormonais. Verificar e garantir armazenamento a 2-8°C. Administrar conforme prescrição."
    elif "pós-parto" in tipo.lower():
        acao_llm = "Janela de Tempo. Realizar avaliação pós-parto, focando na recuperação materna e neonatal."
    else:
        acao_llm = "Consulta de Rotina. Avaliar saúde geral e necessidades de prevenção/promoção da saúde."

    relatorio_mock += f"{i + 1}º Parada: {nome_ra}\n"
    relatorio_mock += f"   - Tipo de Atendimento: {tipo}\n"
    relatorio_mock += f"   - Deslocamento Estimado: {distancia_estimada} km (Aprox. {tempo_estimado} min)\n"
    relatorio_mock += f"   - [AÇÃO LLM]: {acao_llm}\n\n"

with open("roteiro_equipe_llm.txt", "w", encoding="utf-8") as f:
    f.write(relatorio_mock)

print("[3/4] A gerar mapa de ruas reais com GPS (OSRM)... Pode demorar alguns segundos.")
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

for i in range(len(ordem_final_indices)):
    idx_atual = ordem_final_indices[i]
    idx_prox = ordem_final_indices[(i + 1) % len(ordem_final_indices)]
    lat1, lon1 = coords_df[idx_atual]
    lat2, lon2 = coords_df[idx_prox]
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    try:
        resposta = requests.get(url)
        if resposta.status_code == 200:
            dados = resposta.json()
            coordenadas_rota = dados['routes'][0]['geometry']['coordinates']
            rota_folium = [[lat, lon] for lon, lat in coordenadas_rota]
            folium.PolyLine(rota_folium, color="blue", weight=3.5, opacity=0.8).add_to(mapa_folium)
        else:
            folium.PolyLine([(lat1, lon1), (lat2, lon2)], color="blue", weight=3.5, opacity=0.8).add_to(mapa_folium)
    except Exception:
        folium.PolyLine([(lat1, lon1), (lat2, lon2)], color="blue", weight=3.5, opacity=0.8).add_to(mapa_folium)
    time.sleep(0.1)

for ordem, idx in enumerate(ordem_final_indices):
    lat, lon = coords_df[idx]
    nome_ra = nomes_ras[idx]
    tipo_atendimento = tipos_atendimento[idx]

    cor_fundo = "green"
    if "Emergências" in tipo_atendimento:
        cor_fundo = "darkred"
    elif "violência" in tipo_atendimento.lower():
        cor_fundo = "darkorange"

    tamanho = "28px" if ordem == 0 else "22px"
    borda = "3px solid black" if ordem == 0 else "2px solid white"
    z_index = "1000" if ordem == 0 else "auto"

    html_num = f'''
        <div style="font-family: Arial; color: white; background-color: {cor_fundo}; 
            border-radius: 50%; width: {tamanho}; height: {tamanho}; 
            display: flex; justify-content: center; align-items: center; 
            font-weight: bold; font-size: 12px; border: {borda};
            box-shadow: 2px 2px 4px rgba(0,0,0,0.5); z-index: {z_index};">
            {ordem + 1}
        </div>
    '''
    folium.Marker(
        location=[lat, lon],
        icon=folium.DivIcon(html=html_num, icon_anchor=(12, 12)),
        tooltip=f"<b>{ordem + 1}º Parada: {nome_ra}</b><br>{tipo_atendimento}"
    ).add_to(mapa_folium)

mapa_folium.save("resultado_tsp_mapa.html")

print("[4/4] 🚀 A iniciar o Dashboard Interativo (Streamlit)...")
os.system("streamlit run app_painel.py")