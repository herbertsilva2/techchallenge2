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
ORANGE = (255, 140, 0)

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
# --- FUNÇÃO FITNESS ESPECÍFICA DESTE PROJETO (VRP MÚLTIPLOS VEÍCULOS) ---
# ==============================================================================
def calculate_vrp_fitness(path):
    # Divide as 35 cidades para as duas ambulâncias
    meio = len(path) // 2
    rota1 = path[:meio]
    rota2 = path[meio:]

    def calcular_custo_veiculo(rota_veiculo):
        distance = 0
        penalty = 0
        n = len(rota_veiculo)
        DISTANCIA_MAXIMA = 15000 # Reduzimos a distância máxima pois a rota é menor

        for i in range(n):
            p1 = rota_veiculo[i]
            p2 = rota_veiculo[(i + 1) % n]
            dist_step = math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
            distance += dist_step

            orig_idx = cities_locations.index(p1)
            tipo = tipos_atendimento[orig_idx]

            if "Emergências" in tipo:
                penalty += (i ** 2) * 200
            elif "violência" in tipo.lower():
                penalty += (i ** 2) * 100
            elif "hormonais" in tipo.lower():
                if distance > 6000: # Limite de refrigeração ajustado
                    penalty += (distance - 6000) * 5
                penalty += (i * 50)
            elif "pós-parto" in tipo.lower():
                if i > 10: # Ajustado pois cada veículo faz ~17 paradas
                    penalty += (i - 10) * 100

        if distance > DISTANCIA_MAXIMA:
            penalty += (distance - DISTANCIA_MAXIMA) * 10

        return distance + penalty

    # O custo da geração é a soma das rotas da Ambulância 1 e Ambulância 2
    return calcular_custo_veiculo(rota1) + calcular_custo_veiculo(rota2)

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
        meio = len(best_solution) // 2
        rota1 = best_solution[:meio]
        rota2 = best_solution[meio:]

        # Desenhar Rota 1 (Azul)
        draw_paths(screen, rota1, BLUE, width=2)
        pygame.draw.circle(screen, GREEN, rota1[0], NODE_RADIUS + 3)  # Partida Azul

        # Desenhar Rota 2 (Laranja)
        draw_paths(screen, rota2, ORANGE, width=2)
        pygame.draw.circle(screen, GREEN, rota2[0], NODE_RADIUS + 3)  # Partida Laranja

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

    # screen.blit(font_large.render("Ordem da rota atual:", True, BLACK), (20, y_text + 110))

    # ==========================================================================
    # DESENHO DAS LISTAS DE CIDADES (DUAS AMBULÂNCIAS)
    # ==========================================================================
    y_list_title = y_text + 110

    if best_solution:
        # Divide a rota exatamente ao meio para as duas equipas
        meio = len(best_solution) // 2
        rota1 = best_solution[:meio]
        rota2 = best_solution[meio:]

        y_list = y_list_title + 30

        # Títulos das Colunas com as respetivas cores
        screen.blit(font_large.render("Equipe 1 (Azul):", True, BLUE), (20, y_list_title))
        screen.blit(font_large.render("Equipe 2 (Laranja):", True, ORANGE), (PANEL_WIDTH // 2, y_list_title))

        # Desenhar Rota 1 na Coluna da Esquerda
        for i, city_pos in enumerate(rota1):
            idx = cities_locations.index(city_pos)
            nome_cidade = nomes_ras[idx]
            texto_lista = font_small.render(f"{i + 1:02d}. {nome_cidade}", True, BLACK)
            screen.blit(texto_lista, (20, y_list + (i * 20)))

        # Desenhar Rota 2 na Coluna da Direita
        for i, city_pos in enumerate(rota2):
            idx = cities_locations.index(city_pos)
            nome_cidade = nomes_ras[idx]
            texto_lista = font_small.render(f"{i + 1:02d}. {nome_cidade}", True, BLACK)
            screen.blit(texto_lista, (PANEL_WIDTH // 2, y_list + (i * 20)))

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
meio_lista = len(ordem_final_indices) // 2

for i, idx in enumerate(ordem_final_indices):
    nome_ra = nomes_ras[idx]
    tipo = tipos_atendimento[idx]

    # Lógica Matemática para reiniciar a numeração na segunda equipe
    if i < meio_lista:
        ordem_equipe = i + 1
    else:
        ordem_equipe = (i - meio_lista) + 1

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

    # Usando a variável 'ordem_equipe' no texto final
    relatorio_mock += f"{ordem_equipe}º Parada: {nome_ra}\n"
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

# 1. Divide a lista de índices finais exatamente ao meio
meio = len(ordem_final_indices) // 2
rota1_indices = ordem_final_indices[:meio]
rota2_indices = ordem_final_indices[meio:]


# 2. Função auxiliar para traçar a rota com a cor certa no GPS
def desenhar_rota_gps(indices, cor_linha):
    # Nota: Não usamos o "+ 1 % len" aqui para que a rota termine na última paragem
    for i in range(len(indices) - 1):
        idx_atual = indices[i]
        idx_prox = indices[i + 1]
        lat1, lon1 = coords_df[idx_atual]
        lat2, lon2 = coords_df[idx_prox]

        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        try:
            resposta = requests.get(url)
            if resposta.status_code == 200:
                dados = resposta.json()
                coordenadas_rota = dados['routes'][0]['geometry']['coordinates']
                rota_folium = [[lat, lon] for lon, lat in coordenadas_rota]
                folium.PolyLine(rota_folium, color=cor_linha, weight=4.5, opacity=0.8).add_to(mapa_folium)
            else:
                folium.PolyLine([(lat1, lon1), (lat2, lon2)], color=cor_linha, weight=4.5, opacity=0.8).add_to(
                    mapa_folium)
        except Exception:
            folium.PolyLine([(lat1, lon1), (lat2, lon2)], color=cor_linha, weight=4.5, opacity=0.8).add_to(mapa_folium)
        time.sleep(0.1)  # Pausa para não sobrecarregar a API pública de GPS


# 3. Manda desenhar as duas rotas separadas
print("      -> A traçar rotas da Equipe Azul...")
desenhar_rota_gps(rota1_indices, "blue")

print("      -> A traçar rotas da Equipe Laranja...")
desenhar_rota_gps(rota2_indices, "orange")

# Mapeamento dos marcadores com numeração e bordas separadas por equipe
for ordem, idx in enumerate(ordem_final_indices):
    lat, lon = coords_df[idx]
    nome_ra = nomes_ras[idx]
    tipo_atendimento = tipos_atendimento[idx]

    # Descobrir qual é a equipe e reiniciar a ordem
    meio_lista = len(ordem_final_indices) // 2
    if ordem < meio_lista:
        ordem_equipe = ordem + 1
        cor_borda = "blue"
        nome_equipe = "Equipe 1 (Azul)"
    else:
        ordem_equipe = (ordem - meio_lista) + 1
        cor_borda = "orange"
        nome_equipe = "Equipe 2 (Laranja)"

    # Cores de prioridade médica (fundo da bolinha)
    cor_fundo = "green"
    if "Emergências" in tipo_atendimento:
        cor_fundo = "darkred"
    elif "violência" in tipo_atendimento.lower():
        cor_fundo = "darkorange"

    tamanho = "28px" if ordem_equipe == 1 else "22px"
    borda = f"3px solid {cor_borda}" if ordem_equipe == 1 else f"2px solid {cor_borda}"
    z_index = "1000" if ordem_equipe == 1 else "auto"

    html_num = f'''
        <div style="font-family: Arial; color: white; background-color: {cor_fundo}; 
            border-radius: 50%; width: {tamanho}; height: {tamanho}; 
            display: flex; justify-content: center; align-items: center; 
            font-weight: bold; font-size: 12px; border: {borda};
            box-shadow: 2px 2px 4px rgba(0,0,0,0.5); z-index: {z_index};">
            {ordem_equipe}
        </div>
    '''
    folium.Marker(
        location=[lat, lon],
        icon=folium.DivIcon(html=html_num, icon_anchor=(12, 12)),
        tooltip=f"<b>{nome_equipe} | {ordem_equipe}º Parada: {nome_ra}</b><br>{tipo_atendimento}"
    ).add_to(mapa_folium)

mapa_folium.save("resultado_tsp_mapa.html")

print("[4/4] 🚀 A iniciar o Dashboard Interativo (Streamlit)...")
os.system("streamlit run app_painel.py")