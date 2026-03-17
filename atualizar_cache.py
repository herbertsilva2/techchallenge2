import json
import requests
import time
import os

coords_df = [
    (-15.7795, -47.9296), (-16.0160, -48.0682), (-15.8333, -48.0563), (-15.6103, -48.1200), (-15.6580, -47.7925),
    (-15.6216, -47.6521), (-15.7757, -47.7799), (-15.8711, -47.9709), (-15.8127, -48.1038), (-15.8102, -47.9713),
    (-15.7950, -47.9267), (-15.8705, -48.0902), (-16.0036, -47.9872), (-15.9028, -47.7760), (-15.9150, -48.0999),
    (-15.9064, -47.8624), (-15.8814, -48.0169), (-15.7212, -47.8328), (-15.8500, -47.9469), (-15.8394, -48.0289),
    (-15.9039, -48.0381), (-15.8028, -47.9250), (-15.7078, -47.8761), (-15.8864, -47.9542), (-15.7761, -47.9961),
    (-15.6200, -47.8181), (-15.8672, -47.7753), (-15.7483, -47.7633), (-15.8078, -47.9572), (-15.8117, -48.0211),
    (-15.5869, -47.8703), (-15.8203, -48.1364), (-15.8500, -48.0200), (-15.5900, -47.6400), (-15.9189, -48.2436)
]

# Tenta carregar o que já conseguimos baixar antes
cache_rotas = {}
if os.path.exists("rotas_offline.json"):
    with open("rotas_offline.json", "r") as f:
        cache_rotas = json.load(f)

total_pares = len(coords_df) * (len(coords_df) - 1)
rotas_baixadas = 0

print("🔍 A verificar ruas em falta no seu mapa...")

for i in range(len(coords_df)):
    for j in range(len(coords_df)):
        if i != j:
            chave = f"{i}-{j}"

            # Se a rota já existir e não estiver vazia, ignora e avança!
            if chave in cache_rotas and len(cache_rotas[chave]) > 0:
                continue

            # Se estiver a faltar, fazemos o download
            lat1, lon1 = coords_df[i]
            lat2, lon2 = coords_df[j]
            url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"

            try:
                resposta = requests.get(url)
                if resposta.status_code == 200:
                    dados = resposta.json()
                    coordenadas_rua = dados['routes'][0]['geometry']['coordinates']
                    cache_rotas[chave] = coordenadas_rua
                    rotas_baixadas += 1
                    print(f"✅ Rota restaurada: {chave}")
            except Exception:
                pass

            # Pausa MAIOR (meio segundo) para não sermos bloqueados pelo OSRM novamente
            time.sleep(0.5)

        # Salva o ficheiro completo
with open("rotas_offline.json", "w") as f:
    json.dump(cache_rotas, f)

print(f"🎉 Concluído! Conseguimos restaurar {rotas_baixadas} rotas que faltavam.")