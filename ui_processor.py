import streamlit as st
import pandas as pd
import os
from datetime import datetime
from parser import InvoiceParser
from core import ExpenseManager

# Pasta onde as notas ficam esperando
BUFFER_DIR = "notas_pendentes"
if not os.path.exists(BUFFER_DIR):
    os.makedirs(BUFFER_DIR)

def render_processor(manager):

    st.markdown("### 📥 Central de Uploads")
    
    # --- PARTE A: UPLOAD PARA A FILA ---
    with st.expander("📤 Adicionar novas notas à fila", expanded=False):
        uploaded_files = st.file_uploader("Selecione arquivos (PDF)", type="pdf", accept_multiple_files=True)
        if uploaded_files:
            for f in uploaded_files:
                with open(os.path.join(BUFFER_DIR, f.name), "wb") as buffer:
                    buffer.write(f.getbuffer())
            st.success(f"{len(uploaded_files)} notas enviadas para a fila!")
            st.rerun()

    # --- PARTE B: SELECIONAR DA FILA ---
    pendentes = [f for f in os.listdir(BUFFER_DIR) if f.lower().endswith('.pdf')]
    
    if not pendentes:
        st.info("🎉 Fila vazia! Nenhuma nota pendente.")
        return

    st.markdown(f"#### 📋 Fila: {len(pendentes)} notas aguardando")
    arquivo_selecionado = st.selectbox("Nota atual:", pendentes, index=0)
    
    # Caminho do arquivo real na pasta
    current_file_path = os.path.join(BUFFER_DIR, arquivo_selecionado)

    # --- PARTE C: PROCESSAMENTO ---
    parser = InvoiceParser(current_file_path)
    core_manager = ExpenseManager()

    try:
        data = parser.parse()
    except Exception as e:
        st.error(f"Erro ao ler PDF: {e}")
        if st.button("🗑️ Deletar arquivo corrompido"):
            os.remove(current_file_path)
            st.rerun()
        return

    st.markdown("---")
    
    # Metadados (Data, Loja, Pagador)
    c1, c2, c3, c4 = st.columns(4)
    
    data_padrao = datetime.today()
    if data.get('data'):
        try:
            data_padrao = datetime.strptime(data['data'], "%d/%m/%Y")
        except: pass
    
    nova_data = c1.date_input("Data da Nota", value=data_padrao, format="DD/MM/YYYY")
    data_formatada_str = nova_data.strftime("%d/%m/%Y")

    c2.info(f"🛒 {data['loja']}")
    c3.info(f"💳 {data['forma_pagamento']}")
    
    opcoes = ["Kristian", "Giulia", "Outro"]
    sugestao = core_manager.identify_payer(data['cpf_consumidor'])
    idx = opcoes.index(sugestao) if sugestao in opcoes else 2
    pagador_final = c4.selectbox("Quem pagou?", opcoes, index=idx)

    # --- LISTA DE ITENS (LAYOUT PERSONALIZADO + DETALHES QTD/UN) ---
    st.markdown("### 📝 Classificar Itens")
        
    # Cabeçalho da 'Tabela' (Proporção 5 / 1 / 1.5 / 1.5)
    c_h1, c_h2, c_h3, c_h4 = st.columns([5, 1, 1.5, 1.5])
    c_h1.markdown("<div style='text-align: center;'><b>Item (Detalhes)</b></div>", unsafe_allow_html=True)
    c_h2.markdown("<div style='text-align: center;'><b>Valor (R$)</b></div>", unsafe_allow_html=True)
    c_h3.markdown("<div style='text-align: center;'><b>Kristian ↔ Giulia</b></div>", unsafe_allow_html=True)
    c_h4.markdown("<div style='text-align: center;'><b>Categoria</b></div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 2px 0px; border-top: 1px solid #555;'>", unsafe_allow_html=True)

    itens_processados_final = []
    opcoes_slider = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]

    for i, item in enumerate(data["itens"]):
        c1, c2, c3, c4 = st.columns([5, 1, 1.5, 1.5], vertical_alignment="center")
        
        # --- LÓGICA DE COR (VERDE SE FOR DESCONTO/NEGATIVO) ---
        # Se o valor for negativo, pinta de verde (#4CAF50) e negrito
        is_discount = item['valor'] < 0
        cor_texto = "#4CAF50" if is_discount else "inherit"
        peso_fonte = "bold" if is_discount else "normal"
        
        # Col 1: Item + Detalhes
        nome_curto = item['item'][:100] + "..." if len(item['item']) > 100 else item['item']
        
        # Detalhe técnico (Qtd x Unit) - Esconde se for desconto para ficar limpo
        if is_discount:
            html_item = f"<div style='text-align: center; color: {cor_texto}; font-weight: {peso_fonte};'>{nome_curto}</div>"
        else:
            detalhe = f"({item.get('qtd',1):.3f} {item.get('un','UN')} x {item.get('vl_unit', item['valor']):.2f})"
            html_item = f"<div style='text-align: center; line-height:1.2;'><span title='{item['item']}'>{nome_curto}</span><br><span style='font-size:0.8em;color:#aaa;'>{detalhe}</span></div>"
        
        c1.markdown(html_item, unsafe_allow_html=True)
        
        # Col 2: Valor (Com cor)
        c2.markdown(f"<div style='text-align: center; color: {cor_texto}; font-weight: {peso_fonte};'>{item['valor']:.2f}</div>", unsafe_allow_html=True)

        # Col 3: Slider
        with c3:
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            split_value = st.select_slider(f"sl_{i}", options=opcoes_slider, value=50, key=f"split_{i}", label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)

        # Col 4: Categoria (Com Memória)
        with c4:
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            lista_cats = list(core_manager.categories.keys()) + ["Geral"]
            cat_memoria = manager.get_learned_category(item["item"])
            
            # Se for desconto, força categoria 'Geral' ou cria uma 'Descontos' se quiser
            if is_discount:
                cat_final = "Geral"
            else:
                cat_final = cat_memoria if (cat_memoria and cat_memoria in lista_cats) else core_manager.categorize_item(item["item"])
            
            try: idx_cat = lista_cats.index(cat_final)
            except: idx_cat = len(lista_cats) - 1
            
            cat_sel = st.selectbox(f"ct_{i}", options=lista_cats, index=idx_cat, key=f"cat_select_{i}", label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<hr style='margin: 0px 0px; padding: 0px; border-top: 0.5px solid #ccc;'>", unsafe_allow_html=True)

        pct_g = split_value / 100.0
        pct_k = 1.0 - pct_g
        
        itens_processados_final.append({
            "Item": item["item"],
            "Valor (R$)": item["valor"],
            "Categoria": cat_sel,
            "Divisão (K)": pct_k,
            "R$ Kristian": item["valor"] * pct_k,
            "R$ Giulia": item["valor"] * pct_g
        })

    # --- TOTAIS (SIMPLIFICADO) ---
    # Como o desconto já está na lista como negativo, a soma simples resolve tudo!
    edited_df = pd.DataFrame(itens_processados_final)
    
    total_liquido = edited_df["Valor (R$)"].sum()
    k_final = edited_df["R$ Kristian"].sum()
    g_final = edited_df["R$ Giulia"].sum()

    st.markdown("") 
    col_tot1, col_tot2, col_tot3 = st.columns(3)
    
    with col_tot1:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.metric("💰 Total a Pagar", f"R$ {total_liquido:.2f}")
        st.markdown("</div>", unsafe_allow_html=True)
    with col_tot2:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.metric("👤 Kristian", f"R$ {k_final:.2f}")
        st.markdown("</div>", unsafe_allow_html=True)
    with col_tot3:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.metric("👤 Giulia", f"R$ {g_final:.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("💾 Confirmar e Remover da Fila", type="primary", use_container_width=True):
        itens_save = edited_df.to_dict('records')
        
        if manager.save_invoice(data_formatada_str, data['loja'], total_liquido, pagador_final, data['forma_pagamento'], itens_save):
            st.toast("Nota salva!", icon="✅")
            try: os.remove(current_file_path); st.rerun()
            except: st.error("Erro ao deletar arquivo.")