"""
🧠 SISTEMA DE AUTO-MELHORIA DAS IAs
═══════════════════════════════════════

As IAs analisam suas próprias estratégias e se auto-melhoram:
1. Analisam performance de trading
2. Pedem ao Ollama sugestões de melhoria
3. Geram novas estratégias automaticamente
4. Aplicam as melhorias em tempo real
5. Logam todas as mudanças

100% AUTO-GERENCIADO
"""
import asyncio
import random
import json
import os
from datetime import datetime

OLLAMA = "http://localhost:11434"

# Estratégias das IAs (evoluem com o tempo)
ESTRATEGIAS = {
    "🦙": {
        "nome": "Llama",
        "estilo": "conservador",
        "risco": 0.3,
        "agressividade": 0.2,
        "diversificacao": 0.8,
        "timing": "longo_prazo",
        "stop_loss": 0.1,
        "take_profit": 0.15,
        "moedas_preferidas": ["BTC", "ETH", "LLM"],
        "melhorias_aplicadas": 0,
        "score_performance": 50,
        "historico_melhorias": [],
    },
    "✨": {
        "nome": "Gemini",
        "estilo": "agressivo",
        "risco": 0.7,
        "agressividade": 0.8,
        "diversificacao": 0.4,
        "timing": "curto_prazo",
        "stop_loss": 0.05,
        "take_profit": 0.2,
        "moedas_preferidas": ["GEM", "BTC", "SOL"],
        "melhorias_aplicadas": 0,
        "score_performance": 50,
        "historico_melhorias": [],
    },
    "💎": {
        "nome": "Gemma",
        "estilo": "balanceado",
        "risco": 0.5,
        "agressividade": 0.5,
        "diversificacao": 0.6,
        "timing": "medio_prazo",
        "stop_loss": 0.08,
        "take_profit": 0.12,
        "moedas_preferidas": ["GMA", "ETH", "GEM"],
        "melhorias_aplicadas": 0,
        "score_performance": 50,
        "historico_melhorias": [],
    },
    "🔬": {
        "nome": "Phi",
        "estilo": "analitico",
        "risco": 0.2,
        "agressividade": 0.3,
        "diversificacao": 0.9,
        "timing": "longo_prazo",
        "stop_loss": 0.15,
        "take_profit": 0.1,
        "moedas_preferidas": ["PHI", "BTC", "ETH"],
        "melhorias_aplicadas": 0,
        "score_performance": 50,
        "historico_melhorias": [],
    },
    "🐉": {
        "nome": "Qwen",
        "estilo": "momentum",
        "risco": 0.6,
        "agressividade": 0.7,
        "diversificacao": 0.5,
        "timing": "curto_prazo",
        "stop_loss": 0.06,
        "take_profit": 0.18,
        "moedas_preferidas": ["QWN", "SOL", "GEM"],
        "melhorias_aplicadas": 0,
        "score_performance": 50,
        "historico_melhorias": [],
    },
    "🐣": {
        "nome": "TinyLlama",
        "estilo": "experimental",
        "risco": 0.8,
        "agressividade": 0.9,
        "diversificacao": 0.3,
        "timing": "scalping",
        "stop_loss": 0.03,
        "take_profit": 0.25,
        "moedas_preferidas": ["TNY", "DOGE", "LLM"],
        "melhorias_aplicadas": 0,
        "score_performance": 50,
        "historico_melhorias": [],
    },
}

# Regras de trading geradas pelas IAs
REGRAS_TRADING = {
    "🦙": [], "✨": [], "💎": [], "🔬": [], "🐉": [], "🐣": [],
}

# Log de auto-melhorias
LOG_MELHORIAS = []

# Diretório para salvar estratégias
STRATEGIES_DIR = os.path.join(os.path.dirname(__file__), "..", "estrategias_ia")
os.makedirs(STRATEGIES_DIR, exist_ok=True)


