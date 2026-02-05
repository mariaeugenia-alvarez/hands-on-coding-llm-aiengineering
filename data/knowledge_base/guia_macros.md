# Cómo calcular los MACROS

Este documento detalla dos fórmulas para determinar el consumo calórico diario y la distribución de macronutrientes según objetivos personales.

---

## Método 1: Fórmula de Constante Directa

### 1. Cálculo de Calorías Diarias

La fórmula base para obtener las calorías de mantenimiento es:

$$\text{Calorías de mantenimiento} = \text{Kg} \times 22 \times FA$$

- **Kg:** Kilogramos en ayunas.
- **22:** Constante que no se modifica.
- **FA (Factor de Actividad):** Se determina según el nivel de ejercicio semanal.

**Tabla de Factor de Actividad (FA):**

| Factor de Actividad | Descripción |
| --- | --- |
| 1.2 | Poco o ningún ejercicio |
| 1.4 | Ejercicio ligero (1-3 días) |
| 1.6 | Ejercicio moderado (3-5 días) |
| 1.8 | Ejercicio fuerte (6-7 días) |
| 2.0 | Ejercicio muy fuerte (doble turno 7 días) |

### 2. Ajuste según Objetivo

Una vez obtenidas las calorías diarias, se aplica un porcentaje de ajuste:

**Para Bajar de Peso:**
- **-10%:** Bajar de forma lenta conservando masa muscular.
- **-20%:** Ritmo moderado, seguro para mantener músculo.
- **-30%:** Ritmo rápido o para personas con porcentaje de grasa elevado.

**Para Subir de Peso:**
- **+10%:** Recomendado para avanzados o personas con tendencia a engordar.
- **+15%:** Opción para subir un poco más rápido.
- **+20%:** Para personas con dificultad para subir de peso (ectomorfos). Se debe tener cuidado para no subir exceso de grasa.

---

## Cómo sacar los Macros

### Tabla de Aporte Calórico

| Macronutriente | Kcal por gramo |
| --- | --- |
| Proteína | 4 kcal |
| Carbohidrato | 4 kcal |
| Grasa | 9 kcal |

### Distribución por Kilogramo de Peso

| Macros | Mínimo | Máximo |
| --- | --- | --- |
| Proteína | 1.8 g/kg | 2.5 g/kg (pérdida de grasa) |
| Grasas | 0.5 g/kg (pérdida de grasa) | 1.5 g/kg (ganar masa) |
| Carbohidratos | El restante | — |

---

## Ejemplo Práctico (Déficit del 10%)

**Datos de ejemplo:** 82.5 kg con actividad moderada (FA = 1.6).

- **Mantenimiento:** $82.5 \, \text{kg} \times 22 \times 1.6 = 2904 \, \text{kcal}$
- **Déficit 10%:** $2904 \times 0.10 = 290 \, \text{kcal}$ menos
- **Total Objetivo:** **2614 kcal diarias**

**Distribución de Macros:**

- **Proteína (2.5 g/kg):** $82.5\times 2.5 = 206 \, \text{g}$ (**206×4 = 824 kcal**)
- **Grasa (0.5 g/kg):** $82.5\times 0.5 = 41 \, \text{g}$ (**41×9 = 369 kcal**)
- **Carbohidratos:** Calorías restantes $= 2614 - 824 - 369 = 1421 \, \text{kcal}$ → $1421/4 = \mathbf{355 \, g}$

---

## Método 2: Fórmula Harris-Benedict

Este método es más preciso al incluir edad y altura.

### 1. Cálculo del Metabolismo Basal (BMR)

- **Mujeres:** $$\mathrm{BMR} = 655.0955 + (9.5634 \times \text{peso}) + (1.8496 \times \text{altura}) - (4.6756 \times \text{edad})$$
- **Hombres:** $$\mathrm{BMR} = 66.473 + (13.7516 \times \text{peso}) + (5.0033 \times \text{altura}) - (6.755 \times \text{edad})$$

> Nota: Peso en kg, altura en cm, edad en años.

### 2. Factor de Actividad (FA)

| Nivel de Actividad | Factor |
| --- | --- |
| Sedentario | 1.2 |
| Actividad Ligera (1-3 días) | 1.375 |
| Actividad Moderada (3-5 días) | 1.55 |
| Actividad Intensa (6-7 días) | 1.725 |
| Actividad Muy Intensa (Atletas) | 1.9 |

**Cálculo final:** $$\text{Calorías diarias} = \mathrm{BMR} \times FA$$
