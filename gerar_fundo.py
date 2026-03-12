import folium

# Cria um mapa centralizado no Distrito Federal (Brasília)
# Usamos o estilo 'cartodbpositron' porque ele é claro, sem muitas cores,
# o que faz as linhas azuis e pontos vermelhos do seu caixeiro viajante se destacarem muito mais!
mapa_fundo = folium.Map(
    location=[-15.7950, -47.9296], # Coordenadas de Brasília/DF
    zoom_start=20,                 # Zoom aproximado para focar apenas no DF
    tiles='cartodbpositron'
)

mapa_fundo.save("mapa_limpo.html")
print("Pronto! Abra o arquivo mapa_limpo.html no seu navegador.")