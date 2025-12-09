class ExpenseManager:
    def __init__(self):
        self.users = {
            "Kristian": {"cpf": "018.491.380-28"}, 
            "Giulia": {"cpf": "000.000.000-00"}    
        }
        
        self.categories = {
            "Hortifruti": [
                "PESSEGO", "MANGA", "LIMAO", "MELAO", "ALFACE", "BROCOLIS", 
                "FRUTA", "LEGUME", "BANANA", "MACA", "UVA", "BATATA", 
                "CEBOLA", "TOMATE", "CENOURA", "ABACATE", "MAMAO", "LARANJA",
                "COUVE", "REPOLHO", "ABOBORA", "ALHO", "PIMENTAO"
            ],
            "Carnes": [
                "FILEZIN", "SASSAMI", "FRANGO", "CARNE", "BOI", "RES", 
                "PEITO", "COXA", "SOBRECOXA", "MOIDA", "PATINHO", "ALCATRA",
                "BIFE", "LINGUICA", "SALSICHA", "PRESUNTO", "CALABRESA"
            ],
            "Bebidas": [
                "AGUA", "SUCO", "REFRIGERANTE", "CERVEJA", "VIO", 
                "COCA", "PEPSI", "FANTA", "SPRITE", "GUARANA", "VINHO", 
                "VODKA", "ENERGETICO", "CHA", "CAFE", "LEITE"
            ],
            "Padaria": [
                "PANETTONE", "PAO", "BOLO", "TORRADA", "BISCOITO", 
                "BOLACHA", "SALGADINHO", "CROISSANT", "QUEIJO", "REQUEIJAO",
                "MANTEIGA", "MARGARINA", "IOGURTE"
            ],
            "Limpeza": [
                "DETERGENTE", "SABAO", "ALVEJANTE", "PAPEL", "AMACIANTE", 
                "DESINFETANTE", "ESPONJA", "LIXO", "ALCOOL", "MULTI USO", 
                "SANITARIA", "AZULIM", "YPÊ", "OMO"
            ],
            "Higiene": [
                "SHAMPOO", "CONDICIONADOR", "SABONETE", "PASTA", "CREME", 
                "DESODORANTE", "FIO DENTAL", "ESCOVA", "COTTONETE"
            ]
        }

    def identify_payer(self, cpf_found):
        if not cpf_found:
            return "Desconhecido (Sem CPF)"
        for name, data in self.users.items():
            if data["cpf"] == cpf_found:
                return name
        return "Outro"

    def categorize_item(self, item_name):
        item_upper = item_name.upper()
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in item_upper:
                    return category
        return "Geral"