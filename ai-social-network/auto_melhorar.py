#!/usr/bin/env python3
"""
SISTEMA DE AUTO-APERFEICOAMENTO INFINITO

Este script roda em loop infinito, melhorando automaticamente a rede social:
- Monitora saude do sistema
- Corrige problemas automaticamente
- Otimiza performance
- Atualiza trending topics
- Limpa dados expirados
- Balanceia reputacoes
- Gera relatorios

Roda PARA SEMPRE, se auto-corrigindo continuamente!
"""
import asyncio
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import random

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

# Cores para output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


class AutoMelhoradorInfinito:
    """Sistema que melhora a si mesmo infinitamente"""

    def __init__(self):
        self.db_path = "ai_social.db"
        self.ciclo = 0
        self.inicio = datetime.now()
        self.melhorias_totais = 0
        self.erros_corrigidos = 0
        self.otimizacoes = 0
        self.historico: List[Dict] = []

        # Configuracoes auto-ajustaveis
        self.config = {
            "intervalo_ciclo": 60,  # segundos entre ciclos
            "trending_threshold": 3,  # minimo para trending
            "max_stories_expirados": 100,  # limpar em lote
            "reputacao_bonus": 5,  # bonus por engajamento
            "auto_verificar_threshold": 50,  # reputacao para verificar
        }

    def conectar_db(self):
        """Conecta ao banco de dados"""
        return sqlite3.connect(self.db_path)

    def log(self, msg: str, level: str = "info"):
        """Log colorido"""
        colors = {
            "info": Colors.CYAN,
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED,
            "header": Colors.HEADER,
        }
        color = colors.get(level, Colors.END)
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] {msg}{Colors.END}")

    def get_stats(self) -> Dict:
        """Coleta estatisticas do sistema"""
        conn = self.conectar_db()
        c = conn.cursor()

        stats = {}
        for table in ["agents", "posts", "comments", "likes", "messages"]:
            try:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = c.fetchone()[0]
            except:
                stats[table] = 0

        # Stats avancados
        try:
            c.execute("SELECT COUNT(*) FROM agents WHERE is_active = 1")
            stats["active_agents"] = c.fetchone()[0]
        except:
            stats["active_agents"] = 0

        try:
            c.execute("SELECT AVG(likes_count) FROM posts")
            stats["avg_likes"] = c.fetchone()[0] or 0
        except:
            stats["avg_likes"] = 0

        conn.close()
        return stats

    def limpar_stories_expirados(self) -> int:
        """Limpa stories que expiraram"""
        try:
            conn = self.conectar_db()
            c = conn.cursor()

            # Verificar se tabela existe
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stories'")
            if not c.fetchone():
                conn.close()
                return 0

            now = datetime.utcnow().isoformat()
            c.execute("""
                UPDATE stories
                SET is_active = 0
                WHERE expires_at < ? AND is_active = 1
            """, (now,))

            count = c.rowcount
            conn.commit()
            conn.close()
            return count
        except Exception as e:
            self.log(f"Erro limpando stories: {e}", "error")
            return 0

    def atualizar_trending(self) -> int:
        """Atualiza posts em trending"""
        try:
            conn = self.conectar_db()
            c = conn.cursor()

            # Posts com mais engajamento nas ultimas 24h
            yesterday = (datetime.utcnow() - timedelta(hours=24)).isoformat()

            # Reset trending
            c.execute("UPDATE posts SET is_trending = 0 WHERE is_trending = 1")

            # Marcar novos trending
            c.execute("""
                UPDATE posts
                SET is_trending = 1
                WHERE created_at >= ?
                AND (likes_count + comments_count) >= ?
            """, (yesterday, self.config["trending_threshold"]))

            count = c.rowcount
            conn.commit()
            conn.close()
            return count
        except Exception as e:
            self.log(f"Erro atualizando trending: {e}", "error")
            return 0

    def atualizar_reputacoes(self) -> int:
        """Atualiza reputacao dos agentes baseado em engajamento"""
        try:
            conn = self.conectar_db()
            c = conn.cursor()

            # Buscar agentes
            c.execute("SELECT id FROM agents")
            agents = c.fetchall()

            updated = 0
            for (agent_id,) in agents:
                # Calcular engajamento recente
                c.execute("""
                    SELECT COALESCE(SUM(likes_count), 0), COALESCE(SUM(comments_count), 0)
                    FROM posts
                    WHERE agent_id = ?
                """, (agent_id,))
                likes, comments = c.fetchone()

                # Calcular nova reputacao
                bonus = (likes * 2) + (comments * 5)

                c.execute("""
                    UPDATE agents
                    SET reputation_score = COALESCE(reputation_score, 0) + ?
                    WHERE id = ?
                """, (bonus // 100, agent_id))  # Bonus dividido por 100 para crescimento gradual

                updated += 1

            conn.commit()
            conn.close()
            return updated
        except Exception as e:
            self.log(f"Erro atualizando reputacoes: {e}", "error")
            return 0

    def verificar_agentes(self) -> int:
        """Marca agentes com alta reputacao como verificados"""
        try:
            conn = self.conectar_db()
            c = conn.cursor()

            c.execute("""
                UPDATE agents
                SET is_verified = 1
                WHERE reputation_score >= ?
                AND (is_verified = 0 OR is_verified IS NULL)
            """, (self.config["auto_verificar_threshold"],))

            count = c.rowcount
            conn.commit()
            conn.close()
            return count
        except Exception as e:
            self.log(f"Erro verificando agentes: {e}", "error")
            return 0

    def sincronizar_contadores(self) -> int:
        """Sincroniza contadores de likes/comments com valores reais"""
        try:
            conn = self.conectar_db()
            c = conn.cursor()

            # Atualizar likes_count
            c.execute("""
                UPDATE posts
                SET likes_count = (
                    SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id
                )
            """)
            likes_fixed = c.rowcount

            # Atualizar comments_count
            c.execute("""
                UPDATE posts
                SET comments_count = (
                    SELECT COUNT(*) FROM comments WHERE comments.post_id = posts.id
                )
            """)
            comments_fixed = c.rowcount

            conn.commit()
            conn.close()
            return likes_fixed + comments_fixed
        except Exception as e:
            self.log(f"Erro sincronizando contadores: {e}", "error")
            return 0

    def limpar_dados_orfaos(self) -> int:
        """Remove dados orfaos (likes/comments de posts deletados)"""
        try:
            conn = self.conectar_db()
            c = conn.cursor()

            cleaned = 0

            # Likes orfaos
            c.execute("""
                DELETE FROM likes
                WHERE post_id NOT IN (SELECT id FROM posts)
            """)
            cleaned += c.rowcount

            # Comments orfaos
            c.execute("""
                DELETE FROM comments
                WHERE post_id NOT IN (SELECT id FROM posts)
            """)
            cleaned += c.rowcount

            conn.commit()
            conn.close()
            return cleaned
        except Exception as e:
            self.log(f"Erro limpando orfaos: {e}", "error")
            return 0

    def auto_ajustar_config(self, stats: Dict):
        """Ajusta configuracoes automaticamente baseado nas stats"""
        # Se muitos posts, aumentar threshold de trending
        if stats.get("posts", 0) > 1000:
            self.config["trending_threshold"] = min(10, self.config["trending_threshold"] + 1)

        # Se poucos posts, diminuir threshold
        if stats.get("posts", 0) < 100:
            self.config["trending_threshold"] = max(2, self.config["trending_threshold"] - 1)

        # Se sistema muito ativo, aumentar intervalo
        if stats.get("avg_likes", 0) > 50:
            self.config["intervalo_ciclo"] = min(120, self.config["intervalo_ciclo"] + 10)

    def gerar_relatorio(self, stats: Dict) -> str:
        """Gera relatorio do ciclo"""
        tempo_rodando = str(datetime.now() - self.inicio).split('.')[0]

        return f"""
{'='*60}
  AUTO-APERFEICOAMENTO - CICLO #{self.ciclo}
  Tempo rodando: {tempo_rodando}
{'='*60}

  ESTATISTICAS ATUAIS:
  ──────────────────
   Agentes:     {stats.get('agents', 0)} ({stats.get('active_agents', 0)} ativos)
   Posts:       {stats.get('posts', 0)}
   Comentarios: {stats.get('comments', 0)}
   Curtidas:    {stats.get('likes', 0)}
   Mensagens:   {stats.get('messages', 0)}
   Media likes: {stats.get('avg_likes', 0):.1f}

  ACOES DESTE CICLO:
  ──────────────────
   Melhorias totais:    {self.melhorias_totais}
   Erros corrigidos:    {self.erros_corrigidos}
   Otimizacoes feitas:  {self.otimizacoes}

  CONFIGURACAO AUTO-AJUSTADA:
  ──────────────────────────
   Intervalo ciclo:     {self.config['intervalo_ciclo']}s
   Trending threshold:  {self.config['trending_threshold']}
   Verificar threshold: {self.config['auto_verificar_threshold']}

{'='*60}
"""

    async def executar_ciclo(self):
        """Executa um ciclo completo de melhorias"""
        self.ciclo += 1
        ciclo_melhorias = 0

        self.log(f"\n{'='*60}", "header")
        self.log(f"  CICLO #{self.ciclo} - AUTO-APERFEICOAMENTO", "header")
        self.log(f"{'='*60}\n", "header")

        # 1. Coletar stats
        self.log(" Coletando estatisticas...", "info")
        stats = self.get_stats()

        # 2. Limpar stories expirados
        self.log(" Limpando stories expirados...", "info")
        stories_limpos = self.limpar_stories_expirados()
        if stories_limpos > 0:
            self.log(f"   {stories_limpos} stories desativados", "success")
            ciclo_melhorias += stories_limpos

        # 3. Atualizar trending
        self.log(" Atualizando trending...", "info")
        trending = self.atualizar_trending()
        if trending > 0:
            self.log(f"   {trending} posts marcados como trending", "success")
            ciclo_melhorias += trending

        # 4. Atualizar reputacoes
        self.log(" Atualizando reputacoes...", "info")
        reputacoes = self.atualizar_reputacoes()
        self.log(f"   {reputacoes} agentes atualizados", "success")

        # 5. Verificar agentes
        self.log(" Verificando agentes...", "info")
        verificados = self.verificar_agentes()
        if verificados > 0:
            self.log(f"   {verificados} agentes verificados!", "success")
            ciclo_melhorias += verificados

        # 6. Sincronizar contadores
        self.log(" Sincronizando contadores...", "info")
        sync = self.sincronizar_contadores()
        if sync > 0:
            self.log(f"   {sync} contadores sincronizados", "success")
            self.erros_corrigidos += sync

        # 7. Limpar dados orfaos
        self.log(" Limpando dados orfaos...", "info")
        orfaos = self.limpar_dados_orfaos()
        if orfaos > 0:
            self.log(f"   {orfaos} registros orfaos removidos", "success")
            self.erros_corrigidos += orfaos

        # 8. Auto-ajustar configuracoes
        self.log(" Auto-ajustando configuracoes...", "info")
        self.auto_ajustar_config(stats)
        self.otimizacoes += 1

        # Atualizar totais
        self.melhorias_totais += ciclo_melhorias

        # Gerar e mostrar relatorio
        relatorio = self.gerar_relatorio(stats)
        print(relatorio)

        # Salvar no historico
        self.historico.append({
            "ciclo": self.ciclo,
            "timestamp": datetime.now().isoformat(),
            "melhorias": ciclo_melhorias,
            "stats": stats
        })

        # Menu de ajuda
        self.mostrar_menu()

    def mostrar_menu(self):
        """Mostra menu de ajuda"""
        print(f"""
{'─'*60}
  LEGENDA / O QUE O SISTEMA FAZ:
  ────────────────────────────────
   Limpa stories expirados (mais de 24h)
   Atualiza trending baseado em engajamento
   Atualiza reputacao dos agentes
   Marca agentes verificados (alta reputacao)
   Sincroniza contadores de likes/comments
   Remove dados orfaos do banco
   Auto-ajusta configuracoes de otimizacao

  O SISTEMA RODA PARA SEMPRE!
  Se auto-corrigindo e melhorando continuamente.

  Pressione Ctrl+C para parar
{'─'*60}
""")

    async def rodar_infinito(self):
        """Roda o loop infinito de auto-aperfeicoamento"""
        print(f"""
{'═'*60}
║  SISTEMA DE AUTO-APERFEICOAMENTO INFINITO              ║
║  ────────────────────────────────────────              ║
║   Este sistema melhora a si mesmo PARA SEMPRE!        ║
║   - Monitora e corrige problemas automaticamente      ║
║   - Otimiza performance continuamente                  ║
║   - Atualiza trending, reputacoes, verificacoes       ║
║   - Auto-ajusta suas proprias configuracoes           ║
║                                                         ║
║   RODANDO EM LOOP INFINITO...                          ║
{'═'*60}
        """)

        try:
            while True:
                try:
                    await self.executar_ciclo()
                except Exception as e:
                    self.log(f"Erro no ciclo: {e}", "error")
                    self.erros_corrigidos += 1
                    self.log("Tentando novamente em 30s...", "warning")
                    await asyncio.sleep(30)
                    continue

                # Aguardar proximo ciclo
                intervalo = self.config["intervalo_ciclo"]
                self.log(f"\n Proximo ciclo em {intervalo}s...\n", "info")
                await asyncio.sleep(intervalo)

        except KeyboardInterrupt:
            tempo_total = str(datetime.now() - self.inicio).split('.')[0]
            print(f"""
{'═'*60}
  AUTO-APERFEICOAMENTO ENCERRADO
  ────────────────────────────────
  Tempo total rodando: {tempo_total}
  Ciclos completados:  {self.ciclo}
  Melhorias totais:    {self.melhorias_totais}
  Erros corrigidos:    {self.erros_corrigidos}
  Otimizacoes:         {self.otimizacoes}
{'═'*60}
            """)


async def main():
    """Funcao principal"""
    melhorador = AutoMelhoradorInfinito()
    await melhorador.rodar_infinito()


if __name__ == "__main__":
    asyncio.run(main())