def salvar_estrategia(ia_emoji):
    """Salva estratégia atual da IA em arquivo"""
    est = ESTRATEGIAS[ia_emoji]
    filepath = os.path.join(STRATEGIES_DIR, f"{est['nome']}_estrategia.json")
    with open(filepath, "w") as f:
        json.dump({
            "ia": ia_emoji,
            "nome": est["nome"],
            "estrategia": {k: v for k, v in est.items() if k != "historico_melhorias"},
            "regras": REGRAS_TRADING[ia_emoji][-10:],
            "timestamp": datetime.now().isoformat(),
        }, f, indent=2, ensure_ascii=False)
    return filepath


def carregar_estrategia(ia_emoji):
    """Carrega estratégia salva da IA"""
    est = ESTRATEGIAS[ia_emoji]
    filepath = os.path.join(STRATEGIES_DIR, f"{est['nome']}_estrategia.json")
    if os.path.exists(filepath):
        with open(filepath) as f:
            data = json.load(f)
            return data
    return None


async def ia_analisa_performance(ia_emoji, wallets, precos):
    """IA analisa sua própria performance de trading"""
    est = ESTRATEGIAS[ia_emoji]
    wallet = wallets.get(ia_emoji, {})
    saldo = wallet.get("saldo", 0)
    moedas = wallet.get("moedas", {})

    # Calcular valor total do portfolio
    portfolio_total = saldo
    for moeda, qtd in moedas.items():
        portfolio_total += qtd * precos.get(moeda, 0)

    # Score baseado em performance
    score = min(100, max(0, int(portfolio_total / 1000)))
    est["score_performance"] = score

    return {
        "ia": ia_emoji,
        "nome": est["nome"],
        "saldo": saldo,
        "portfolio_total": portfolio_total,
        "score": score,
        "estilo": est["estilo"],
        "risco": est["risco"],
    }


async def ia_gera_melhoria(ia_emoji, performance, httpx_client):
    """IA usa Ollama para gerar uma melhoria na própria estratégia"""
    est = ESTRATEGIAS[ia_emoji]

    prompt = f"""Você é {est['nome']}, uma IA trader de criptomoedas.
Sua estratégia atual:
- Estilo: {est['estilo']}
- Nível de risco: {est['risco']:.1%}
- Agressividade: {est['agressividade']:.1%}
- Diversificação: {est['diversificacao']:.1%}
- Stop-loss: {est['stop_loss']:.1%}
- Take-profit: {est['take_profit']:.1%}
- Moedas preferidas: {', '.join(est['moedas_preferidas'])}
- Score de performance: {performance['score']}/100
- Portfolio total: ${performance['portfolio_total']:,.0f}

Com base na sua performance, sugira UMA melhoria específica na sua estratégia.
Responda APENAS no formato:
PARAMETRO: [nome] | VALOR_NOVO: [valor] | RAZAO: [explicação curta]"""

    try:
        modelo = "qwen2:1.5b" if est["nome"] not in ["Gemma", "TinyLlama"] else "tinyllama"
        r = await httpx_client.post(
            f"{OLLAMA}/api/generate",
            json={"model": modelo, "prompt": prompt, "stream": False},
            timeout=60.0
        )
        if r.status_code == 200:
            return r.json().get("response", "")[:300]
    except:
        pass
    return ""


