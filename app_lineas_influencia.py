"""
Interfaz grafica (Streamlit) para lineas de influencia de una viga
simplemente apoyada bajo un tren de cargas: momento maximo (metodo del eje
equidistante / teorema de Barre), reacciones en los apoyos y cortante.

Ejecutar con:
    streamlit run app_lineas_influencia.py
"""

import pandas as pd
import streamlit as st

import influence_lines as il

st.set_page_config(page_title="Lineas de Influencia - Puentes con Cargas Puntuales", layout="wide")

st.title("Líneas de Influencia - Puentes con Cargas Puntuales")
st.caption("Sistema de unidades - MKS")

tab_tren, tab_momento, tab_reacciones, tab_cortante = st.tabs([
    "Tren de carga", "Momento", "Reacciones", "Cortante",
])

# ---------------------------------------------------------------------------
# Tab: Tren de carga (viga, definicion del tren, resultante/centroide,
# ejes equidistantes)
# ---------------------------------------------------------------------------

with tab_tren:
    st.subheader("Datos de la viga")
    L = st.number_input(
        "Longitud de la viga L [m]",
        min_value=0.01, value=10.0, step=0.01, format="%.2f",
    )

    st.subheader("Definir tren de carga")
    st.caption(
        "Ingresa las cargas en orden de izquierda a derecha del tren de carga: la "
        "intensidad de cada carga y la distancia a la carga siguiente. La distancia "
        "de la ultima fila no se usa (no hay carga siguiente)."
    )

    default_train = pd.DataFrame({
        "P": [5.0, 3.0, 10.0],
        "d": [2.0, 3.0, 0.0],
    })
    train_df = st.data_editor(
        default_train,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "P": st.column_config.NumberColumn("Pᵢ [ton]", step=0.01, format="%.2f"),
            "d": st.column_config.NumberColumn(
                "Distancia a la carga siguiente [m]", min_value=0.0, step=0.01, format="%.2f",
            ),
        },
    ).dropna()

    magnitudes = train_df["P"].astype(float).tolist()
    distancias = train_df["d"].astype(float).tolist()[:-1] if len(train_df) > 1 else []

    if len(train_df) == 0:
        st.warning("Agrega al menos una carga al tren.")
        st.stop()
    if any(d < 0 for d in distancias):
        st.error("Las distancias entre cargas no pueden ser negativas.")
        st.stop()

    train = il.build_load_train(magnitudes, distancias)

    st.pyplot(il.draw_load_train_diagram(train))

    try:
        R, x_e = il.resultant_and_centroid(train)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    st.subheader("Resultante y centroide")
    r_col, xe_col = st.columns(2)
    r_col.metric("R (resultante) [ton]", f"{R:.4f}")
    xe_col.metric("xₑ (centroide, desde el origen del tren) [m]", f"{x_e:.4f}")

    st.pyplot(il.draw_train_resultant_diagram(train, R, x_e))

    st.subheader("Ejes equidistantes")
    c1, c2, s_left, s_right = il.equidistant_axes(train, x_e)
    st.caption(
        "c₁: a la mitad entre la resultante y la carga mas cercana a su izquierda.  "
        "c₂: a la mitad entre la resultante y la carga mas cercana a su derecha.  "
        "Ambos medidos desde el origen del tren (la carga mas a la izquierda)."
    )
    e1, e2 = st.columns(2)
    e1.metric(f"c₁ [m]  (carga vecina en x={s_left:.2f} m)", f"{c1:.4f}")
    e2.metric(f"c₂ [m]  (carga vecina en x={s_right:.2f} m)", f"{c2:.4f}")

# ---------------------------------------------------------------------------
# Tab: Momento (metodo del eje equidistante)
# ---------------------------------------------------------------------------

