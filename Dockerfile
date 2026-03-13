# Usa uma imagem oficial e leve do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências do sistema necessárias para algumas bibliotecas de IA
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia os requisitos e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto para dentro do container
COPY . .

# Garante que o Python reconheça a raiz do projeto (substitui o PYTHONPATH=.)
ENV PYTHONPATH=/app

# Expõe a porta padrão do Streamlit
EXPOSE 8501

# Comando para iniciar a interface
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]