import json

ALIMENTOS_PATH = "data/alimentos.json"
RECETAS_PATH = "data/recetas.json"

with open(ALIMENTOS_PATH, "r", encoding="utf-8") as f:
    alimentos_data = json.load(f)

alimentos = {
    item["id"]: item["por_100g"] for item in alimentos_data.get("alimentos", [])
}

with open(RECETAS_PATH, "r", encoding="utf-8") as f:
    recetas_data = json.load(f)

for receta in recetas_data.get("recetas", []):
    proteina = 0.0
    carbo = 0.0
    grasas = 0.0
    calorias = 0.0
    for ing in receta.get("ingredientes", []):
        aid = ing.get("alimento_id")
        qty = ing.get("cantidad", 0)  # gramos
        if aid not in alimentos:
            print(
                f'Warning: alimento_id {aid} no encontrado para receta {receta.get("id")}'
            )
            continue
        por100 = alimentos[aid]
        p = por100.get("proteina", 0)
        c = por100.get("carbohidratos", por100.get("carbos", 0))
        g = por100.get("grasas", 0)
        cal = por100.get("calorias", 0)
        factor = qty / 100.0
        proteina += p * factor
        carbo += c * factor
        grasas += g * factor
        calorias += cal * factor
    receta["macros_totales"] = {
        "proteina": round(proteina, 2),
        "carbos": round(carbo, 2),
        "grasas": round(grasas, 2),
    }
    receta["calorias_totales"] = round(calorias, 2)

with open(RECETAS_PATH, "w", encoding="utf-8") as f:
    json.dump(recetas_data, f, ensure_ascii=False, indent=2)

print("Macros calculados y `data/recetas.json` actualizado.")
