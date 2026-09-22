# Líneas de Influencia - Puentes con Cargas Puntuales

Aplicación en Streamlit para calcular líneas de influencia en una viga simplemente apoyada sometida a un tren de cargas puntuales (cargas con distancia fija entre sí, como un vehículo cruzando un puente).

Calcula:

- **Momento máximo** en una sección, ubicando el tren mediante el método del eje equidistante (teorema de Barré), con las dos alternativas de posicionamiento (c₁ y c₂).
- **Reacciones en los apoyos A y B**, para una posición del tren definida por el usuario.
- **Cortante** en una sección definida por el usuario, incluyendo el salto en la línea de influencia.
- **Posición más demandante**: para reacciones y cortante, además del cálculo en la posición que defines, la aplicación determina la posición del tren que produce el valor máximo (de forma analítica exacta, no por fuerza bruta).

Sistema de unidades: MKS práctico (longitudes en metros, cargas en toneladas, momentos en ton·m).

## Requisitos

- Python 3.9 o superior

## Instalación y uso

```bash
git clone https://github.com/RACALLEO/Lineas_Influencia_Puentes.git
cd Lineas_Influencia_Puentes
pip install -r requirements.txt
streamlit run app_lineas_influencia.py
```

Esto abre la aplicación en el navegador en `http://localhost:8501`.

## Estructura del proyecto

| Archivo | Contenido |
|---|---|
| `app_lineas_influencia.py` | Interfaz gráfica (pestañas: Tren de carga, Momento, Reacciones, Cortante) |
| `influence_lines.py` | Lógica de cálculo (líneas de influencia, tren de carga, posicionamiento, dibujos) y una versión de línea de comandos (`python influence_lines.py`) |
| `requirements.txt` | Dependencias de Python |

## Fundamento teórico

Las líneas de influencia de reacciones, cortante y momento para una viga simplemente apoyada se obtienen evaluando la respuesta ante una carga unitaria móvil:

```
RA(x) = (L - x) / L
RB(x) = x / L

V(x) = -x / L         si x < a
V(x) = (L - x) / L    si x > a

M(x) = x (L - a) / L  si x <= a
M(x) = a (L - x) / L  si x >= a
```

La respuesta real ante el tren de carga es `suma(Pᵢ · ordenada(xᵢ))` para cada carga del tren.

Para ubicar el tren de forma que produzca el momento máximo en una sección, se usa el método del eje equidistante: se calcula la resultante `R` y su centroide `xₑ`, y se define un eje a la mitad de distancia entre la resultante y la carga más cercana a su izquierda (c₁) o a su derecha (c₂); el eje elegido se hace coincidir con la mitad de la luz de la viga.

## Licencia

MIT. Ver [LICENSE](LICENSE).
