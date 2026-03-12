import pygame
from pygame.locals import *
import random
import itertools
from genetic_algorithm import mutate, order_crossover, generate_random_population, calculate_fitness, sort_population, \
    default_problems
from draw_functions import draw_paths, draw_plot, draw_cities
import sys
import numpy as np
from benchmark_att35 import *

# Tentativa de importar folium para o mapa final interativo
try:
    import folium

    TEM_FOLIUM = True
except ImportError:
    print("Aviso: Biblioteca 'folium' não instalada. O mapa HTML final não será gerado.")
    print("Para instalar, use: pip install folium")
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

# --- LISTA COM OS NOMES DAS 35 CIDADES (Para a interface de texto) ---
nomes_ras = [
    "Plano Piloto", "Gama", "Taguatinga", "Brazlândia", "Sobradinho",
    "Planaltina", "Paranoá", "N. Bandeirante", "Ceilândia", "Guará",
    "Cruzeiro", "Samambaia", "Santa Maria", "São Sebastião", "Recanto das Emas",
    "Lago Sul", "Riacho Fundo", "Lago Norte", "Candangolândia", "Águas Claras",
    "Riacho Fundo II", "Sudoeste/Octogonal", "Varjão", "Park Way", "SCIA (Estrutural)",
    "Sobradinho II", "Jardim Botânico", "Itapoã", "SIA", "Vicente Pires",
    "Fercal", "Sol Nascente", "Arniqueira", "Arapoanga", "Água Quente"
]

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TSP Solver using Pygame - Distrito Federal")
clock = pygame.time.Clock()
generation_counter = itertools.count(start=1)

# --- INICIALIZAR FONTES PARA OS TEXTOS DA INTERFACE ---
pygame.font.init()
# Fontes levemente menores e em negrito para os destaques
fonte_stats = pygame.font.SysFont("Arial", 16, bold=True)
fonte_lista = pygame.font.SysFont("Arial", 14)

# --- FORMA 1: CARREGAR O MAPA SEM DISTORCER ---
try:
    mapa_fundo = pygame.image.load("mapa_df.png")
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
    print("Aviso: Imagem 'mapa_df.png' não encontrada.")
    tem_mapa_pygame = False
    mapa_largura, mapa_altura = WIDTH - PLOT_X_OFFSET, HEIGHT
    offset_x_mapa, offset_y_mapa = PLOT_X_OFFSET, 0

# ================================================================
cities_locations = [
    (690, 318), (573, 667), (647, 397), (532, 261), (854, 235),
    (1142, 175), (1157, 553), (785, 510), (513, 409), (767, 459),
    (825, 414), (555, 525), (770, 657), (1051, 628), (613, 558),
    (835, 501), (742, 533), (901, 352), (810, 485), (713, 463),
    (714, 571), (837, 429), (887, 321), (781, 577), (751, 397),
    (965, 318), (872, 571), (991, 357), (788, 384), (711, 421),
    (807, 120), (566, 466), (730, 503), (1118, 244), (493, 594),
]
# =================================================================

target_solution = [cities_locations[i - 1] for i in att_35_cities_order]
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
best_solution = population[0]
geracao_atual = 1


# Função auxiliar para desenhar a interface de texto
def draw_side_panel(screen, generation, best_fitness, stagnation_counter, best_solution, cities_locations, nomes_ras):
    # Posição inicial empurrada para baixo (escapando do gráfico)
    y_start = 400
    x_start = 20
    col2_x = 220  # Posição X da segunda coluna de estatísticas

    # 1. Desenhar Estatísticas em 2 Colunas para economizar espaço
    text_ras = fonte_stats.render(f"RAs: {len(cities_locations)}", True, BLACK)
    text_gen = fonte_stats.render(f"Geração: {generation}", True, BLACK)
    text_dist = fonte_stats.render(f"Melhor distância: {best_fitness:.1f} px", True, BLACK)

    text_stag = fonte_stats.render(f"Estagnação: {stagnation_counter}/{MAX_STAGNATION}", True, BLACK)
    text_sair = fonte_stats.render("Comando: Aperte 'Q' para sair", True, (150, 0, 0))  # Cor vermelha escura
    text_titulo_rota = fonte_stats.render("Ordem da rota atual:", True, BLACK)

    # Coluna Esquerda
    screen.blit(text_ras, (x_start, y_start))
    screen.blit(text_gen, (x_start, y_start + 25))
    screen.blit(text_dist, (x_start, y_start + 50))

    # Coluna Direita
    screen.blit(text_stag, (col2_x, y_start))
    screen.blit(text_sair, (col2_x, y_start + 25))

    # Título da Rota (mais abaixo)
    screen.blit(text_titulo_rota, (x_start, y_start + 85))

    # 2. Resgatar os índices originais para saber a ordem dos nomes
    ordem_atual_indices = [cities_locations.index(cidade) for cidade in best_solution]

    # 3. Desenhar a lista em 2 colunas com espaçamento otimizado
    y_lista_start = y_start + 115
    espacamento_linha = 15  # Distância exata entre as linhas para caber na tela

    for i, idx in enumerate(ordem_atual_indices):
        nome_cidade = nomes_ras[idx]
        texto_cidade = fonte_lista.render(f"{i + 1:02d}. {nome_cidade}", True, BLACK)

        # Se for até o item 18, fica na coluna da esquerda. Senão, vai para a direita.
        if i < 18:
            screen.blit(texto_cidade, (x_start, y_lista_start + (i * espacamento_linha)))
        else:
            screen.blit(texto_cidade, (x_start + 200, y_lista_start + ((i - 18) * espacamento_linha)))


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
        geracao_atual = next(generation_counter)

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

        # Desenhar tudo da interface
        draw_plot(screen, list(range(len(best_fitness_values))),
                  best_fitness_values, y_label="Fitness - Distância (pxls)")

        # Chama a nova função de desenhar os textos
        draw_side_panel(screen, geracao_atual, best_fitness, stagnation_counter, best_solution, cities_locations,
                        nomes_ras)

        draw_cities(screen, cities_locations, RED, NODE_RADIUS)
        draw_paths(screen, best_solution, BLUE, width=3)
        draw_paths(screen, population[1], rgb_color=(128, 128, 128), width=1)

        print(f"Geração {geracao_atual}: Melhor fitness = {round(best_fitness, 2)}")

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
        # Se parou de evoluir, mantém o ecrã desenhado com os textos intactos
        screen.fill(WHITE)
        if tem_mapa_pygame:
            screen.blit(mapa_fundo, (offset_x_mapa, offset_y_mapa))
        if len(best_fitness_values) > 0:
            draw_plot(screen, list(range(len(best_fitness_values))), best_fitness_values,
                      y_label="Fitness - Distância (pxls)")

            # Chama a função de texto também no estado estagnado
            draw_side_panel(screen, geracao_atual, best_fitness, stagnation_counter, best_solution, cities_locations,
                            nomes_ras)

            draw_cities(screen, cities_locations, RED, NODE_RADIUS)
            draw_paths(screen, best_solution, BLUE, width=3)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

