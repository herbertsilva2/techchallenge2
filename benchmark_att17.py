# -*- coding: utf-8 -*-
"""
Coordenadas das Regiões Administrativas do Distrito Federal (DF)
"""

att_17_cities_locations = [
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

# Nova ordem. O seu algoritmo genético vai encontrar a melhor rota,
# mas para inicializar a variável alvo de forma segura, colocamos uma sequência simples.
att_17_cities_order = [
    1, 12, 5, 17, 3, 9, 14, 2, 11, 8, 16, 4, 7, 15, 6, 10, 13, 1
]