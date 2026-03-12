import pygame
from pygame.locals import *
import random
import itertools
from genetic_algorithm import mutate, order_crossover, generate_random_population, calculate_fitness, sort_population, \
    default_problems
from draw_functions import draw_paths, draw_plot, draw_cities
import sys
import numpy as np
from benchmark_att17 import *

# Tentativa de importar folium para o mapa final interativo
try:
    import folium
    TEM_FOLIUM = True
except ImportError:
    print("Aviso: Biblioteca 'folium' não instalada. O mapa HTML final não será gerado.")
    print("Para instalar, use: pip install folium")
    TEM_FOLIUM = False

# Define constant values
# pygame
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
att_cities_locations = np.array(att_17_cities_locations)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TSP Solver using Pygame - Distrito Federal")
clock = pygame.time.Clock()
generation_counter = itertools.count(start=1)

# --- FORMA 1: CARREGAR O MAPA SEM DISTORCER ---
try:
    # A procurar por uma imagem do mapa do DF
    mapa_fundo = pygame.image.load("mapa_df.png")
    img_largura, img_altura = mapa_fundo.get_size()

    # Área máxima disponível para o mapa (Tirando o gráfico)
    area_max_largura = WIDTH - PLOT_X_OFFSET
    area_max_altura = HEIGHT

    # Calcula o fator de escala para manter a proporção exata da imagem
    fator_escala = min(area_max_largura / img_largura, area_max_altura / img_altura)

    mapa_largura = int(img_largura * fator_escala)
    mapa_altura = int(img_altura * fator_escala)

    mapa_fundo = pygame.transform.smoothscale(mapa_fundo, (mapa_largura, mapa_altura))

    # Centraliza o mapa na tela se ele não ocupar tudo
    offset_x_mapa = PLOT_X_OFFSET + (area_max_largura - mapa_largura) // 2
    offset_y_mapa = (area_max_altura - mapa_altura) // 2

    tem_mapa_pygame = True
except pygame.error:
    print("Aviso: Imagem 'mapa_df.png' não encontrada.")
    tem_mapa_pygame = False
    mapa_largura, mapa_altura = WIDTH - PLOT_X_OFFSET, HEIGHT
    offset_x_mapa, offset_y_mapa = PLOT_X_OFFSET, 0

# =================================================================
# --- CALIBRAÇÃO DOS PONTOS NO NOVO MAPA ---
# =================================================================
MARGEM_ESQUERDA = 60
MARGEM_DIREITA = 300
MARGEM_TOPO = 150
MARGEM_BAIXO = 60
# Para áreas pequenas como uma cidade/distrito, o mapa é plano.
# Não é necessário ajuste de inclinação (0).
AJUSTE_INCLINACAO = -0.03

# Longitude é o X (índice 1) e Latitude é o Y (índice 0)
min_x = min(point[1] for point in att_cities_locations)
max_x = max(point[1] for point in att_cities_locations)
min_y = min(point[0] for point in att_cities_locations)
max_y = max(point[0] for point in att_cities_locations)

area_util_largura = mapa_largura - (MARGEM_ESQUERDA + MARGEM_DIREITA)
area_util_altura = mapa_altura - (MARGEM_TOPO + MARGEM_BAIXO)

scale_x = area_util_largura / (max_x - min_x)
scale_y = area_util_altura / (max_y - min_y)

cities_locations = []
for point in att_cities_locations:
    lon = point[1]  # Eixo Horizontal
    lat = point[0]  # Eixo Vertical

    # Calcula o novo X com base na Longitude
    novo_x = int((lon - min_x) * scale_x) + offset_x_mapa + MARGEM_ESQUERDA

    # Calcula o novo Y com base na Latitude (INVERTIDO: max_y - lat)
    novo_y = int((max_y - lat) * scale_y) + offset_y_mapa + MARGEM_TOPO

    # Aplica o ajuste de inclinação se necessário
    distancia_da_direita = (max_x - lon) * scale_x
    novo_y -= int(distancia_da_direita * AJUSTE_INCLINACAO)

    cities_locations.append((novo_x, novo_y))

target_solution = [cities_locations[i - 1] for i in att_17_cities_order]
fitness_target_solution = calculate_fitness(target_solution)
print(f"Best Solution Target: {fitness_target_solution}")

# Create Initial Population
population = generate_random_population(cities_locations, POPULATION_SIZE)
best_fitness_values = []
best_solutions = []

# Critério de parada
MAX_STAGNATION = 100
stagnation_counter = 0
previous_best_fitness = float('inf')
best_solution = population[0]  # Variável global para guardar a melhor rota

# Main game loop
evolving = True
running = True

