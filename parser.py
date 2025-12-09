import pdfplumber
import re

class InvoiceParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.raw_text = ""
        self.data = {
            "loja": None,
            "data": None,
            "cpf_consumidor": None,
            "forma_pagamento": "Indefinido",
            "total_nota": 0.0,
            "itens": [] # Desconto entrará aqui como negativo
        }

    def _convert_br_number(self, value_str):
        if not value_str: return 0.0
        try:
            return float(value_str.replace('.', '').replace(',', '.'))
        except:
            return 0.0

    def parse(self):
        with pdfplumber.open(self.pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text(layout=True) or "" 
            self.raw_text = full_text

        lines = self.raw_text.split('\n')
        
        # --- ESTADOS DO LEITOR ---
        lendo_itens = False # Só vira True quando passar pelo cabeçalho
        linha_anterior_pendente = ""
        acumulado_desconto = 0.0

        for line in lines:
            line_clean = line.strip()
            if not line_clean: continue
            line_upper = line_clean.upper()

            # ===============================================================
            # 1. METADADOS GERAIS (Lê em qualquer lugar da nota)
            # ===============================================================
            
            # Data
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', line_clean)
            if date_match and not self.data["data"]:
                self.data["data"] = date_match.group(1)

            # Loja (Geralmente nas primeiras linhas)
            if not self.data["loja"] and ("DISTRIBUIDORA" in line_upper or "SUPERMERCADO" in line_upper or "LTDA" in line_upper):
                self.data["loja"] = line_clean

            # CPF (Pega e limpa da linha) [cite: 16]
            if "CPF" in line_upper or "CNPJ" in line_upper:
                cpf_match = re.search(r'(\d{3}\.\d{3}\.\d{3}-\d{2})', line_clean)
                if cpf_match: self.data["cpf_consumidor"] = cpf_match.group(1)
                # Remove o CPF da linha para não sujar se estiver grudado no item
                line_clean = re.sub(r'(?i)(CPF|CNPJ):?\s*[\d\.\/-]{11,18}', '', line_clean).strip()

            # Desconto (Pega e soma)
            if "DESCONTO" in line_upper:
                match_desc = re.search(r'(?:DESCONTOS?|DESC\.?|R\$).+?(\d+,\d{2})', line_clean, re.IGNORECASE)
                if match_desc:
                    acumulado_desconto += self._convert_br_number(match_desc.group(1))

            # Forma de Pagamento (Geralmente no final)
            if "CARTÃO" in line_upper or "CREDITO" in line_upper: self.data["forma_pagamento"] = "Cartão de Crédito"
            elif "DEBITO" in line_upper: self.data["forma_pagamento"] = "Débito"
            elif "PIX" in line_upper: self.data["forma_pagamento"] = "Pix"
            elif "DINHEIRO" in line_upper: self.data["forma_pagamento"] = "Dinheiro"

            # ===============================================================
            # 2. CONTROLE DE ESTADO (Onde começa e onde termina a lista?)
            # ===============================================================

            # GATILHO DE FIM: Se achou "Valor Total", acabou a lista. 
            if "VALOR TOTAL" in line_upper or "TOTAL R$" in line_upper:
                lendo_itens = False
                continue

            # GATILHO DE INÍCIO: Se achou o cabeçalho da tabela, começa na próxima. 
            # Verifica palavras chaves do cabeçalho
            if "CÓDIGO" in line_upper and "DESCRIÇÃO" in line_upper:
                lendo_itens = True
                continue # Pula a linha do cabeçalho em si

            # Se ainda não ativou o modo leitura (e não é cabeçalho explícito),
            # verifica se a linha JÁ É um item (caso o cabeçalho não tenha sido lido corretamente)
            # Isso é uma segurança caso o PDF não tenha o texto "Código Descrição" legível.
            regex_item_check = r'\d+,\d{2}\s+\d+,\d{2}\s*$' # Termina com dois preços?
            if not lendo_itens and re.search(regex_item_check, line_clean) and not "VALOR" in line_upper:
                lendo_itens = True

            # ===============================================================
            # 3. LEITURA DE ITENS (Só processa se lendo_itens == True)
            # ===============================================================
            
            if lendo_itens:
                # Limpeza de lixo específico dentro da área de itens
                line_clean = re.sub(r'(?i)Protocolo.*?\d+', '', line_clean).strip() # Protocolo
                line_clean = re.sub(r'(?:\d{4}\s?){11}', '', line_clean).strip() # Chave de acesso [cite: 13]
                
                # Injeção de espaço (Desgrudar "0,500KG") 
                line_clean = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', line_clean)
                line_clean = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', line_clean)

                # Regex do Item: Pega do FIM para o COMEÇO
                # Qtd -> Un -> Unit -> Total
                regex_completo = r'(\d+(?:,\d+)?)\s+([a-zA-Z]{2,3})\s+(\d+(?:,\d+)?)\s+(\d+(?:,\d+)?)\s*$'
                match = re.search(regex_completo, line_clean)
                
                item_data = {}

                if match:
                    # Achou padrão completo
                    qtd = self._convert_br_number(match.group(1))
                    un = match.group(2)
                    vl_unit = self._convert_br_number(match.group(3))
                    vl_total = self._convert_br_number(match.group(4))
                    
                    # Nome é o que sobrou no começo
                    texto_nome = line_clean[:match.start()].strip()
                    # Remove o CÓDIGO numérico inútil do início (ex: "6675") 
                    texto_nome = re.sub(r'^\d+\s+', '', texto_nome).strip()
                    
                    item_data = {"item": texto_nome, "qtd": qtd, "un": un, "vl_unit": vl_unit, "valor": vl_total}

                elif re.search(r'(\d+,\d{2})\s*$', line_clean):
                    # Achou só o total (item quebrado)
                    match_total = re.search(r'(\d+,\d{2})\s*$', line_clean)
                    vl_total = self._convert_br_number(match_total.group(1))
                    
                    texto_nome = line_clean[:match_total.start()].strip()
                    texto_nome = re.sub(r'^\d+\s+', '', texto_nome).strip()
                    
                    # Se tiver texto suficiente, é item
                    if len(texto_nome) > 2:
                        item_data = {"item": texto_nome, "qtd": 1.0, "un": "UN", "vl_unit": vl_total, "valor": vl_total}

                # Salva ou Junta com anterior
                if item_data:
                    if linha_anterior_pendente:
                        item_data["item"] = f"{linha_anterior_pendente} {item_data['item']}"
                        linha_anterior_pendente = ""
                    self.data["itens"].append(item_data)
                else:
                    # Se tem texto mas não é comando de sistema, guarda
                    palavras_sistema = ["PÁGINA", "PAGE", "DANFE", "CONSUMIDOR", "NFC-E", "VERSÃO"]
                    if len(line_clean) > 3 and not any(p in line_upper for p in palavras_sistema):
                        linha_anterior_pendente = line_clean

        # --- FIM DO LOOP: Adiciona o Desconto como Item ---
        if acumulado_desconto > 0:
            self.data["itens"].append({
                "item": "💸 DESCONTO / ABATIMENTO",
                "qtd": 1, "un": "UN", "vl_unit": -acumulado_desconto, 
                "valor": -acumulado_desconto
            })

        self.data["total_nota"] = sum(item["valor"] for item in self.data["itens"])
        return self.data