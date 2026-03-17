import json
import requests
import time

# As suas 35 coordenadas de GPS exatas
coords_df = [
    (-15.7795, -47.9296), (-16.0160, -48.0682), (-15.8333, -48.0563), (-15.6103, -48.1200), (-15.6580, -47.7925),
    (-15.6216, -47.6521), (-15.7757, -47.7799), (-15.8711, -47.9709), (-15.8127, -48.1038), (-15.8102, -47.9713),
    (-15.7950, -47.9267), (-15.8705, -48.0902), (-16.0036, -47.9872), (-15.9028, -47.7760), (-15.9150, -48.0999),
    (-15.9064, -47.8624), (-15.8814, -48.0169), (-15.7212, -47.8328), (-15.8500, -47.9469), (-15.8394, -48.0289),
    (-15.9039, -48.0381), (-15.8028, -47.9250), (-15.7078, -47.8761), (-15.8864, -47.9542), (-15.7761, -47.9961),
    (-15.6200, -47.8181), (-15.8672, -47.7753), (-15.7483, -47.7633), (-15.8078, -47.9572), (-15.8117, -48.0211),
    (-15.5869, -47.8703), (-15.8203, -48.1364), (-15.8500, -48.0200), (-15.5900, -47.6400), (-15.9189, -48.2436)
]

cache_rotas = {}
total_pares = len(coords_df) * (len(coords_df) - 1)
contador = 0

print("A baixar mapa de ruas do DF... Isso pode demorar uns 5 a 10 minutos.")
print("Só precisa de fazer isto uma vez!")

for i in range(len(coords_df)):
    for j in range(len(coords_df)):
        if i != j:
            lat1, lon1 = coords_df[i]
            lat2, lon2 = coords_df[j]

            # Pedir a rota real de carro ao OSRM
            url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
            try:
                resposta = requests.get(url)
                if resposta.status_code == 200:
                    dados = resposta.json()
                    coordenadas_rua = dados['routes'][0]['geometry']['coordinates']
                    # Guardar na nossa "memória" com a chave "i-j"
                    cache_rotas[f"{i}-{j}"] = coordenadas_rua
            except Exception as e:
                pass

            contador += 1
            if contador % 50 == 0:
                print(f"Progresso: {contador}/{total_pares} rotas baixadas...")

            time.sleep(0.1)  # Pausa para não bloquear a API pública

# Guardar tudo num ficheiro local offline
with open("rotas_offline.json", "w") as f:
    json.dump(cache_rotas, f)

print("✅ Concluído! Ficheiro 'rotas_offline.json' criado com sucesso.")