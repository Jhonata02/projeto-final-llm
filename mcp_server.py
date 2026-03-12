import os

class LocalMCPServer:
    def __init__(self):
        self.workspace_dir = os.path.join(os.path.dirname(__file__), "planos_gerados")
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        # O "Banco de Dados" com TODAS as regras da Resolução CSE/UFCG 08/2017
        self.regras_curso = {
            # --- OBRIGATÓRIAS ---
            "fundamentos de matemática para ciência da computação ii": ["fundamentos de matemática para ciência da computação i"],
            "cálculo diferencial e integral i": ["fundamentos de matemática para ciência da computação i"],
            "programação ii": ["programação i", "laboratório de programação i"],
            "laboratório de programação ii": ["programação i", "laboratório de programação i"],
            "álgebra linear": ["fundamentos de matemática para ciência da computação ii"],
            "lógica para computação": ["fundamentos de matemática para ciência da computação ii"],
            "cálculo diferencial e integral ii": ["cálculo diferencial e integral i"],
            "estrutura de dados": ["programação ii", "laboratório de programação ii"],
            "laboratório de estrutura de dados": ["programação ii", "laboratório de programação ii"],
            "introdução à probabilidade": ["cálculo diferencial e integral i", "fundamentos de matemática para ciência da computação ii"],
            "projeto de software": ["programação i", "laboratório de programação i"],
            "paradigmas de linguagem de programação": ["programação i", "laboratório de programação i"],
            "banco de dados i": ["estrutura de dados"],
            "organização e arquitetura de computadores": ["introdução à computação"],
            "laboratório de organização e arquitetura de computadores": ["introdução à computação"],
            "estatística aplicada": ["introdução à probabilidade"],
            "análise de sistemas": ["programação i", "laboratório de programação i"],
            "engenharia de software": ["programação i", "laboratório de programação i"],
            "redes de computadores": ["introdução à computação"],
            "sistemas operacionais": ["organização e arquitetura de computadores"],
            "teoria da computação": ["paradigmas de linguagem de programação"],
            "programação concorrente": ["sistemas operacionais"],
            "inteligência artificial": ["teoria da computação"],
            "análise e técnicas de algoritmos": ["estrutura de dados", "laboratório de estrutura de dados"],
            "compiladores": ["paradigmas de linguagem de programação"],
            "projeto em computação i": ["engenharia de software"],
            "projeto em computação ii": ["projeto em computação i"],
            "trabalho de conclusão de curso": ["projeto de trabalho de conclusão de curso"],

            # --- OPTATIVAS ESPECÍFICAS ---
            "administração de sistemas gerenciadores de bancos de dados": ["banco de dados i"],
            "arquitetura de software": ["projeto de software"],
            "avaliação de desempenho de sistemas discretos": ["introdução à probabilidade"],
            "banco de dados ii": ["banco de dados i"],
            "computação e música": ["estrutura de dados", "análise e técnicas de algoritmos"], 
            "desenvolvimento de aplicações corporativas avançadas": ["projeto de software"],
            "desenvolvimento de software integrado à operação da infraestrutura": ["projeto de software"],
            "gerência de redes": ["redes de computadores"],
            "interconexão de redes de computadores": ["redes de computadores"],
            "prática de ensino em computação ii": ["prática de ensino em computação i"],
            "princípios de desenvolvimento web": ["programação ii"],
            "programação em banco de dados": ["banco de dados i"],
            "projeto de redes de computadores": ["redes de computadores"],
            "provisionamento e operação de infraestrutura": ["sistemas operacionais"],
            "reconhecimento de padrões e redes neurais": ["estatística aplicada", "análise e técnicas de algoritmos"],
            "segurança de sistemas": ["sistemas operacionais", "redes de computadores"],
            "verificação e validação de software": ["engenharia de software"],

            # --- OPTATIVAS GERAIS ---
            "cálculo diferencial e integral iii": ["cálculo diferencial e integral ii", "fundamentos de matemática para ciência da computação ii"],
            "física geral ii": ["física geral i", "cálculo diferencial e integral i", "fundamentos de matemática para ciência da computação ii"],
            "física geral iii": ["física geral ii", "cálculo diferencial e integral ii"],
            "física geral iv": ["física geral iii", "cálculo diferencial e integral iii"]
        }
        
        # Histórico Mockado (Disciplinas que o aluno já pagou)
        # Sinta-se à vontade para adicionar ou remover disciplinas daqui para testar o bloqueio!
        self.historico_aluno = [
            "fundamentos de matemática para ciência da computação i",
            "introdução à computação", 
            "programação i", 
            "laboratório de programação i"
        ]

    def verificar_prerequisitos(self, disciplina: str) -> tuple[bool, str]:
        # Normalizando a entrada para comparar com as chaves do dicionário
        disciplina_clean = disciplina.lower().strip()
        
        if disciplina_clean not in self.regras_curso:
            return True, "Sem pré-requisitos cadastrados (ou disciplina de 1º período)."
            
        prereqs = self.regras_curso[disciplina_clean]
        faltam = [p for p in prereqs if p not in self.historico_aluno]
        
        if faltam:
            return False, f"Falta cursar: {', '.join([f.title() for f in faltam])}"
        return True, "Pré-requisitos totalmente atendidos."

    def salvar_plano_estudos(self, nome_aluno: str, plano_recomendado: str, disciplinas_pretendidas: list[str] = None) -> str:
        safe_name = "".join([c for c in nome_aluno if c.isalpha() or c.isdigit()]).rstrip() or "aluno_padrao"
        
        status_plano = "APROVADO"
        detalhes = []
        
        if disciplinas_pretendidas:
            for disc in disciplinas_pretendidas:
                pode_cursar, motivo = self.verificar_prerequisitos(disc)
                if pode_cursar:
                    detalhes.append(f"✅ {disc.title()}: {motivo}")
                else:
                    detalhes.append(f"❌ {disc.title()}: BLOQUEADA. {motivo}")
                    status_plano = "REJEITADO (Falta de pré-requisitos)"
        else:
            detalhes.append("Nenhuma disciplina identificada.")

        relatorio_final = (
            f"=== PLANO DE MATRÍCULA: {status_plano} ===\n"
            f"Aluno: {nome_aluno}\n\n"
            f"Histórico Atual (Simulado): {len(self.historico_aluno)} disciplinas concluídas.\n\n"
            f"Análise de Pré-requisitos (Base: Res. 08/2017):\n" + "\n".join(detalhes) + "\n\n"
            f"Notas do Agente:\n{plano_recomendado}\n"
            f"=========================================="
        )
        
        file_path = os.path.join(self.workspace_dir, f"plano_{safe_name}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(relatorio_final)
            
        return f"Plano {status_plano} e salvo em: {file_path}"

# Instância global
mcp_local = LocalMCPServer()

def salvar_plano_estudos(nome_aluno: str, plano_recomendado: str, disciplinas_pretendidas: list[str] = None):
    # Fallback caso o LLM mande uma string separada por vírgula em vez de lista
    if isinstance(disciplinas_pretendidas, str):
        disciplinas_pretendidas = [d.strip() for d in disciplinas_pretendidas.split(",")]
    return mcp_local.salvar_plano_estudos(nome_aluno, plano_recomendado, disciplinas_pretendidas)

if __name__ == "__main__":
    print("Servidor MCP Local com validação de grade COMPLETA pronto.")