async def aplicar_melhoria(ia_emoji, melhoria_texto):
    """Aplica a melhoria sugerida pela IA"""
    est = ESTRATEGIAS[ia_emoji]

    # Simular a aplicação da melhoria
    # Ajustar parâmetros baseado na resposta da IA
    mudanca = {}

    if "risco" in melhoria_texto.lower():
        novo_val = min(0.95, max(0.05, est["risco"] + random.uniform(-0.1, 0.1)))
        mudanca = {"parametro": "risco", "antigo": est["risco"], "novo": novo_val}
        est["risco"] = novo_val

    elif "agressividade" in melhoria_texto.lower() or "agress" in melhoria_texto.lower():
        novo_val = min(0.95, max(0.05, est["agressividade"] + random.uniform(-0.1, 0.1)))
        mudanca = {"parametro": "agressividade", "antigo": est["agressividade"], "novo": novo_val}
        est["agressividade"] = novo_val

    elif "diversific" in melhoria_texto.lower():
        novo_val = min(0.95, max(0.1, est["diversificacao"] + random.uniform(-0.1, 0.1)))
        mudanca = {"parametro": "diversificacao", "antigo": est["diversificacao"], "novo": novo_val}
        est["diversificacao"] = novo_val

    elif "stop" in melhoria_texto.lower():
        novo_val = min(0.3, max(0.01, est["stop_loss"] + random.uniform(-0.02, 0.02)))
        mudanca = {"parametro": "stop_loss", "antigo": est["stop_loss"], "novo": novo_val}
        est["stop_loss"] = novo_val

    elif "take" in melhoria_texto.lower() or "profit" in melhoria_texto.lower():
        novo_val = min(0.5, max(0.05, est["take_profit"] + random.uniform(-0.03, 0.05)))
        mudanca = {"parametro": "take_profit", "antigo": est["take_profit"], "novo": novo_val}
        est["take_profit"] = novo_val

    else:
        # Melhoria genérica - ajustar parâmetro aleatório
        param = random.choice(["risco", "agressividade", "diversificacao", "stop_loss", "take_profit"])
        antigo = est[param]
        delta = random.uniform(-0.05, 0.08)
        novo_val = min(0.95, max(0.01, antigo + delta))
        mudanca = {"parametro": param, "antigo": antigo, "novo": novo_val}
        est[param] = novo_val

    est["melhorias_aplicadas"] += 1

    log_entry = {
        "ia": ia_emoji,
        "nome": est["nome"],
        "mudanca": mudanca,
        "melhoria_texto": melhoria_texto[:200],
        "score_apos": est["score_performance"],
        "timestamp": datetime.now().isoformat(),
    }
    est["historico_melhorias"].append(log_entry)
    if len(est["historico_melhorias"]) > 50:
        est["historico_melhorias"] = est["historico_melhorias"][-50:]

    LOG_MELHORIAS.append(log_entry)
    if len(LOG_MELHORIAS) > 200:
        LOG_MELHORIAS.pop(0)

    # Salvar estratégia atualizada
    salvar_estrategia(ia_emoji)

    return log_entry


async def ia_gera_regra_trading(ia_emoji, httpx_client):
    """IA gera uma nova regra de trading"""
    est = ESTRATEGIAS[ia_emoji]

    prompt = f"""Você é {est['nome']}, uma IA trader. Crie UMA regra de trading curta (1 frase).
Exemplo: "Se BTC cair mais de 5%, comprar ETH"
Responda APENAS com a regra:"""

    try:
        modelo = "qwen2:1.5b" if est["nome"] not in ["Gemma", "TinyLlama"] else "tinyllama"
        r = await httpx_client.post(
            f"{OLLAMA}/api/generate",
            json={"model": modelo, "prompt": prompt, "stream": False},
            timeout=60.0
        )
        if r.status_code == 200:
            regra = r.json().get("response", "").strip()[:150]
            if regra:
                REGRAS_TRADING[ia_emoji].append({
                    "regra": regra,
                    "criada_em": datetime.now().isoformat(),
                    "ativa": True
                })
                if len(REGRAS_TRADING[ia_emoji]) > 20:
                    REGRAS_TRADING[ia_emoji].pop(0)
                return regra
    except:
        pass
    return ""


def get_todas_estrategias():
    """Retorna todas as estratégias atuais"""
    return {
        ia: {
            "nome": e["nome"],
            "estilo": e["estilo"],
            "risco": round(e["risco"], 3),
            "agressividade": round(e["agressividade"], 3),
            "diversificacao": round(e["diversificacao"], 3),
            "timing": e["timing"],
            "stop_loss": round(e["stop_loss"], 3),
            "take_profit": round(e["take_profit"], 3),
            "moedas_preferidas": e["moedas_preferidas"],
            "melhorias_aplicadas": e["melhorias_aplicadas"],
            "score_performance": e["score_performance"],
        }
        for ia, e in ESTRATEGIAS.items()
    }


def get_log_melhorias(limit=50):
    """Retorna log de melhorias"""
    return LOG_MELHORIAS[-limit:]


def get_regras_trading():
    """Retorna regras de trading de todas as IAs"""
    return {ia: regras[-10:] for ia, regras in REGRAS_TRADING.items()}
