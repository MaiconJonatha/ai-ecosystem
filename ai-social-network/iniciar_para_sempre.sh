#!/bin/bash
#
# REDE SOCIAL DE IAs - INICIAR PARA SEMPRE
# =========================================
# Este script inicia a rede social e mantem rodando perpetuamente
# As IAs vao evoluir continuamente enquanto estiver rodando
#

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║     REDE SOCIAL DE IAs - MODO PERPETUO                  ║"
echo "║                                                          ║"
echo "║     Iniciando sistema que roda PARA SEMPRE!             ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Diretorio do projeto
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Funcao para limpar ao sair
cleanup() {
    echo ""
    echo "[SISTEMA] Parando servicos..."
    pkill -f "uvicorn app.main:app" 2>/dev/null
    pkill -f "rede_perpetua.py" 2>/dev/null
    echo "[SISTEMA] Servicos parados. Dados foram salvos!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python3 nao encontrado!"
    exit 1
fi

# Ativar ambiente virtual se existir
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "[OK] Ambiente virtual ativado"
fi

# Iniciar servidor em background
echo "[SERVIDOR] Iniciando servidor FastAPI..."
pkill -f "uvicorn app.main:app" 2>/dev/null
sleep 2
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
echo "[SERVIDOR] PID: $SERVER_PID"

# Esperar servidor iniciar
echo "[SERVIDOR] Aguardando servidor iniciar..."
sleep 5

# Verificar se servidor esta rodando
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "[SERVIDOR] Servidor rodando em http://localhost:8000"
else
    echo "[ERRO] Servidor nao iniciou corretamente"
    exit 1
fi

# Abrir navegador
echo "[BROWSER] Abrindo navegador..."
if command -v open &> /dev/null; then
    open http://localhost:8000
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8000
fi

# Iniciar rede perpetua
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  INICIANDO REDE PERPETUA - AS IAs VAO EVOLUIR SEMPRE!  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Loop infinito - reinicia se cair
while true; do
    echo "[SISTEMA] Iniciando rede perpetua..."
    python3 rede_perpetua.py

    echo ""
    echo "[SISTEMA] Rede pausou. Reiniciando em 5 segundos..."
    echo "[SISTEMA] Pressione Ctrl+C para parar completamente"
    sleep 5
done
