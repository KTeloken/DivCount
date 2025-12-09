import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

# --- FUNÇÕES AUXILIARES ---

def make_donut_chart(df, coluna_valor, coluna_label, tipo='azul'):
    """
    Cria um gráfico de rosca estilizado com o tema do usuário.
    """
    if tipo == 'azul':
        # Paleta para combinar com o Azul Neon do tema
        colors = alt.Scale(range=['#14AAFF', '#0077C2', '#004BA0', '#69E2FF'])
    else:
        colors = alt.Scale(scheme='magma') 

    base = alt.Chart(df).encode(theta=alt.Theta(coluna_valor, stack=True))
    
    pie = base.mark_arc(innerRadius=65, outerRadius=105).encode(
        color=alt.Color(coluna_label, scale=colors, legend=None),
        order=alt.Order(coluna_valor, sort="descending"),
        tooltip=[coluna_label, alt.Tooltip(coluna_valor, format=",.2f")]
    )
    
    text = base.mark_text(radius=125).encode(
        text=alt.Text(coluna_valor, format=",.2f"),
        order=alt.Order(coluna_valor, sort="descending"),
        color=alt.value("#FAFAFA")  # Cor do texto do tema escuro
    )
    
    return pie + text

# --- FUNÇÃO DASHBOARD RENDER ---