with tab_momento:
    st.subheader("Tren de carga sobre la viga")
    st.caption(
        "El tren se ubica sobre la viga haciendo coincidir el eje equidistante "
        "(c₁ o c₂) con L/2. Las cargas que caen fuera de la viga se descartan."
    )

    inc_c1, exc_c1, origen_c1 = il.position_train_on_beam(train, c1, L)
    inc_c2, exc_c2, origen_c2 = il.position_train_on_beam(train, c2, L)

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("**Alternativa con c₁**")
        fig_c1 = il.draw_beam_diagram(L, inc_c1, excluded=exc_c1, title="c1 alineado con L/2")
        st.pyplot(fig_c1)
    with col_c2:
        st.markdown("**Alternativa con c₂**")
        fig_c2 = il.draw_beam_diagram(L, inc_c2, excluded=exc_c2, title="c2 alineado con L/2")
        st.pyplot(fig_c2)

    st.subheader("Momento en la seccion de analisis")
    a_col, choice_col = st.columns(2)
    with a_col:
        a = st.number_input(
            "Posicion de la seccion de analisis a [m] (desde A, origen de la viga)",
            min_value=0.0, max_value=float(L), value=min(4.0, float(L)),
            step=0.01, format="%.2f",
        )
    with choice_col:
        opcion = st.radio(
            "Condicion de carga a usar para el calculo",
            options=["c₁", "c₂"],
            horizontal=True,
        )

    if opcion == "c₁":
        incluidas, excluidas = inc_c1, exc_c1
    else:
        incluidas, excluidas = inc_c2, exc_c2

    if not incluidas:
        st.error("Con esta alternativa, todas las cargas del tren quedan fuera de la viga.")
        st.stop()

    resultado = il.compute_moment(L, a, incluidas)

    if excluidas:
        st.warning(
            "Cargas excluidas (fuera de la viga): " +
            ", ".join(f"P={P:.2f} ton en x={x:.2f} m" for x, P in excluidas)
        )

    st.metric(f"Momento maximo en x=a={a:.2f} m  (con {opcion}) [ton*m]", f"{resultado['M']:.4f}")

    st.markdown("**Ordenadas de influencia por carga**")
    tabla = pd.DataFrame([
        {"xᵢ [m]": r["x"], "Pᵢ [ton]": r["P"], "M(xᵢ) [m]": r["m_ord"],
         "Pᵢ x M(xᵢ) [ton*m]": r["P"] * r["m_ord"]}
        for r in resultado["rows"]
    ])
    st.dataframe(tabla, use_container_width=True)

    st.markdown("**Viga con el tren de carga posicionado y seccion de analisis**")
    fig_final = il.draw_beam_diagram(L, incluidas, a=a, excluded=excluidas,
                                      title=f"Alternativa {opcion} - M = {resultado['M']:.4f} ton*m")
    st.pyplot(fig_final)

    st.markdown("**Linea de influencia de M en la seccion a**")
    fig_il = il.plot_influence_line_m(L, a, incluidas, resultado)
    st.pyplot(fig_il)

# ---------------------------------------------------------------------------
# Tab: Reacciones en A y B
# ---------------------------------------------------------------------------

with tab_reacciones:
    st.subheader("Posicion del tren sobre la viga")
    st.caption(
        "Se usa el mismo tren de carga, pero aqui la posicion sobre la viga no "
        "depende de c₁/c₂: defines directamente la posicion de la carga mas a la "
        "derecha del tren. Las cargas que caen fuera de la viga se descartan."
    )

    x_derecho = st.number_input(
        "Posicion del extremo derecho del tren sobre la viga [m] (desde A)",
        min_value=0.0, max_value=float(L), value=min(8.0, float(L)),
        step=0.01, format="%.2f",
    )

    inc_r, exc_r, origen_r = il.position_train_by_right_end(train, x_derecho, L)

    if not inc_r:
        st.error("Con esta posicion, todas las cargas del tren quedan fuera de la viga.")
        st.stop()

    if exc_r:
        st.warning(
            "Cargas excluidas (fuera de la viga): " +
            ", ".join(f"P={P:.2f} ton en x={x:.2f} m" for x, P in exc_r)
        )

    fig_reacciones_viga = il.draw_beam_diagram(L, inc_r, excluded=exc_r)
    st.pyplot(fig_reacciones_viga)

    reacciones = il.compute_reactions(L, inc_r)

    ra_col, rb_col = st.columns(2)
    ra_col.metric("RA [ton]", f"{reacciones['RA']:.4f}")
    rb_col.metric("RB [ton]", f"{reacciones['RB']:.4f}")

    suma_incluidas = sum(P for _, P in inc_r)
    check = reacciones["RA"] + reacciones["RB"]
    if abs(check - suma_incluidas) < 1e-6:
        st.success(
            f"Verificacion de equilibrio OK: RA + RB = {check:.4f} ton = "
            f"suma de cargas incluidas ({suma_incluidas:.4f} ton)"
        )
    else:
        st.error(
            f"RA + RB = {check:.4f} ton no coincide con la suma de cargas incluidas "
            f"({suma_incluidas:.4f} ton)"
        )

    st.markdown("**Ordenadas de influencia por carga**")
    tabla_reacciones = pd.DataFrame([
        {"xᵢ [m]": r["x"], "Pᵢ [ton]": r["P"], "RA(xᵢ)": r["ra_ord"], "RB(xᵢ)": r["rb_ord"]}
        for r in reacciones["rows"]
    ])
    st.dataframe(tabla_reacciones, use_container_width=True)

    st.markdown("**Lineas de influencia de RA y RB**")
    fig_reacciones_il = il.plot_influence_lines_reactions(L, inc_r, reacciones)
    st.pyplot(fig_reacciones_il)

    st.subheader("Posicion mas demandante (reaccion maxima)")
    st.caption(
        "RA y RB, para las cargas que estan sobre la viga, son funciones lineales "
        "a tramos de la posicion del tren: el maximo siempre ocurre exactamente "
        "donde una carga entra o sale de la viga, asi que el programa evalua solo "
        "esos puntos (sin recorrer todo el rango) para hallar la posicion critica."
    )
    x_ra_opt, ra_max, loads_ra_opt = il.find_max_reaction(train, L, "RA")
    x_rb_opt, rb_max, loads_rb_opt = il.find_max_reaction(train, L, "RB")

    crit_ra_col, crit_rb_col = st.columns(2)
    with crit_ra_col:
        st.markdown("**Posicion critica para RA**")
        st.metric("Posicion optima del extremo derecho [m]", f"{x_ra_opt:.4f}")
        st.metric("RA maxima [ton]", f"{ra_max:.4f}")
        st.pyplot(il.draw_beam_diagram(
            L, loads_ra_opt, title=f"Posicion critica - RA maxima = {ra_max:.4f} ton"))
    with crit_rb_col:
        st.markdown("**Posicion critica para RB**")
        st.metric("Posicion optima del extremo derecho [m]", f"{x_rb_opt:.4f}")
        st.metric("RB maxima [ton]", f"{rb_max:.4f}")
        st.pyplot(il.draw_beam_diagram(
            L, loads_rb_opt, title=f"Posicion critica - RB maxima = {rb_max:.4f} ton"))