print("A iniciar a evolução. Prima 'Q' para parar e gerar o mapa HTML.")

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False

    if evolving:
        generation = next(generation_counter)

        # Preenche o fundo
        screen.fill(WHITE)
        if tem_mapa_pygame:
            screen.blit(mapa_fundo, (offset_x_mapa, offset_y_mapa))

        population_fitness = [calculate_fitness(individual) for individual in population]
        population, population_fitness = sort_population(population, population_fitness)
        best_fitness = calculate_fitness(population[0])

        if best_fitness < previous_best_fitness:
            previous_best_fitness = best_fitness
            stagnation_counter = 0
        else:
            stagnation_counter += 1

        if stagnation_counter >= MAX_STAGNATION:
            print(f"Critério de paragem atingido: Estagnou por {MAX_STAGNATION} gerações.")
            evolving = False

        best_solution = population[0]
        best_fitness_values.append(best_fitness)
        best_solutions.append(best_solution)

        draw_plot(screen, list(range(len(best_fitness_values))),
                  best_fitness_values, y_label="Fitness - Distância (pxls)")

        draw_cities(screen, cities_locations, RED, NODE_RADIUS)
        draw_paths(screen, best_solution, BLUE, width=3)
        draw_paths(screen, population[1], rgb_color=(128, 128, 128), width=1)

        print(f"Geração {generation}: Melhor fitness = {round(best_fitness, 2)}")

        if evolving:
            new_population = [population[0]]  # ELITISM
            while len(new_population) < POPULATION_SIZE:
                probability = 1 / np.array(population_fitness)
                parent1, parent2 = random.choices(population, weights=probability, k=2)
                child1 = order_crossover(parent1, parent2)
                child1 = mutate(child1, MUTATION_PROBABILITY)
                new_population.append(child1)
            population = new_population

    else:
        # Se parou de evoluir, mantém o ecrã desenhado
        screen.fill(WHITE)
        if tem_mapa_pygame:
            screen.blit(mapa_fundo, (offset_x_mapa, offset_y_mapa))
        if len(best_fitness_values) > 0:
            draw_plot(screen, list(range(len(best_fitness_values))), best_fitness_values,
                      y_label="Fitness - Distância (pxls)")
            draw_cities(screen, cities_locations, RED, NODE_RADIUS)
            draw_paths(screen, best_solution, BLUE, width=3)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

# --- FORMA 2: GERAR MAPA INTERATIVO NO FOLIUM APÓS FECHAR O PYGAME ---
if TEM_FOLIUM:
    print("\nA gerar o mapa interativo no Folium...")

    # Coordenadas geográficas reais do Distrito Federal
    coords_df = [
        (-15.7795, -47.9296), # 1. Brasília (Plano Piloto)
        (-15.6103, -48.1200), # 2. Brazlândia
        (-15.8127, -48.1038), # 3. Ceilândia
        (-15.7950, -47.9267), # 4. Cruzeiro
        (-16.0160, -48.0682), # 5. Gama
        (-15.8102, -47.9713), # 6. Guará
        (-15.7212, -47.8328), # 7. Lago Norte
        (-15.9064, -47.8624), # 8. Lago Sul
        (-15.8711, -47.9709), # 9. Núcleo Bandeirante
        (-15.7757, -47.7799), # 10. Paranoá
        (-15.6216, -47.6521), # 11. Planaltina
        (-15.9150, -48.0999), # 12. Recanto das Emas
        (-15.8705, -48.0902), # 13. Samambaia
        (-16.0036, -47.9872), # 14. Santa Maria
        (-15.9028, -47.7760), # 15. São Sebastião
        (-15.6580, -47.7925), # 16. Sobradinho
        (-15.8333, -48.0563)  # 17. Taguatinga
    ]

    # Cria o mapa centralizado em Brasília, com um zoom adequado para o DF
    mapa_folium = folium.Map(location=[-15.7950, -47.9296], zoom_start=10)

    # Vai buscar os índices originais baseados no melhor caminho
    ordem_final_indices = [cities_locations.index(cidade) for cidade in best_solution]

    # Cria a rota
    rota_lat_lon = [coords_df[i] for i in ordem_final_indices]
    rota_lat_lon.append(rota_lat_lon[0]) # Fecha o ciclo para retornar à origem

    # Adiciona os marcadores vermelhos
    for lat, lon in coords_df:
        folium.CircleMarker(location=[lat, lon], radius=4, color='red', fill=True).add_to(mapa_folium)

    # Adiciona a linha da rota
    folium.PolyLine(rota_lat_lon, color="blue", weight=2.5, opacity=0.8).add_to(mapa_folium)

    mapa_folium.save("resultado_tsp_mapa.html")
    print("Sucesso! O ficheiro 'resultado_tsp_mapa.html' foi guardado. Pode abri-lo no seu navegador.")

sys.exit()