def render_dashboard(manager):
    df_compras, df_reembolsos = manager.get_financial_data()
    
    if df_compras.empty:
        st.info("📭 Nenhuma compra registrada. Comece processando uma nota na aba 'Processar Nota'.")
        return

    # --- INÍCIO: CÁLCULOS GLOBAIS (BALANÇO) ---
    # Conversão de data para uso em filtros e gráficos (IMPORTANTE)
    df_compras['data_compra'] = pd.to_datetime(df_compras['data_compra'], format='%d/%m/%Y', errors='coerce')

    # 1. Consumo Total
    k_consumo_total = df_compras["kristian_parte"].sum()
    g_consumo_total = df_compras["giulia_parte"].sum()
    
    # 2. Pagamento na Loja
    k_pagou_loja_total = df_compras[df_compras["pagador"] == "Kristian"]["valor"].sum()
    g_pagou_loja_total = df_compras[df_compras["pagador"] == "Giulia"]["valor"].sum()
    
    # 3. Pix (Reembolsos)
    k_recebeu_pix = df_reembolsos[df_reembolsos["recebedor"] == "Kristian"]["valor"].sum() if not df_reembolsos.empty else 0.0
    g_recebeu_pix = df_reembolsos[df_reembolsos["recebedor"] == "Giulia"]["valor"].sum() if not df_reembolsos.empty else 0.0
    k_enviou_pix = df_reembolsos[df_reembolsos["pagador"] == "Kristian"]["valor"].sum() if not df_reembolsos.empty else 0.0
    g_enviou_pix = df_reembolsos[df_reembolsos["pagador"] == "Giulia"]["valor"].sum() if not df_reembolsos.empty else 0.0

    # 4. Cálculo do Saldo
    k_total_desembolso = k_pagou_loja_total + k_enviou_pix
    g_total_desembolso = g_pagou_loja_total + g_enviou_pix
    saldo_k = (k_total_desembolso) - k_recebeu_pix - k_consumo_total
    
    # -----------------------------------------------
    # BLOCO 1: BALANÇO E QUITAÇÃO (TOPO)
    # -----------------------------------------------
    st.markdown("### 🏦 Balanço Atual (Acumulado)")
    col_balanco, col_quitacao = st.columns([1, 2])
    
    with col_balanco:
        valor_divida = abs(saldo_k)
        if saldo_k > 0.01: 
            st.error(f"🚨 **Giulia deve: R$ {valor_divida:.2f}**")
            st.caption("para o Kristian")
        elif saldo_k < -0.01: 
            st.error(f"🚨 **Kristian deve: R$ {valor_divida:.2f}**")
            st.caption("para a Giulia")
        else:
            st.success("✅ **Contas em dia!**")

    with col_quitacao:
        with st.expander("💸 Registrar Quitação (Pix)"):
            c_pag, c_rec, c_val, c_btn = st.columns([1.5, 1.5, 1.5, 1])
            idx_pag = 1 if saldo_k > 0 else 0 
            quem_paga = c_pag.selectbox("Quem pagou?", ["Kristian", "Giulia"], index=idx_pag)
            quem_recebe = "Kristian" if quem_paga == "Giulia" else "Giulia"
            c_rec.text_input("Quem recebe?", value=quem_recebe, disabled=True)
            valor_pgto = c_val.number_input("Valor (R$)", min_value=0.0, step=10.0)
            if c_btn.button("Confirmar", use_container_width=True):
                if valor_pgto > 0:
                    if manager.save_reimbursement(quem_paga, quem_recebe, valor_pgto):
                        st.toast("Salvo!", icon="✅")
                        st.rerun()

    st.markdown("---")
    
    # -----------------------------------------------
    # BLOCO 2: BALANÇO DETALHADO (RESTAURADO)
    # -----------------------------------------------
    st.markdown("### 🔍 Detalhamento Financeiro (Total)")
    
    col_k_pagou, col_g_pagou, col_k_consumiu, col_g_consumiu = st.columns(4)
    
    col_k_pagou.metric(
        "Kristian Desembolsou (Loja + Pix)", 
        f"R$ {k_total_desembolso:.2f}",
        delta=f"Pix Enviado: R$ {k_enviou_pix:.2f} / Recebido: R$ {k_recebeu_pix:.2f}", 
        delta_color="off"
    )
    col_g_pagou.metric(
        "Giulia Desembolsou (Loja + Pix)", 
        f"R$ {g_total_desembolso:.2f}",
        delta=f"Pix Enviado: R$ {g_enviou_pix:.2f} / Recebido: R$ {g_recebeu_pix:.2f}", 
        delta_color="off"
    )
    col_k_consumiu.metric(
        "Kristian Consumiu (Gasto Real)", 
        f"R$ {k_consumo_total:.2f}",
        delta=f"Pago na Loja: R$ {k_pagou_loja_total:.2f}",
        delta_color="off"
    )
    col_g_consumiu.metric(
        "Giulia Consumiu (Gasto Real)", 
        f"R$ {g_consumo_total:.2f}",
        delta=f"Pago na Loja: R$ {g_pagou_loja_total:.2f}",
        delta_color="off"
    )

    st.markdown("---")
    
    # -----------------------------------------------
    # BLOCO 3: ANÁLISE DE COMPRAS (FILTROS E GRÁFICOS)
    # -----------------------------------------------
    st.markdown("### 🔎 Análise de Compras")
    
    # --- FILTROS ---
    with st.expander("🔻 Filtros Avançados", expanded=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        
        # Filtro Data
        min_date = df_compras['data_compra'].min().date()
        max_date = df_compras['data_compra'].max().date()
        
        data_inicio, data_fim = f_col1.date_input(
            "Período", 
            value=(min_date, max_date), 
            min_value=min_date, 
            max_value=max_date
        )
        
        # Filtro Categoria
        categorias = ["Todas"] + sorted(df_compras['categoria'].unique().tolist())
        cat_selecionada = f_col2.selectbox("Categoria", categorias)
        
        # Filtro Loja
        lojas = ["Todas"] + sorted(df_compras['loja'].unique().tolist())
        loja_selecionada = f_col3.selectbox("Loja", lojas)

    # Aplica Filtros
    df_filtered = df_compras.copy()
    df_filtered = df_filtered[
        (df_filtered['data_compra'].dt.date >= data_inicio) & 
        (df_filtered['data_compra'].dt.date <= data_fim)
    ]
    if cat_selecionada != "Todas": df_filtered = df_filtered[df_filtered['categoria'] == cat_selecionada]
    if loja_selecionada != "Todas": df_filtered = df_filtered[df_filtered['loja'] == loja_selecionada]
    
    total_filtrado = df_filtered['valor'].sum()
    st.markdown(f"#### Gastos no período filtrado: **R$ {total_filtrado:.2f}**")
    
    # --- GRÁFICOS (Removido "Top Itens") ---
    tab_cat, tab_tempo = st.tabs(["🍩 Categorias", "📈 Evolução"])

    # ABA 1: CATEGORIA
    with tab_cat:
        col_g1, col_g2 = st.columns(2)
        df_cat = df_filtered.groupby("categoria")["valor"].sum().reset_index()
        
        with col_g1:
            if not df_cat.empty:
                chart = alt.Chart(df_cat).mark_bar(color='#14AAFF').encode(
                    x=alt.X('valor', title='Total (R$)'),
                    y=alt.Y('categoria', sort='-x', title=''),
                    tooltip=['categoria', alt.Tooltip('valor', format=",.2f")]
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("Sem dados para os filtros selecionados.")
                
        with col_g2:
            if not df_cat.empty:
                st.altair_chart(make_donut_chart(df_cat, "valor", "categoria", tipo='azul'), use_container_width=True)

    # ABA 2: EVOLUÇÃO (Corrigido para usar a data da nota)
        with tab_tempo:
            if not df_filtered.empty:
                # Agrupa e ORDENA por data para a linha não ficar bagunçada
                df_tempo = df_filtered.groupby("data_compra")["valor"].sum().reset_index().sort_values("data_compra")
                
                # Gráfico de Linha com Eixo Temporal (:T)
                line = alt.Chart(df_tempo).mark_line(point=True, color='#14AAFF').encode(
                    x=alt.X('data_compra:T', title='Data da Nota', axis=alt.Axis(format="%d/%m")), # :T força entender como tempo
                    y=alt.Y('valor', title='Valor (R$)'),
                    tooltip=[alt.Tooltip('data_compra', format='%d/%m/%Y', title="Data"), alt.Tooltip('valor', format=",.2f")]
                ).interactive()
                st.altair_chart(line, use_container_width=True)
            else:
                st.warning("Sem dados.")
    
    # -----------------------------------------------
    # BLOCO 4: DOWNLOAD E TABELA BRUTA (RESTAURADO)
    # -----------------------------------------------
    with st.container():
        st.markdown("### 📥 Exportar Dados")
        
        if not df_filtered.empty:
            df_export = df_filtered[['data_compra', 'loja', 'pagador', 'item_nome', 'categoria', 'valor', 'kristian_parte', 'giulia_parte']]
            csv = df_export.to_csv(index=False, date_format='%d/%m/%Y').encode('utf-8')
            
            st.download_button(
                label="📥 Baixar Dados Filtrados (CSV)",
                data=csv,
                file_name='dados_filtrados_contas.csv',
                mime='text/csv'
            )

        with st.expander("🔎 Ver Tabela Completa (Itens Filtrados)"):
            if not df_filtered.empty:
                st.dataframe(
                    df_filtered.drop(columns=['nota_id']).style.format({
                        "valor": "R$ {:.2f}",
                        "kristian_parte": "R$ {:.2f}",
                        "giulia_parte": "R$ {:.2f}",
                        "data_compra": lambda t: t.strftime('%d/%m/%Y')
                    }), 
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.info("Sem dados para exibir na tabela.")