# --- FORMA 2: GERAR MAPA INTERATIVO NO FOLIUM APÓS FECHAR O PYGAME ---
if TEM_FOLIUM:
    print("\nA gerar o mapa interativo no Folium...")

    coords_df = [
        (-15.7795, -47.9296),  # 1. Brasília (Plano Piloto)
        (-16.0160, -48.0682),  # 2. Gama
        (-15.8333, -48.0563),  # 3. Taguatinga
        (-15.6103, -48.1200),  # 4. Brazlândia
        (-15.6580, -47.7925),  # 5. Sobradinho
        (-15.6216, -47.6521),  # 6. Planaltina
        (-15.7757, -47.7799),  # 7. Paranoá
        (-15.8711, -47.9709),  # 8. Núcleo Bandeirante
        (-15.8127, -48.1038),  # 9. Ceilândia
        (-15.8102, -47.9713),  # 10. Guará
        (-15.7950, -47.9267),  # 11. Cruzeiro
        (-15.8705, -48.0902),  # 12. Samambaia
        (-16.0036, -47.9872),  # 13. Santa Maria
        (-15.9028, -47.7760),  # 14. São Sebastião
        (-15.9150, -48.0999),  # 15. Recanto das Emas
        (-15.9064, -47.8624),  # 16. Lago Sul
        (-15.8814, -48.0169),  # 17. Riacho Fundo
        (-15.7212, -47.8328),  # 18. Lago Norte
        (-15.8500, -47.9469),  # 19. Candangolândia
        (-15.8394, -48.0289),  # 20. Águas Claras
        (-15.9039, -48.0381),  # 21. Riacho Fundo II
        (-15.8028, -47.9250),  # 22. Sudoeste/Octogonal
        (-15.7078, -47.8761),  # 23. Varjão
        (-15.8864, -47.9542),  # 24. Park Way
        (-15.7761, -47.9961),  # 25. SCIA (Estrutural)
        (-15.6200, -47.8181),  # 26. Sobradinho II
        (-15.8672, -47.7753),  # 27. Jardim Botânico
        (-15.7483, -47.7633),  # 28. Itapoã
        (-15.8078, -47.9572),  # 29. SIA
        (-15.8117, -48.0211),  # 30. Vicente Pires
        (-15.5869, -47.8703),  # 31. Fercal
        (-15.8203, -48.1364),  # 32. Sol Nascente/Pôr do Sol
        (-15.8500, -48.0200),  # 33. Arniqueira
        (-15.5900, -47.6400),  # 34. Arapoanga
        (-15.9189, -48.2436)  # 35. Água Quente
    ]

    mapa_folium = folium.Map(location=[-15.7950, -47.9296], zoom_start=10)

    ordem_final_indices = [cities_locations.index(cidade) for cidade in best_solution]

    rota_lat_lon = [coords_df[i] for i in ordem_final_indices]
    rota_lat_lon.append(rota_lat_lon[0])

    for lat, lon in coords_df:
        folium.CircleMarker(location=[lat, lon], radius=4, color='red', fill=True).add_to(mapa_folium)

    folium.PolyLine(rota_lat_lon, color="blue", weight=2.5, opacity=0.8).add_to(mapa_folium)

    mapa_folium.save("resultado_tsp_mapa.html")
    print("Sucesso! O ficheiro 'resultado_tsp_mapa.html' foi guardado. Pode abri-lo no seu navegador.")

sys.exit()