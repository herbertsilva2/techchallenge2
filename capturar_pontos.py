import pygame
import sys

from pygame import QUIT, MOUSEBUTTONDOWN

# Configurações iguais ao seu tsp.py
WIDTH, HEIGHT = 1500, 800
PLOT_X_OFFSET = 450

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mapeador de Cidades - Clique nos nomes!")

# CARREGUE O NOME DA SUA IMAGEM AQUI
nome_da_imagem = "mapa_df.png" # <--- Mude se o nome for diferente

try:
    mapa_fundo = pygame.image.load(nome_da_imagem)
except:
    print(f"Erro: Não encontrei a imagem '{nome_da_imagem}'.")
    sys.exit()

img_largura, img_altura = mapa_fundo.get_size()
area_max_largura = WIDTH - PLOT_X_OFFSET
fator_escala = min(area_max_largura / img_largura, HEIGHT / img_altura)
mapa_largura = int(img_largura * fator_escala)
mapa_altura = int(img_altura * fator_escala)
mapa_fundo = pygame.transform.smoothscale(mapa_fundo, (mapa_largura, mapa_altura))
offset_x_mapa = PLOT_X_OFFSET + (area_max_largura - mapa_largura) // 2
offset_y_mapa = (HEIGHT - mapa_altura) // 2

# Lista na ordem exata do seu arquivo benchmark_att35.py
nomes = [
    "1. Brasília", "2. Gama", "3. Taguatinga", "4. Brazlândia", "5. Sobradinho",
    "6. Planaltina", "7. Paranoá", "8. N. Bandeirante", "9. Ceilândia", "10. Guará",
    "11. Cruzeiro (perto do Sudoeste)", "12. Samambaia", "13. Santa Maria", "14. São Sebastião",
    "15. Recanto das Emas", "16. Lago Sul", "17. Riacho Fundo", "18. Lago Norte", "19. Candangolândia",
    "20. Águas Claras", "21. Riacho Fundo II", "22. Sudoeste/Octogonal", "23. Varjão", "24. Park Way",
    "25. SCIA", "26. Sobradinho II", "27. Jardim Botânico", "28. Itapoã", "29. SIA", "30. Vicente Pires",
    "31. Fercal (Acima de Sobradinho)", "32. Sol Nascente (Colado em Ceilândia)",
    "33. Arniqueira (Abaixo de Águas Claras)", "34. Arapoanga (Perto de Planaltina)",
    "35. Água Quente (Fronteira sudoeste)"
]

coordenadas_pixels = []
fonte = pygame.font.SysFont(None, 36)

rodando = True
while rodando:
    screen.fill((255, 255, 255))
    screen.blit(mapa_fundo, (offset_x_mapa, offset_y_mapa))

    # Desenha os pontos já clicados
    for p in coordenadas_pixels:
        pygame.draw.circle(screen, (255, 0, 0), p, 6)

    # Mostra no topo esquerdo onde você deve clicar agora
    if len(coordenadas_pixels) < 35:
        texto = fonte.render(f"Clique em: {nomes[len(coordenadas_pixels)]}", True, (0, 0, 0))
        screen.blit(texto, (20, 20))
    else:
        texto = fonte.render("PRONTO! Copie os dados no terminal e feche a janela.", True, (0, 150, 0))
        screen.blit(texto, (20, 20))

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == QUIT:
            rodando = False
        elif event.type == MOUSEBUTTONDOWN and len(coordenadas_pixels) < 35:
            # Captura a posição X, Y exata do mouse
            x, y = event.pos
            coordenadas_pixels.append((x, y))
            print(f"Marcado {nomes[len(coordenadas_pixels)-1]}: ({x}, {y})")

            # Quando terminar os 35 cliques, ele gera o código pronto pra você!
            if len(coordenadas_pixels) == 35:
                print("\n\n=== COPIE E COLE O BLOCO ABAIXO NO SEU TSP.PY ===")
                print("cities_locations = [")
                for coord in coordenadas_pixels:
                    print(f"    {coord},")
                print("]")
                print("=================================================")

pygame.quit()
sys.exit()