import streamlit as st
import pandas as pd
from datetime import datetime

def render_history_manager(db_manager):
    st.markdown("### 🗂️ Histórico Completo")

    tab_notas, tab_reembolsos = st.tabs(["🛒 Notas Fiscais", "💸 Reembolsos/Pix"])

    # -------------------------------
    # ABA 1: NOTAS FISCAIS
    # -------------------------------
    with tab_notas:
        notas = db_manager.get_all_invoices()

        if not notas:
            st.info("Nenhuma nota registrada.")
        else:
            df_notas = pd.DataFrame(notas)

            # Converte data_compra para datetime (formato dd/mm/YYYY vindo do app)
            df_notas["data_compra_dt"] = pd.to_datetime(
                df_notas["data_compra"],
                format="%d/%m/%Y",
                errors="coerce",
            )

            # Filtros
            st.markdown("#### 🔎 Filtros")
            col_f1, col_f2 = st.columns(2)

            min_date = df_notas["data_compra_dt"].min().date()
            max_date = df_notas["data_compra_dt"].max().date()

            data_inicio, data_fim = col_f1.date_input(
                "Período",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )

            lojas = ["Todas"] + sorted(df_notas["loja"].unique().tolist())
            loja_sel = col_f2.selectbox("Loja", lojas)

            # Aplica filtros
            df_filtrado = df_notas.copy()
            df_filtrado = df_filtrado[
                (df_filtrado["data_compra_dt"].dt.date >= data_inicio)
                & (df_filtrado["data_compra_dt"].dt.date <= data_fim)
            ]

            if loja_sel != "Todas":
                df_filtrado = df_filtrado[df_filtrado["loja"] == loja_sel]

            if df_filtrado.empty:
                st.info("Nenhuma nota encontrada para os filtros selecionados.")
            else:
                # Agrupa por data (string original) para manter visual amigável
                for data_str in df_filtrado["data_compra"].unique():
                    notas_dia = df_filtrado[df_filtrado["data_compra"] == data_str]
                    with st.expander(f"📅 {data_str} ({len(notas_dia)} notas)"):
                        for _, row in notas_dia.iterrows():
                            c1, c2 = st.columns([4, 1])
                            c1.markdown(
                                f"**{row['loja']}** | {row['pagador']} | **R$ {row['total_nota']:.2f}**"
                            )
                            if c2.button("🗑️ Excluir", key=f"del_n_{row['id']}"):
                                db_manager.delete_invoice(row["id"])
                                st.rerun()

    # -------------------------------
    # ABA 2: REEMBOLSOS
    # -------------------------------
    with tab_reembolsos:
        reembolsos = db_manager.get_all_reimbursements()

        if not reembolsos:
            st.info("Nenhum reembolso registrado.")
        else:
            for r in reembolsos:
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(
                        f"💸 **{r['pagador']}** ➝ **{r['recebedor']}**: R$ {r['valor']:.2f}"
                    )
                    c1.caption(f"Data: {r['data_pagamento']}")
                    if c2.button("🗑️ Excluir", key=f"del_r_{r['id']}"):
                        db_manager.delete_reimbursement(r["id"])
                        st.rerun()
