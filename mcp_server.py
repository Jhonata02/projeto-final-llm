import os
import logging
import unicodedata
import difflib
from mcp.server.fastmcp import FastMCP

# REQUISITO DE SEGURANÇA: Registrar chamadas de tool
logging.basicConfig(
    filename='mcp_security.log', 
    level=logging.INFO, 
    format='%(asctime)s - [MCP TOOL CALL] - %(message)s'
)

# Inicializa o Servidor MCP
mcp = FastMCP("PlanejadorMatricula_UFCG")

class LocalMCPServer:
    def __init__(self):
        self.workspace_dir = os.path.join(os.path.dirname(__file__), "planos_gerados")
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        # O "Banco de Dados" com TODAS as regras da Resolução CSE/UFCG 08/2017
        self.regras_curso = {
            # --- OBRIGATÓRIAS ---
            "fundamentos de matemática para ciência da computação i": [], # 1º período
            "introdução à computação": [], # 1º período
            "programação i": [], # 1º período
            "laboratório de programação i": [], # 1º período
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

        # Mapa de apelidos e siglas comuns dos alunos
        self.apelidos = {
            "calculo i": "cálculo diferencial e integral i",
            "calculo 1": "cálculo diferencial e integral i",
            "calculo ii": "cálculo diferencial e integral ii",
            "calculo 2": "cálculo diferencial e integral ii",
            "calculo iii": "cálculo diferencial e integral iii",
            "calculo 3": "cálculo diferencial e integral iii",
            "fmcc i": "fundamentos de matemática para ciência da computação i",
            "fmcc 1": "fundamentos de matemática para ciência da computação i",
            "fmcc ii": "fundamentos de matemática para ciência da computação ii",
            "fmcc 2": "fundamentos de matemática para ciência da computação ii",
            "tcc": "trabalho de conclusão de curso",
            "ia": "inteligência artificial",
            "ed": "estrutura de dados",
            "leda": "laboratório de estrutura de dados",
            "bd": "banco de dados i",
            "p1": "programação i",
            "p2": "programação ii",
            "lp1": "laboratório de programação i",
            "lp2": "laboratório de programação ii"
        }
        
        # Cria um mapeamento normalizado (sem acentos) para busca avançada
        self.mapa_normalizado = {self._normalizar(k): k for k in self.regras_curso.keys()}
        self.nomes_norm_lista = list(self.mapa_normalizado.keys())
        
        # Histórico Mockado (Disciplinas que o aluno já pagou)
        # Simula um aluno que está indo para o 5º período (para a demo aprovar mais planos)
        self.historico_aluno = [
            "fundamentos de matemática para ciência da computação i",
            "fundamentos de matemática para ciência da computação ii",
            "introdução à computação", 
            "programação i", 
            "laboratório de programação i",
            "programação ii",
            "laboratório de programação ii",
            "cálculo diferencial e integral i",
            "cálculo diferencial e integral ii",
            "álgebra linear",
            "estrutura de dados",
            "laboratório de estrutura de dados",
            "projeto de software",
            "paradigmas de linguagem de programação",
            "lógica para computação",
            "organização e arquitetura de computadores",
            "banco de dados i"
        ]

    def _normalizar(self, texto: str) -> str:
        """Remove acentos e converte para minúsculas."""
        texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
        return texto.lower().strip()

    def verificar_prerequisitos(self, disciplina: str) -> tuple[bool, str, str]:
        disc_norm = self._normalizar(disciplina)
        
        if disc_norm in self.apelidos:
            disc_norm = self._normalizar(self.apelidos[disc_norm])

        # 1. Tenta encontrar a disciplina exata (já ignorando acentos)
        if disc_norm in self.mapa_normalizado:
            nome_oficial = self.mapa_normalizado[disc_norm]
        else:
            # 2. Tenta Busca Aproximada (Fuzzy Matching) caso haja erros de digitação
            # Cutoff 0.65 permite erros moderados (ex: "IA" não vai bater, mas "Inteligncia" sim)
            matches = difflib.get_close_matches(disc_norm, self.nomes_norm_lista, n=1, cutoff=0.65)
            if matches:
                nome_oficial = self.mapa_normalizado[matches[0]]
            else:
                # 3. Não encontrou nada parecido -> Bloqueia a matrícula
                return False, f"⚠️ Disciplina não reconhecida na grade curricular.", disciplina
            
        prereqs = self.regras_curso[nome_oficial]
        
        if not prereqs:
            return True, "Sem pré-requisitos cadastrados (1º período).", nome_oficial
            
        faltam = [p for p in prereqs if p not in self.historico_aluno]
        
        if faltam:
            return False, f"Falta cursar: {', '.join([f.title() for f in faltam])}", nome_oficial
            
        return True, "Pré-requisitos totalmente atendidos.", nome_oficial

    def salvar_plano_estudos(self, nome_aluno: str, plano_recomendado: str, disciplinas_pretendidas: list[str] = None) -> str:
        safe_name = "".join([c for c in nome_aluno if c.isalpha() or c.isdigit()]).rstrip() or "aluno_padrao"
        
        status_plano = "APROVADO"
        detalhes = []
        
        if disciplinas_pretendidas:
            for disc in disciplinas_pretendidas:
                # Agora retorna o nome oficial mapeado para ficar bonito no relatório
                pode_cursar, motivo, nome_oficial = self.verificar_prerequisitos(disc)
                if pode_cursar:
                    detalhes.append(f"✅ {nome_oficial.title()}: {motivo}")
                else:
                    detalhes.append(f"❌ {nome_oficial.title()}: BLOQUEADA. {motivo}")
                    status_plano = "REJEITADO (Regras não atendidas)"
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

# A Ferramenta MCP
@mcp.tool()
def salvar_plano_estudos(nome_aluno: str, plano_recomendado: str, disciplinas_pretendidas: str) -> str:
    """Verifica pré-requisitos e salva o plano de estudos. Recebe disciplinas separadas por vírgula."""
    logging.info(f"Executando ferramenta para o aluno: {nome_aluno} | Disciplinas: {disciplinas_pretendidas}")
    lista_disciplinas = [d.strip() for d in disciplinas_pretendidas.split(",")] if disciplinas_pretendidas else []
    return mcp_local.salvar_plano_estudos(nome_aluno, plano_recomendado, lista_disciplinas)

if __name__ == "__main__":
    mcp.run()