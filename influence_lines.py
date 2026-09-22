"""
Viga simplemente apoyada (A: apoyo fijo izquierdo, B: apoyo movil derecho)
bajo un tren de cargas puntuales (cargas con distancia fija entre si, que se
desplazan juntas sobre la viga).

Sistema de unidades: MKS practico para estructuras -> longitudes en metros (m),
cargas en toneladas (ton). Los momentos resultan en ton*m.

Flujo:
1. Longitud de la viga L.
2. Definir el tren de carga: distancias entre cargas consecutivas e
   intensidad de cada carga.
3. Calcular la resultante R del tren y la posicion de su centroide xe
   (medida desde el origen del tren, la carga mas a la izquierda).
4. Calcular los dos ejes equidistantes (metodo de Barre): c1 (entre la
   resultante y la carga mas cercana a su izquierda) y c2 (entre la
   resultante y la carga mas cercana a su derecha).
5. Ubicar el tren sobre la viga haciendo coincidir el eje equidistante (c1 o
   c2) con la mitad de la luz L/2; las cargas que caen fuera de la viga se
   descartan. Con la posicion resultante se calcula el momento en una seccion
   a una distancia "a" desde el apoyo A, usando la linea de influencia de M:
        M(x) = x (L - a) / L   si x <= a
        M(x) = a (L - x) / L   si x >= a
   y M_total = suma( Pi * M(xi) ).
6. Reacciones en A y B: el usuario define la posicion del extremo derecho
   del tren sobre la viga (posicionamiento independiente de c1/c2). Con esa
   posicion se calculan las reacciones usando las lineas de influencia:
        RA(x) = (L - x) / L
        RB(x) = x / L
   y RA_total = suma( Pi * RA(xi) ), RB_total = suma( Pi * RB(xi) ).
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon


# ---------------------------------------------------------------------------
# Lineas de influencia
# ---------------------------------------------------------------------------

def il_ra(x, L):
    """Influencia de la reaccion en A: RA(x) = (L - x) / L"""
    return (L - x) / L


def il_rb(x, L):
    """Influencia de la reaccion en B: RB(x) = x / L"""
    return x / L


def il_v(x, a, L):
    """Influencia del cortante en la seccion x = a.

    x < a  -> V(x) = -x / L
    x > a  -> V(x) = (L - x) / L
    x == a -> discontinuidad (salto de magnitud 1); se devuelven ambos limites.
    """
    if x < a:
        return -x / L
    elif x > a:
        return (L - x) / L
    else:
        v_izq = -a / L
        v_der = (L - a) / L
        return v_izq, v_der


def il_m(x, a, L):
    """Influencia del momento en la seccion x = a.

    x <= a -> M(x) = x (L - a) / L
    x >= a -> M(x) = a (L - x) / L
    (ambas coinciden en x = a: M(a) = a (L - a) / L)
    """
    if x <= a:
        return x * (L - a) / L
    else:
        return a * (L - x) / L


# ---------------------------------------------------------------------------
# Tren de carga: resultante, centroide y ejes equidistantes
# ---------------------------------------------------------------------------

def build_load_train(magnitudes, distances):
    """Construye el tren de carga a partir de las magnitudes Pi [ton] y las
    distancias [m] entre cargas consecutivas (n-1 distancias para n cargas).

    Devuelve una lista [(si, Pi), ...] con si medido desde el origen del
    tren (la carga mas a la izquierda, s1 = 0), en el mismo orden en que se
    ingresaron las cargas (de izquierda a derecha)."""
    n = len(magnitudes)
    if len(distances) != n - 1:
        raise ValueError("Se necesitan exactamente n-1 distancias para n cargas.")
    s = [0.0] * n
    for i in range(1, n):
        s[i] = s[i - 1] + distances[i - 1]
    return list(zip(s, magnitudes))


def resultant_and_centroid(train):
    """R = suma de las cargas. xe = suma(Pi * si) / R, medido desde el
    origen del tren (izquierda)."""
    R = sum(P for _, P in train)
    if R == 0:
        raise ValueError("La resultante del tren de carga no puede ser cero.")
    x_e = sum(s * P for s, P in train) / R
    return R, x_e


def equidistant_axes(train, x_e):
    """c1: eje a la mitad de la distancia entre la resultante y la carga mas
    cercana a su IZQUIERDA. c2: idem con la carga mas cercana a su DERECHA.
    Ambos medidos desde el origen del tren."""
    s_values = sorted(s for s, _ in train)
    s_left = max((s for s in s_values if s <= x_e), default=s_values[0])
    s_right = min((s for s in s_values if s >= x_e), default=s_values[-1])
    c1 = (x_e + s_left) / 2
    c2 = (x_e + s_right) / 2
    return c1, c2, s_left, s_right


def _place_train(train, origen_beam, L):
    """Ubica el tren de carga sobre la viga dado el origen del tren (x=0 del
    tren) en coordenadas de la viga. Devuelve (incluidas, excluidas)."""
    incluidas, excluidas = [], []
    for s, P in train:
        x_beam = origen_beam + s
        if -1e-9 <= x_beam <= L + 1e-9:
            incluidas.append((min(max(x_beam, 0.0), L), P))
        else:
            excluidas.append((x_beam, P))
    return incluidas, excluidas


def position_train_on_beam(train, c, L):
    """Ubica el tren de carga sobre la viga de modo que el eje equidistante
    c (medido desde el origen del tren) coincida con L/2. Devuelve:
      - incluidas: [(x_beam, P), ...] cargas dentro de [0, L]
      - excluidas: [(x_beam, P), ...] cargas que caen fuera de la viga
      - origen_beam: posicion en la viga del origen del tren (x=0 del tren)
    """
    origen_beam = L / 2 - c
    incluidas, excluidas = _place_train(train, origen_beam, L)
    return incluidas, excluidas, origen_beam


def position_train_by_right_end(train, x_derecho, L):
    """Ubica el tren de carga sobre la viga de modo que la carga mas a la
    derecha del tren quede en x = x_derecho (posicion definida por el
    usuario, medida desde A). Devuelve (incluidas, excluidas, origen_beam)
    con el mismo formato que position_train_on_beam."""
    s_last = max(s for s, _ in train)
    origen_beam = x_derecho - s_last
    incluidas, excluidas = _place_train(train, origen_beam, L)
    return incluidas, excluidas, origen_beam


# ---------------------------------------------------------------------------
# Calculo de momento, cortante y reacciones
# ---------------------------------------------------------------------------

def compute_moment(L, a, loads):
    rows = []
    M_total = 0.0
    for x, P in loads:
        m_ord = il_m(x, a, L)
        M_total += P * m_ord
        rows.append({"x": x, "P": P, "m_ord": m_ord})
    return {"rows": rows, "M": M_total}


def compute_shear(L, a, loads):
    rows = []
    V_izq_total = V_der_total = 0.0
    for x, P in loads:
        v_ord = il_v(x, a, L)
        if isinstance(v_ord, tuple):
            v_izq_ord, v_der_ord = v_ord
        else:
            v_izq_ord = v_der_ord = v_ord
        V_izq_total += P * v_izq_ord
        V_der_total += P * v_der_ord
        rows.append({
            "x": x, "P": P,
            "v_izq_ord": v_izq_ord, "v_der_ord": v_der_ord,
            "en_seccion": abs(x - a) < 1e-9,
        })
    return {"rows": rows, "V_izq": V_izq_total, "V_der": V_der_total}


def compute_reactions(L, loads):
    rows = []
    RA_total = RB_total = 0.0
    for x, P in loads:
        ra_ord = il_ra(x, L)
        rb_ord = il_rb(x, L)
        RA_total += P * ra_ord
        RB_total += P * rb_ord
        rows.append({"x": x, "P": P, "ra_ord": ra_ord, "rb_ord": rb_ord})
    return {"rows": rows, "RA": RA_total, "RB": RB_total}


# ---------------------------------------------------------------------------
# Busqueda de la posicion critica (posicion del extremo derecho del tren que
# maximiza la reaccion en A, en B, o el cortante en una seccion).
#
# RA, RB y V (para cargas incluidas) son funciones LINEALES A TRAMOS de la
# posicion del tren: cada carga aporta una pendiente constante mientras esta
# sobre la viga, y el valor total solo tiene quiebres/saltos exactamente
# donde una carga entra o sale de la viga, o (para V) cruza la seccion de
# analisis. Por lo tanto el maximo siempre ocurre en uno de esos puntos
# exactos, sin necesidad de recorrer todo el rango con una malla fina.
# ---------------------------------------------------------------------------

def _candidate_positions(train, L, extra=None):
    """Genera las posiciones candidatas del extremo derecho del tren donde
    puede estar el maximo: los limites del dominio [0, L] y los puntos
    exactos donde alguna carga entra o sale de la viga."""
    s_values = [s for s, _ in train]
    s_last = max(s_values)
    candidatos = {0.0, L}
    for s in s_values:
        candidatos.add(min(max(s_last - s, 0.0), L))
        candidatos.add(min(max(s_last - s + L, 0.0), L))
    if extra:
        for x in extra:
            candidatos.add(min(max(x, 0.0), L))
    return sorted(candidatos)


def find_max_reaction(train, L, kind):
    """Encuentra la posicion del extremo derecho del tren de carga
    (0 <= x <= L) que maximiza la reaccion 'RA' o 'RB'.

    Devuelve (x_optimo, valor_maximo, cargas_incluidas_en_esa_posicion)."""
    best_x = best_val = best_loads = None
    for x_right in _candidate_positions(train, L):
        incluidas, _, _ = position_train_by_right_end(train, x_right, L)
        if not incluidas:
            continue
        reacciones = compute_reactions(L, incluidas)
        val = reacciones[kind]
        if best_val is None or val > best_val:
            best_val, best_x, best_loads = val, x_right, incluidas
    return best_x, best_val, best_loads


def find_max_shear(train, L, a):
    """Encuentra la posicion del extremo derecho del tren de carga
    (0 <= x <= L) que maximiza el cortante en la seccion x = a.

    Devuelve (x_optimo, valor_maximo, cargas_incluidas_en_esa_posicion)."""
    s_values = [s for s, _ in train]
    s_last = max(s_values)
    extra = [a + s_last - s for s in s_values]
    best_x = best_val = best_loads = None
    for x_right in _candidate_positions(train, L, extra=extra):
        incluidas, _, _ = position_train_by_right_end(train, x_right, L)
        if not incluidas:
            continue
        corte = compute_shear(L, a, incluidas)
        val = max(corte["V_izq"], corte["V_der"])
        if best_val is None or val > best_val:
            best_val, best_x, best_loads = val, x_right, incluidas
    return best_x, best_val, best_loads


# ---------------------------------------------------------------------------
# Graficos
# ---------------------------------------------------------------------------

def plot_influence_line_m(L, a, loads, result):
    """Linea de influencia de M en x=a, con las ordenadas de cada carga
    marcadas."""
    n_pts = 400
    xs = [L * i / n_pts for i in range(n_pts + 1)]
    ys = [il_m(x, a, L) for x in xs]

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(xs, ys, color="seagreen")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(a, color="gray", linestyle="--", linewidth=0.8)
    ax.set_title(f"Linea de influencia de $M$ en la seccion x=a={a:.3g} m")
    ax.set_xlabel("x (posicion de la carga unitaria desde A) [m]")
    ax.set_ylabel("$M(x)$ [m]")
    ax.grid(True, linestyle="--", alpha=0.5)
    for r in result["rows"]:
        ax.plot(r["x"], r["m_ord"], "o", color="red")
        ax.annotate(f"P={r['P']:.2f} ton\n({r['x']:.2f}, {r['m_ord']:.3f})",
                    (r["x"], r["m_ord"]), textcoords="offset points",
                    xytext=(5, 8), fontsize=8, color="red")
    fig.tight_layout()
    return fig


def plot_influence_line_v(L, a, loads, result):
    """Linea de influencia de V en x=a, con el salto en la seccion y las
    ordenadas de cada carga marcadas."""
    n_pts = 400
    xs = [L * i / n_pts for i in range(n_pts + 1)]
    xs_left = [x for x in xs if x <= a]
    xs_right = [x for x in xs if x >= a]
    v_left = [il_v(x, a, L) for x in xs_left]
    v_right = [il_v(x, a, L) for x in xs_right]
    v_left = [v[0] if isinstance(v, tuple) else v for v in v_left]
    v_right = [v[1] if isinstance(v, tuple) else v for v in v_right]

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(xs_left, v_left, color="darkorange")
    ax.plot(xs_right, v_right, color="darkorange")
    ax.plot([a, a], [-a / L, (L - a) / L], color="darkorange", linestyle=":")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(a, color="gray", linestyle="--", linewidth=0.8)
    ax.set_title(f"Linea de influencia de $V$ en la seccion x=a={a:.3g} m")
    ax.set_xlabel("x (posicion de la carga unitaria desde A) [m]")
    ax.set_ylabel("$V(x)$")
    ax.grid(True, linestyle="--", alpha=0.5)
    for r in result["rows"]:
        y = r["v_der_ord"] if r["x"] >= a else r["v_izq_ord"]
        ax.plot(r["x"], y, "o", color="red")
        ax.annotate(f"P={r['P']:.2f} ton\n({r['x']:.2f}, {y:.3f})",
                    (r["x"], y), textcoords="offset points",
                    xytext=(5, 8), fontsize=8, color="red")
    fig.tight_layout()
    return fig


def plot_influence_lines_reactions(L, loads, result):
    """Lineas de influencia de RA y RB, con las ordenadas de cada carga
    marcadas."""
    n_pts = 400
    xs = [L * i / n_pts for i in range(n_pts + 1)]
    ra_ys = [il_ra(x, L) for x in xs]
    rb_ys = [il_rb(x, L) for x in xs]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    def style_axis(ax, title, ylabel):
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title(title)
        ax.set_xlabel("x (posicion de la carga unitaria desde A) [m]")
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle="--", alpha=0.5)

    def mark_loads(ax, ord_key):
        for r in result["rows"]:
            y = r[ord_key]
            ax.plot(r["x"], y, "o", color="red")
            ax.annotate(f"P={r['P']:.2f}\n({r['x']:.2f}, {y:.3f})",
                        (r["x"], y), textcoords="offset points",
                        xytext=(5, 8), fontsize=8, color="red")

    axes[0].plot(xs, ra_ys, color="steelblue")
    style_axis(axes[0], "Influencia de $R_A$", "$R_A(x)$")
    mark_loads(axes[0], "ra_ord")

    axes[1].plot(xs, rb_ys, color="steelblue")
    style_axis(axes[1], "Influencia de $R_B$", "$R_B(x)$")
    mark_loads(axes[1], "rb_ord")

    fig.tight_layout()
    return fig


def draw_load_train_diagram(train):
    """Esquema del tren de carga aislado (sin viga): cada carga como flecha
    con su magnitud, y las distancias entre cargas consecutivas dibujadas
    como cotas (linea con flechas <-> y texto), al estilo de un plano."""

    s_values = [s for s, _ in train]
    P_values = [P for _, P in train]
    span = max(s_values) - min(s_values)
    u = span * 0.06 if span > 1e-9 else 0.5  # unidad base

    fig, ax = plt.subplots(figsize=(max(8.0, span / 1.1 + 2.5), 3.8))

    baseline_y = 0.0
    ax.plot([min(s_values) - u, max(s_values) + u], [baseline_y, baseline_y],
            color="black", linewidth=1.5, zorder=1)

    arrow_top = 3.0 * u
    for s, P in zip(s_values, P_values):
        ax.annotate("", xy=(s, baseline_y), xytext=(s, arrow_top),
                    arrowprops=dict(arrowstyle="-|>", color="crimson", linewidth=2), zorder=4)
        ax.text(s, arrow_top + 0.2 * u, f"P={P:.2f} ton", ha="center", va="bottom",
                fontsize=9, color="crimson")
        ax.plot([s, s], [baseline_y, -0.4 * u], color="gray", linewidth=0.8, linestyle=":")

    sorted_s = sorted(s_values)
    bottom_y = -0.8 * u

    # --- Cota corrida: distancia entre cargas consecutivas ---
    if len(sorted_s) > 1:
        dim_y = -0.9 * u
        for i in range(len(sorted_s) - 1):
            x0, x1 = sorted_s[i], sorted_s[i + 1]
            for x in (x0, x1):
                ax.plot([x, x], [-0.4 * u, dim_y], color="gray", linewidth=0.8, linestyle=":")
            ax.annotate("", xy=(x1, dim_y), xytext=(x0, dim_y),
                        arrowprops=dict(arrowstyle="<->", color="black", linewidth=1))
            ax.text((x0 + x1) / 2, dim_y - 0.3 * u, f"{x1 - x0:.2f} m",
                    ha="center", va="top", fontsize=8.5)
        bottom_y = dim_y - 0.8 * u

        # --- Cota total del tren ---
        total_dim_y = dim_y - 1.3 * u
        for x in (sorted_s[0], sorted_s[-1]):
            ax.plot([x, x], [dim_y - 0.5 * u, total_dim_y], color="gray",
                    linewidth=0.6, linestyle=":")
        ax.annotate("", xy=(sorted_s[-1], total_dim_y), xytext=(sorted_s[0], total_dim_y),
                    arrowprops=dict(arrowstyle="<->", color="black", linewidth=1))
        ax.text((sorted_s[0] + sorted_s[-1]) / 2, total_dim_y - 0.3 * u,
                f"Longitud total del tren = {sorted_s[-1] - sorted_s[0]:.2f} m",
                ha="center", va="top", fontsize=8.5, fontweight="bold")
        bottom_y = total_dim_y - 0.8 * u

    ax.set_title("Tren de carga", fontsize=11)
    ax.set_xlim(min(s_values) - 1.5 * u, max(s_values) + 1.5 * u)
    ax.set_ylim(bottom_y, arrow_top + 1.0 * u)
    ax.axis("off")
    fig.tight_layout()
    return fig


def draw_train_resultant_diagram(train, R, x_e):
    """Esquema del tren de carga con su resultante R marcada en la posicion
    xe, y la distancia xe dibujada como cota desde el origen del tren
    (la carga mas a la izquierda, s = 0)."""

    s_values = [s for s, _ in train]
    P_values = [P for _, P in train]
    span = max(s_values) - min(s_values)
    u = span * 0.06 if span > 1e-9 else 0.5  # unidad base

    origen = 0.0
    xmin = min(min(s_values), x_e, origen)
    xmax = max(max(s_values), x_e, origen)

    fig, ax = plt.subplots(figsize=(max(8.0, (xmax - xmin) / 1.1 + 2.5), 3.8))

    baseline_y = 0.0
    ax.plot([xmin - u, xmax + u], [baseline_y, baseline_y], color="black",
            linewidth=1.5, zorder=1)

    # --- Cargas del tren (atenuadas, de referencia) ---
    arrow_top = 3.0 * u
    for s, P in zip(s_values, P_values):
        ax.annotate("", xy=(s, baseline_y), xytext=(s, arrow_top * 0.7),
                    arrowprops=dict(arrowstyle="-|>", color="crimson", linewidth=1.4, alpha=0.55),
                    zorder=3)
        ax.text(s, arrow_top * 0.7 + 0.15 * u, f"{P:.2f} ton", ha="center", va="bottom",
                fontsize=7.5, color="crimson", alpha=0.75)
        ax.plot([s, s], [baseline_y, -0.4 * u], color="gray", linewidth=0.6,
                linestyle=":", alpha=0.6)

    # --- Resultante R en xe ---
    r_top = arrow_top * 1.25
    ax.annotate("", xy=(x_e, baseline_y), xytext=(x_e, r_top),
                arrowprops=dict(arrowstyle="-|>", color="navy", linewidth=2.8), zorder=5)
    ax.text(x_e, r_top + 0.2 * u, f"R = {R:.2f} ton", ha="center", va="bottom",
            fontsize=10, color="navy", fontweight="bold")
    ax.plot([x_e, x_e], [baseline_y, -0.4 * u], color="navy", linewidth=0.9, linestyle=":")

    # --- Cota de xe desde el origen del tren ---
    dim_y = -0.9 * u
    ax.plot([origen, origen], [-0.4 * u, dim_y], color="gray", linewidth=0.8, linestyle=":")
    ax.text(origen, -0.25 * u, "0", ha="center", va="top", fontsize=8, color="dimgray")
    if abs(x_e - origen) > 1e-9:
        ax.plot([x_e, x_e], [-0.4 * u, dim_y], color="navy", linewidth=0.8, linestyle=":")
        ax.annotate("", xy=(x_e, dim_y), xytext=(origen, dim_y),
                    arrowprops=dict(arrowstyle="<->", color="navy", linewidth=1.2))
        ax.text((origen + x_e) / 2, dim_y - 0.3 * u, f"$x_e$ = {x_e:.2f} m",
                ha="center", va="top", fontsize=9, color="navy", fontweight="bold")
    else:
        ax.text(origen, dim_y - 0.3 * u, f"$x_e$ = {x_e:.2f} m", ha="center", va="top",
                fontsize=9, color="navy", fontweight="bold")

    ax.set_title("Resultante del tren de carga", fontsize=11)
    ax.set_xlim(xmin - 1.5 * u, xmax + 1.5 * u)
    ax.set_ylim(dim_y - 1.0 * u, r_top + 1.0 * u)
    ax.axis("off")
    fig.tight_layout()
    return fig


def draw_beam_diagram(L, loads, a=None, excluded=None, title=None):
    """Esquema de la viga simplemente apoyada: apoyo fijo en A, apoyo movil
    en B, cargas puntuales (flechas hacia abajo, magnitud en toneladas).

    a: si se indica, dibuja la seccion de analisis 1-1 en x = a.
    excluded: cargas del tren que quedaron fuera de la viga (se listan en el
    titulo/nota, no se dibujan sobre la viga).
    """

    s = max(L * 0.035, 1e-6)  # unidad base para el tamano de los simbolos

    fig, ax = plt.subplots(figsize=(10, 3.8))

    beam_y = 0.0
    ax.plot([0, L], [beam_y, beam_y], color="black", linewidth=5,
             solid_capstyle="butt", zorder=3)

    # --- Apoyo A: articulacion fija (triangulo + rayado de tierra) ---
    tri_a = Polygon(
        [(0, 0), (-s, -1.6 * s), (s, -1.6 * s)],
        closed=True, facecolor="dimgray", edgecolor="black", zorder=2,
    )
    ax.add_patch(tri_a)
    ax.plot([-1.6 * s, 1.6 * s], [-1.6 * s, -1.6 * s], color="black", linewidth=1.2)
    for i in range(-2, 3):
        xh = i * 0.7 * s
        ax.plot([xh, xh - 0.5 * s], [-1.6 * s, -2.2 * s], color="black", linewidth=0.8)

    # --- Apoyo B: apoyo movil (triangulo + rodillos + rayado de tierra) ---
    tri_b = Polygon(
        [(L, 0), (L - s, -1.6 * s), (L + s, -1.6 * s)],
        closed=True, facecolor="dimgray", edgecolor="black", zorder=2,
    )
    ax.add_patch(tri_b)
    roller_y = -1.9 * s
    for dx in (-0.6 * s, 0.6 * s):
        ax.add_patch(Circle((L + dx, roller_y), 0.3 * s, facecolor="dimgray",
                             edgecolor="black", zorder=2))
    ground_y = -2.2 * s
    ax.plot([L - 1.6 * s, L + 1.6 * s], [ground_y, ground_y], color="black", linewidth=1.2)
    for i in range(-2, 3):
        xh = L + i * 0.7 * s
        ax.plot([xh, xh - 0.5 * s], [ground_y, ground_y - 0.6 * s], color="black", linewidth=0.8)

    ax.text(0, -3.0 * s, "A", ha="center", va="top", fontsize=11, fontweight="bold")
    ax.text(L, -3.0 * s, "B", ha="center", va="top", fontsize=11, fontweight="bold")

    # --- Cargas puntuales (flechas hacia abajo) ---
    arrow_top = 4.5 * s
    for i, (x, P) in enumerate(loads):
        # alterna la altura de la flecha si hay cargas muy cercanas en x
        top = arrow_top if i % 2 == 0 else arrow_top * 0.75
        ax.annotate(
            "", xy=(x, beam_y), xytext=(x, top),
            arrowprops=dict(arrowstyle="-|>", color="crimson", linewidth=2),
            zorder=4,
        )
        ax.text(x, top + 0.3 * s, f"P={P:.2f} ton", ha="center", va="bottom",
                fontsize=9, color="crimson")
        ax.text(x, -0.9 * s, f"x={x:.2f} m", ha="center", va="top",
                fontsize=8, color="black", rotation=0)
        ax.plot([x, x], [0, -0.5 * s], color="gray", linewidth=0.8, linestyle=":")

    # --- Seccion de analisis 1-1 en x = a (opcional) ---
    top_label_y = arrow_top
    if a is not None:
        ax.axvline(a, color="royalblue", linestyle="--", linewidth=1.3, zorder=1)
        ax.text(a, arrow_top + 1.2 * s, f"seccion 1-1\na={a:.2f} m", ha="center",
                va="bottom", fontsize=9, color="royalblue")
        top_label_y = arrow_top + 1.2 * s

    # --- Cota de longitud total L ---
    dim_y = ground_y - 1.4 * s
    ax.annotate(
        "", xy=(L, dim_y), xytext=(0, dim_y),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=1),
    )
    ax.text(L / 2, dim_y - 0.4 * s, f"L = {L:.2f} m", ha="center", va="top", fontsize=9)

    if title:
        ax.set_title(title, fontsize=10, color="dimgray")

    if excluded:
        nota = "Excluidas (fuera de la viga): " + ", ".join(
            f"P={P:.2f} ton" for _, P in excluded
        )
        ax.text(L / 2, dim_y - 1.1 * s, nota, ha="center", va="top",
                fontsize=8, color="firebrick")

    ax.set_xlim(-0.08 * L - s, 1.08 * L + s)
    ax.set_ylim(dim_y - 1.9 * s, top_label_y + 2.2 * s)
    ax.set_aspect("auto")
    ax.axis("off")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Entrada de datos (CLI)
# ---------------------------------------------------------------------------

def get_float(prompt, min_val=None, max_val=None):
    while True:
        try:
            val = float(input(prompt))
        except ValueError:
            print("  -> Ingresa un numero valido.")
            continue
        if min_val is not None and val < min_val:
            print(f"  -> El valor debe ser >= {min_val}.")
            continue
        if max_val is not None and val > max_val:
            print(f"  -> El valor debe ser <= {max_val}.")
            continue
        return val


def get_int(prompt, min_val=None):
    while True:
        try:
            val = int(input(prompt))
        except ValueError:
            print("  -> Ingresa un entero valido.")
            continue
        if min_val is not None and val < min_val:
            print(f"  -> El valor debe ser >= {min_val}.")
            continue
        return val


def get_beam_length():
    print("=== 1. Datos de la viga (unidades: m, ton) ===")
    return get_float("Longitud de la viga L [m]: ", min_val=1e-9)


def get_load_train():
    print("\n=== 2. Definir tren de carga (de izquierda a derecha) ===")
    n = get_int("Numero de cargas del tren: ", min_val=1)
    magnitudes = []
    distances = []
    for i in range(1, n + 1):
        P = get_float(f"  Magnitud P{i} [ton]: ")
        magnitudes.append(P)
        if i < n:
            d = get_float(f"  Distancia entre P{i} y P{i + 1} [m]: ", min_val=0.0)
            distances.append(d)
    return build_load_train(magnitudes, distances)


# ---------------------------------------------------------------------------
# Programa principal (CLI)
# ---------------------------------------------------------------------------

def main():
    L = get_beam_length()
    train = get_load_train()

    print("\n=== 3. Resultante y centroide del tren de carga ===")
    R, x_e = resultant_and_centroid(train)
    print(f"R (resultante)  = {R:.4f} ton")
    print(f"xe (centroide)  = {x_e:.4f} m  (desde el origen del tren)")

    print("\n=== 4. Ejes equidistantes ===")
    c1, c2, s_left, s_right = equidistant_axes(train, x_e)
    print(f"c1 (con carga izquierda en x={s_left:.2f} m) = {c1:.4f} m")
    print(f"c2 (con carga derecha  en x={s_right:.2f} m) = {c2:.4f} m")

    print("\n=== 5. Posicionar el tren sobre la viga y calcular momento ===")
    a = get_float(f"Posicion de la seccion de analisis a [m] (0 <= a <= {L}): ",
                  min_val=0.0, max_val=L)
    print("Elige la alternativa de posicionamiento:")
    print("  1) c1 (con la carga mas cercana a la izquierda de la resultante)")
    print("  2) c2 (con la carga mas cercana a la derecha de la resultante)")
    opcion = get_int("Opcion [1/2]: ", min_val=1)
    c_elegido = c1 if opcion == 1 else c2

    incluidas, excluidas, origen_beam = position_train_on_beam(train, c_elegido, L)
    resultado = compute_moment(L, a, incluidas)

    print(f"\nOrigen del tren sobre la viga: x = {origen_beam:.4f} m")
    if excluidas:
        print("Cargas excluidas (fuera de la viga):")
        for x, P in excluidas:
            print(f"  P={P:.2f} ton en x={x:.2f} m")
    print(f"\nMomento en x=a={a:.2f} m  ->  M = {resultado['M']:.4f} ton*m")

    draw_beam_diagram(L, incluidas, a=a, excluded=excluidas)
    plot_influence_line_m(L, a, incluidas, resultado)

    print("\n=== 6. Reacciones en A y B ===")
    x_derecho = get_float(
        f"Posicion del extremo derecho del tren sobre la viga [m] (0 <= x <= {L}): ",
        min_val=0.0, max_val=L,
    )
    inc_r, exc_r, origen_r = position_train_by_right_end(train, x_derecho, L)
    reacciones = compute_reactions(L, inc_r)

    print(f"\nOrigen del tren sobre la viga: x = {origen_r:.4f} m")
    if exc_r:
        print("Cargas excluidas (fuera de la viga):")
        for x, P in exc_r:
            print(f"  P={P:.2f} ton en x={x:.2f} m")
    print(f"\nRA = {reacciones['RA']:.4f} ton")
    print(f"RB = {reacciones['RB']:.4f} ton")

    draw_beam_diagram(L, inc_r, excluded=exc_r, title="Tren de carga para calculo de reacciones")
    plot_influence_lines_reactions(L, inc_r, reacciones)

    print("\n=== 7. Cortante en la seccion de analisis ===")
    x_derecho_v = get_float(
        f"Posicion del extremo derecho del tren sobre la viga [m] (0 <= x <= {L}): ",
        min_val=0.0, max_val=L,
    )
    a_v = get_float(f"Posicion de la seccion de analisis a [m] (0 <= a <= {L}): ",
                     min_val=0.0, max_val=L)
    inc_v, exc_v, origen_v = position_train_by_right_end(train, x_derecho_v, L)
    corte = compute_shear(L, a_v, inc_v)

    print(f"\nOrigen del tren sobre la viga: x = {origen_v:.4f} m")
    if exc_v:
        print("Cargas excluidas (fuera de la viga):")
        for x, P in exc_v:
            print(f"  P={P:.2f} ton en x={x:.2f} m")
    if abs(corte["V_izq"] - corte["V_der"]) < 1e-9:
        print(f"\nV en x=a={a_v:.2f} m  ->  V = {corte['V_izq']:.4f} ton")
    else:
        print(f"\nV en x=a={a_v:.2f} m (lado izq., x -> a-) = {corte['V_izq']:.4f} ton")
        print(f"V en x=a={a_v:.2f} m (lado der., x -> a+) = {corte['V_der']:.4f} ton")

    draw_beam_diagram(L, inc_v, a=a_v, excluded=exc_v,
                       title="Tren de carga para calculo de cortante")
    plot_influence_line_v(L, a_v, inc_v, corte)
    plt.show()


if __name__ == "__main__":
    main()
