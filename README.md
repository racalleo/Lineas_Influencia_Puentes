# Líneas de Influencia - Puentes con Cargas Puntuales

Aplicación web (Streamlit) para calcular líneas de influencia en una viga simplemente apoyada sometida a un tren de cargas puntuales (cargas con distancia fija entre sí, como un vehículo cruzando un puente): momento máximo por el método del eje equidistante (teorema de Barré), reacciones en los apoyos y cortante en una sección, incluyendo la posición más demandante de cada uno.

**Aviso:** los resultados son referenciales. Deben ser verificados por el ingeniero responsable del proyecto. Los autores no asumen responsabilidad por el uso de esta herramienta.

## Qué hace

- **Tren de carga**: defines la intensidad de cada carga y la distancia a la siguiente; la aplicación calcula la resultante `R` y su centroide `xₑ`.
- **Ejes equidistantes (Barré)**: `c₁` y `c₂`, para ubicar el tren en la posición que produce el momento máximo.
- **Momento máximo**: en la sección que definas, con las dos alternativas de posicionamiento (`c₁` o `c₂`).
- **Reacciones en A y B**: para una posición del tren definida directamente por ti (el extremo derecho del tren sobre la viga).
- **Cortante**: en la sección que definas, incluyendo el salto característico de la línea de influencia.
- **Posición más demandante**: además del cálculo en la posición que defines, para reacciones y cortante la aplicación determina la posición del tren que produce el valor máximo, de forma analítica exacta (no por fuerza bruta).

Unidades: MKS práctico (m, ton, ton·m).

## Instalación

Requiere Python 3.9 o superior.

```bash
pip install -r requirements.txt
```

## Uso

```bash
streamlit run app_lineas_influencia.py
```

Se abre en `http://localhost:8501`.

También existe una versión de línea de comandos:

```bash
python influence_lines.py
```

## Estructura

| Archivo | Contenido |
|---|---|
| `app_lineas_influencia.py` | Interfaz Streamlit (pestañas: Tren de carga, Momento, Reacciones, Cortante) |
| `influence_lines.py` | Ecuaciones de líneas de influencia, tren de carga, posicionamiento y dibujos (sin interfaz), más la versión de línea de comandos |
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

Para ubicar el tren de forma que produzca el momento máximo en una sección, se usa el método del eje equidistante: se calcula la resultante `R` y su centroide `xₑ`, y se define un eje a la mitad de distancia entre la resultante y la carga más cercana a su izquierda (`c₁`) o a su derecha (`c₂`); el eje elegido se hace coincidir con la mitad de la luz de la viga.

## Criterios y alcance

- Viga simplemente apoyada (apoyo fijo en A, apoyo móvil en B); no aplica a vigas continuas, en voladizo ni a otros sistemas estructurales.
- El tren de carga se modela como cargas puntuales rígidas con distancia fija entre sí; no incluye carga distribuida ni cargas independientes que se muevan por separado.
- Las cargas del tren que quedan fuera de la longitud de la viga en una posición dada se excluyen del cálculo en esa posición.
- El momento máximo se obtiene con el método del eje equidistante (teorema de Barré), que ubica la posición crítica bajo una de las cargas del tren; es el resultado clásico para vigas simplemente apoyadas bajo cargas móviles.
- La posición más demandante para reacciones y cortante se determina evaluando únicamente los puntos donde la respuesta puede cambiar de pendiente (una carga entra o sale de la viga, o cruza la sección de análisis), ya que la respuesta es lineal a tramos entre esos puntos.
- No se consideran efectos dinámicos, impacto, ni combinaciones de carga distintas al tren definido.

## Referencias

- Hibbeler, R. C. *Análisis Estructural*.
- Kassimali, A. *Análisis Estructural*.
- Barré, J. J. (teorema del eje equidistante para el momento máximo bajo un tren de cargas móviles).

## Licencia

MIT. Ver [LICENSE](LICENSE).
