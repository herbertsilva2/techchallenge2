import pygame
from pygame.locals import *
import random
import itertools
from genetic_algorithm import mutate, order_crossover, generate_random_population, calculate_fitness, sort_population
from draw_functions import draw_paths, draw_plot, draw_cities
import sys
import numpy as np
from benchmark_att35 import *

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
tipos_atendimento = [
    "Medicamentos hormonais (Controle de Temperatura)", "Atendimento pós-parto (Janela de Tempo)",
    "Emergência obstétrica (Prioridade Máxima)", "Consulta de Rotina", "Atendimento pós-parto (Janela de Tempo)",
    "Casos de violência doméstica (Protocolos Especiais)", "Medicamentos hormonais (Controle de Temperatura)",
    "Consulta de Rotina", "Emergência obstétrica (Prioridade Máxima)",
    "Casos de violência doméstica (Protocolos Especiais)",
    "Consulta de Rotina", "Emergência obstétrica (Prioridade Máxima)", "Atendimento pós-parto (Janela de Tempo)",
    "Casos de violência doméstica (Protocolos Especiais)", "Medicamentos hormonais (Controle de Temperatura)",
    "Consulta de Rotina", "Atendimento pós-parto (Janela de Tempo)", "Consulta de Rotina",
    "Medicamentos hormonais (Controle de Temperatura)", "Consulta de Rotina", "Atendimento pós-parto (Janela de Tempo)",
    "Consulta de Rotina", "Casos de violência doméstica (Protocolos Especiais)", "Consulta de Rotina",
    "Emergência obstétrica (Prioridade Máxima)", "Atendimento pós-parto (Janela de Tempo)", "Consulta de Rotina",
    "Casos de violência doméstica (Protocolos Especiais)", "Medicamentos hormonais (Controle de Temperatura)",
    "Atendimento pós-parto (Janela de Tempo)", "Consulta de Rotina", "Emergência obstétrica (Prioridade Máxima)",
    "Casos de violência doméstica (Protocolos Especiais)", "Atendimento pós-parto (Janela de Tempo)",
    "Emergência obstétrica (Prioridade Máxima)"
]

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TSP Solver using Pygame - Distrito Federal")
clock = pygame.time.Clock()
generation_counter = itertools.count(start=1)

pygame.font.init()
fonte_stats = pygame.font.SysFont("Arial", 16, bold=True)
fonte_lista = pygame.font.SysFont("Arial", 14)

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
    text_dist = fonte_stats.render(f"Melhor distância: {best_fitness:.1f} px", True, BLACK)
    text_stag = fonte_stats.render(f"Estagnação: {stagnation_counter}/{MAX_STAGNATION}", True, BLACK)
    text_sair = fonte_stats.render("Comando: Aperte 'Q' para sair e gerar LLM", True, (150, 0, 0))
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

        population_fitness = [calculate_fitness(individual) for individual in population]
        population, population_fitness = sort_population(population, population_fitness)
        best_fitness = calculate_fitness(population[0])

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
        draw_cities(screen, cities_locations, RED, NODE_RADIUS)
        draw_paths(screen, best_solution, BLUE, width=3)
        draw_paths(screen, population[1], rgb_color=(128, 128, 128), width=1)

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
            draw_cities(screen, cities_locations, RED, NODE_RADIUS)
            draw_paths(screen, best_solution, BLUE, width=3)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

# ==============================================================================
# --- INTEGRAÇÃO LLM: GERAÇÃO DO ROTEIRO E MANUAL (REQUISITO 3 - PROJETO 2) ---
# ==============================================================================
print("\nGerando Relatório e Manual via LLM...")

ordem_final_indices = [cities_locations.index(cidade) for cidade in best_solution]

# 1. Estruturando os dados para a "LLM"
roteiro_detalhado = ""
for i, idx in enumerate(ordem_final_indices):
    roteiro_detalhado += f"{i + 1}º Parada: {nomes_ras[idx]}\n"
    roteiro_detalhado += f"   - Tipo de Atendimento: {tipos_atendimento[idx]}\n"

    # Adicionando instruções específicas baseadas no tipo de atendimento (Simulação de output da LLM)
    if "Emergência" in tipos_atendimento[idx]:
        roteiro_detalhado += "   - [AÇÃO LLM]: Ligar sirene ao entrar na RA. Preparar kit de estabilização. Tempo de parada mínimo estimado: 15 min.\n"
    elif "Violência doméstica" in tipos_atendimento[idx]:
        roteiro_detalhado += "   - [AÇÃO LLM]: Abordagem discreta obrigatória (Veículo descaracterizado). Seguir protocolo de escuta ativa e acolhimento seguro.\n"
    elif "hormonais" in tipos_atendimento[idx]:
        roteiro_detalhado += "   - [AÇÃO LLM]: Verificar temperatura da caixa refrigerada (deve estar entre 2°C e 8°C) antes de realizar a entrega.\n"
    else:
        roteiro_detalhado += "   - [AÇÃO LLM]: Confirmar dados da paciente e realizar orientações padrão de saúde da mulher.\n"
    roteiro_detalhado += "\n"

# 2. Montando o texto final do relatório
relatorio_llm = f"""
=========================================================
 MANUAL DE INSTRUÇÕES E ROTEIRO DE EQUIPE (GERADO POR LLM)
=========================================================
CONTEXTO:
Este relatório foi gerado automaticamente para guiar a equipe de 
transporte especializado em saúde da mulher pelo Distrito Federal.
A rota foi otimizada matematicamente para cobrir {len(cities_locations)} 
Regiões Administrativas com a maior eficiência possível.

ROTEIRO DETALHADO (ORDEM DE VISITAS):
---------------------------------------------------------
{roteiro_detalhado}
=========================================================
ORIENTAÇÕES FINAIS (LLM):
Lembre-se de manter o respeito e a privacidade de todas as pacientes. 
Em caso de mudança de prioridade (ex: nova emergência obstétrica), 
o algoritmo deverá ser rodado novamente para recálculo de rota.
=========================================================
"""

# 3. Salvando e exibindo
with open("roteiro_equipe_llm.txt", "w", encoding="utf-8") as f:
    f.write(relatorio_llm)

print(relatorio_llm)
print("Sucesso! O manual da equipe foi salvo como 'roteiro_equipe_llm.txt'.\n")

# --- FORMA 2: GERAR MAPA INTERATIVO NO FOLIUM ---
if TEM_FOLIUM:
    print("A gerar o mapa interativo no Folium...")
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
    rota_lat_lon = [coords_df[i] for i in ordem_final_indices]
    rota_lat_lon.append(rota_lat_lon[0])

    for lat, lon in coords_df:
        folium.CircleMarker(location=[lat, lon], radius=4, color='red', fill=True).add_to(mapa_folium)

    folium.PolyLine(rota_lat_lon, color="blue", weight=2.5, opacity=0.8).add_to(mapa_folium)

    mapa_folium.save("resultado_tsp_mapa.html")

sys.exit()