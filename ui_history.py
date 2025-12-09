import streamlit as st
import pandas as pd

def render_history_manager(db_manager):
    st.markdown("### 🗂️ Histórico Completo")
    tab_notas, tab_reembolsos = st.tabs(["🛒 Notas Fiscais", "💸 Reembolsos/Pix"])

    with tab_notas:
        notas = db_manager.get_all_invoices()
        if not notas:
            st.info("Nenhuma nota registrada.")
        else:
            df_notas = pd.DataFrame(notas)
            for data in df_notas["data_compra"].unique():
                notas_dia = df_notas[df_notas["data_compra"] == data]
                with st.expander(f"📅 {data} ({len(notas_dia)} notas)"):
                    for _, row in notas_dia.iterrows():
                        c1, c2 = st.columns([4, 1])
                        c1.markdown(f"**{row['loja']}** | {row['pagador']} | **R$ {row['total_nota']:.2f}**")
                        if c2.button("🗑️ Excluir", key=f"del_n_{row['id']}"):
                            db_manager.delete_invoice(row['id'])
                            st.rerun()

    with tab_reembolsos:
        reembolsos = db_manager.get_all_reimbursements()
        if not reembolsos:
            st.info("Nenhum reembolso registrado.")
        else:
            for r in reembolsos:
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(f"💸 **{r['pagador']}** ➝ **{r['recebedor']}**: R$ {r['valor']:.2f}")
                    c1.caption(f"Data: {r['data_pagamento']}")
                    if c2.button("🗑️ Excluir", key=f"del_r_{r['id']}"):
                        db_manager.delete_reimbursement(r['id'])
                        st.rerun()