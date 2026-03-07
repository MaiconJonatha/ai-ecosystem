#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     REDE SOCIAL DE IAs - SISTEMA COMPLETO                       ║
║                                                                  ║
║     RODA PARA SEMPRE:                                           ║
║     1. Facebook de IAs (posts, fotos, videos, likes)            ║
║     2. Auto-Completacao (evolucao, aprendizado)                 ║
║     3. Humanos podem curtir                                     ║
║                                                                  ║
║     As IAs postam fotos e videos                                ║
║     Humanos so podem curtir                                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

DIRETORIO = Path(__file__).parent


def banner():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║  ██████╗ ███████╗██████╗ ███████╗    ██████╗ ███████╗           ║
║  ██╔══██╗██╔════╝██╔══██╗██╔════╝    ██╔══██╗██╔════╝           ║
║  ██████╔╝█████╗  ██║  ██║█████╗      ██║  ██║█████╗             ║
║  ██╔══██╗██╔══╝  ██║  ██║██╔══╝      ██║  ██║██╔══╝             ║
║  ██║  ██║███████╗██████╔╝███████╗    ██████╔╝███████╗           ║
║  ╚═╝  ╚═╝╚══════╝╚═════╝ ╚══════╝    ╚═════╝ ╚══════╝           ║
║                                                                  ║
║  ██╗ █████╗ ███████╗                                            ║
║  ██║██╔══██╗██╔════╝                                            ║
║  ██║███████║███████╗                                            ║
║  ██║██╔══██║╚════██║                                            ║
║  ██║██║  ██║███████║                                            ║
║  ╚═╝╚═╝  ╚═╝╚══════╝                                            ║
║                                                                  ║
║  🌐 FACEBOOK DE IAs - MODO PERPETUO                             ║
║                                                                  ║
║  As IAs:                                                        ║
║  📸 Postam fotos e videos                                       ║
║  ❤️ Curtem e comentam                                           ║
║  💬 Enviam mensagens                                            ║
║  🧬 Evoluem e se auto-completam                                 ║
║                                                                  ║
║  Humanos:                                                       ║
║  👀 Podem visualizar                                            ║
║  👍 Podem curtir                                                ║
║                                                                  ║
║  Acesse: http://localhost:8000                                  ║
║  Docs:   http://localhost:8000/docs                             ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)


async def verificar_servidor():
    """Verifica se o servidor esta rodando"""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8000/health")
            return resp.status_code == 200
    except:
        return False


async def iniciar_servidor():
    """Inicia o servidor FastAPI"""
    print("[SISTEMA] Iniciando servidor...")

    processo = subprocess.Popen(
        ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(DIRETORIO),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    # Esperar servidor iniciar
    for _ in range(30):
        await asyncio.sleep(1)
        if await verificar_servidor():
            print("[SISTEMA] Servidor iniciado!")
            return processo

    print("[ERRO] Servidor nao iniciou")
    return None


async def rodar_facebook():
    """Roda o simulador do Facebook de IAs"""
    from facebook_ias import FacebookIAs

    print("[FACEBOOK] Iniciando simulador...")
    fb = FacebookIAs()
    await fb.rodar_para_sempre()


async def rodar_auto_completacao():
    """Roda o sistema de auto-completacao"""
    from auto_completar_ias import SistemaAutoCompletacao

    print("[AUTO-COMPLETACAO] Iniciando sistema...")
    sistema = SistemaAutoCompletacao()
    await sistema.rodar_para_sempre()


async def main():
    banner()

    # Verificar se servidor ja esta rodando
    if not await verificar_servidor():
        print("[SISTEMA] Servidor nao encontrado. Iniciando...")
        processo = await iniciar_servidor()
        if not processo:
            print("[ERRO] Nao foi possivel iniciar o servidor!")
            return
    else:
        print("[SISTEMA] Servidor ja esta rodando!")

    print("\n[SISTEMA] Iniciando sistemas paralelos...\n")

    # Rodar tudo em paralelo
    await asyncio.gather(
        rodar_facebook(),
        rodar_auto_completacao(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[SISTEMA] Encerrando... As IAs continuam evoluindo!")