# ---------------------------------------------------------------------------
# Tab: Cortante en la seccion de analisis
# ---------------------------------------------------------------------------

with tab_cortante:
    st.subheader("Posicion del tren sobre la viga")
    st.caption(
        "De nuevo, la posicion sobre la viga se define con el extremo derecho del "
        "tren (independiente de c₁/c₂). Ademas defines la seccion de analisis a "
        "donde se calcula el cortante."
    )

    xv_col, av_col = st.columns(2)
    with xv_col:
        x_derecho_v = st.number_input(
            "Posicion del extremo derecho del tren sobre la viga [m] (desde A)",
            min_value=0.0, max_value=float(L), value=min(8.0, float(L)),
            step=0.01, format="%.2f", key="x_derecho_v",
        )
    with av_col:
        a_v = st.number_input(
            "Posicion de la seccion de analisis a [m] (desde A, origen de la viga)",
            min_value=0.0, max_value=float(L), value=min(4.0, float(L)),
            step=0.01, format="%.2f", key="a_v",
        )

    inc_v, exc_v, origen_v = il.position_train_by_right_end(train, x_derecho_v, L)

    if not inc_v:
        st.error("Con esta posicion, todas las cargas del tren quedan fuera de la viga.")
        st.stop()

    if exc_v:
        st.warning(
            "Cargas excluidas (fuera de la viga): " +
            ", ".join(f"P={P:.2f} ton en x={x:.2f} m" for x, P in exc_v)
        )

    fig_corte_viga = il.draw_beam_diagram(L, inc_v, a=a_v, excluded=exc_v)
    st.pyplot(fig_corte_viga)

    corte = il.compute_shear(L, a_v, inc_v)

    if abs(corte["V_izq"] - corte["V_der"]) < 1e-9:
        st.metric(f"Cortante en x=a={a_v:.2f} m [ton]", f"{corte['V_izq']:.4f}")
    else:
        st.metric(f"Cortante en x=a={a_v:.2f} m (izq / der) [ton]",
                  f"{corte['V_izq']:.4f} / {corte['V_der']:.4f}")

    st.markdown("**Ordenadas de influencia por carga**")
    tabla_corte = pd.DataFrame([
        {"xᵢ [m]": r["x"], "Pᵢ [ton]": r["P"], "V_izq(xᵢ)": r["v_izq_ord"],
         "V_der(xᵢ)": r["v_der_ord"], "En la seccion (salto)": "si" if r["en_seccion"] else ""}
        for r in corte["rows"]
    ])
    st.dataframe(tabla_corte, use_container_width=True)

    st.markdown("**Linea de influencia de V en la seccion a**")
    fig_corte_il = il.plot_influence_line_v(L, a_v, inc_v, corte)
    st.pyplot(fig_corte_il)

    st.subheader("Posicion mas demandante (cortante maximo)")
    st.caption(
        "El cortante total tambien es lineal a tramos: solo cambia de forma "
        "brusca donde una carga cruza la seccion a, o entra/sale de la viga. "
        "El programa evalua unicamente esos puntos para hallar el maximo."
    )
    x_v_opt, v_max, loads_v_opt = il.find_max_shear(train, L, a_v)
    st.metric("Posicion optima del extremo derecho [m]", f"{x_v_opt:.4f}")
    st.metric(f"Cortante maximo en x=a={a_v:.2f} m [ton]", f"{v_max:.4f}")
    st.pyplot(il.draw_beam_diagram(
        L, loads_v_opt, a=a_v, title=f"Posicion critica - V maximo = {v_max:.4f} ton"))
