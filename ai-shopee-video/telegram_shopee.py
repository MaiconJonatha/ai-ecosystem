#!/usr/bin/env python3
"""
Telegram → Shopee Video Pipeline
Monitora canais do Telegram para baixar vídeos de produtos e repostar no Shopee Video.

Modos:
  1. Monitor: Conecta em canais e baixa vídeos automaticamente
  2. Bot: Recebe vídeos encaminhados e posta no Shopee Video
  3. Ambos: Monitor + Bot simultâneo

Uso:
  python3 telegram_shopee.py --login                    # Primeiro login (pede código SMS)
  python3 telegram_shopee.py --monitor                  # Monitorar canais
  python3 telegram_shopee.py --bot                      # Modo bot (recebe vídeos)
  python3 telegram_shopee.py --both                     # Monitor + Bot
  python3 telegram_shopee.py --list-channels            # Listar canais que você participa
  python3 telegram_shopee.py --add-channel CANAL        # Adicionar canal para monitorar
  python3 telegram_shopee.py --post-pending             # Postar vídeos pendentes no Shopee
"""
import asyncio, json, os, sys, argparse, hashlib, re, glob, time
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto

try:
    sys.stdout.reconfigure(line_buffering=True)
except:
    pass

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

# === CONFIG ===
CONFIG_FILE = os.path.join(DIR, "telegram_config.json")
VIDEOS_DIR = os.path.join(DIR, "static", "videos", "telegram")
PENDING_FILE = os.path.join(DIR, "telegram_pending.json")
LOG_FILE = os.path.join(DIR, "telegram_shopee.log")
SESSION_FILE = os.path.join(DIR, "telegram_session")

os.makedirs(VIDEOS_DIR, exist_ok=True)

# Palavras-chave para filtrar vídeos de produtos Shopee
KEYWORDS_SHOPEE = [
    "shopee", "shp.ee", "s.shopee", "compre", "link na bio",
    "promoção", "desconto", "oferta", "achado", "barato",
    "frete grátis", "cupom", "afiliado", "recomendo",
    "produto", "review", "unboxing", "testei",
]


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")


def load_config():
    """Carrega configuração (api_id, api_hash, canais)"""
    default = {
        "api_id": "",
        "api_hash": "",
        "phone": "",
        "channels": [],
        "auto_post": False,
        "filter_keywords": True,
        "max_videos_per_channel": 10,
        "download_interval": 60,
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
            default.update(cfg)
    return default


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def load_pending():
    """Carrega lista de vídeos pendentes para postar"""
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE) as f:
            return json.load(f)
    return []


def save_pending(pending):
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f, indent=2, ensure_ascii=False)


def is_shopee_video(message):
    """Verifica se a mensagem contém vídeo relacionado a Shopee"""
    if not message.media:
        return False

    # Verificar se é vídeo
    is_video = False
    if isinstance(message.media, MessageMediaDocument):
        doc = message.media.document
        if doc:
            for attr in doc.attributes:
                if hasattr(attr, 'mime_type') or (hasattr(attr, 'duration') and hasattr(attr, 'w')):
                    is_video = True
                    break
            if doc.mime_type and 'video' in doc.mime_type:
                is_video = True

    if not is_video:
        return False

    # Se filtro de keywords ativo, verificar texto
    text = (message.text or message.message or "").lower()
    if not text:
        return True  # Vídeo sem texto = aceitar

    for kw in KEYWORDS_SHOPEE:
        if kw.lower() in text:
            return True

    return False


def extract_shopee_link(text):
    """Extrai link do Shopee do texto da mensagem"""
    if not text:
        return None
    patterns = [
        r'(https?://s\.shopee\.com\.br/\S+)',
        r'(https?://shp\.ee/\S+)',
        r'(https?://shopee\.com\.br/\S+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


async def get_client(config):
    """Cria cliente Telethon"""
    if not config.get("api_id") or not config.get("api_hash"):
        log("❌ Configure api_id e api_hash primeiro!")
        log("   Acesse: https://my.telegram.org → API development tools")
        log(f"   Edite: {CONFIG_FILE}")
        return None

    client = TelegramClient(
        SESSION_FILE,
        int(config["api_id"]),
        config["api_hash"]
    )
    return client


# === LOGIN ===

HASH_FILE = os.path.join(DIR, ".telegram_code_hash")

async def telegram_login(config, code=None):
    """Login no Telegram - envia SMS e depois valida código"""
    client = await get_client(config)
    if not client:
        return

    phone = config.get("phone", "")
    await client.connect()

    if not await client.is_user_authorized():
        if not code:
            # Passo 1: Enviar código SMS
            result = await client.send_code_request(phone)
            # Salvar phone_code_hash para usar depois
            with open(HASH_FILE, "w") as f:
                f.write(result.phone_code_hash)
            log("📱 Código SMS enviado! Rode novamente com --code XXXXX")
            await client.disconnect()
            return
        else:
            # Passo 2: Validar código
            phone_code_hash = ""
            if os.path.exists(HASH_FILE):
                with open(HASH_FILE) as f:
                    phone_code_hash = f.read().strip()
            try:
                await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            except Exception as e:
                if "password" in str(e).lower() or "2fa" in str(e).lower() or "SessionPasswordNeeded" in str(type(e).__name__):
                    log("🔐 Conta tem 2FA. Rode com --code XXXXX --password SUA_SENHA")
                    await client.disconnect()
                    return
                raise
            # Limpar hash
            if os.path.exists(HASH_FILE):
                os.remove(HASH_FILE)

    me = await client.get_me()
    log(f"✅ Logado como: {me.first_name} (@{me.username}) - ID: {me.id}")
    await client.disconnect()


# === LISTAR CANAIS ===

async def list_channels(config):
    """Lista canais/grupos que o usuário participa"""
    client = await get_client(config)
    if not client:
        return

    await client.start(phone=config.get("phone", ""))
    log("📋 Listando canais e grupos...\n")

    async for dialog in client.iter_dialogs():
        if dialog.is_channel or dialog.is_group:
            entity = dialog.entity
            members = getattr(entity, 'participants_count', '?')
            tipo = "📢 Canal" if dialog.is_channel else "👥 Grupo"
            monitored = "✅" if str(dialog.id) in [str(c) for c in config.get("channels", [])] else "  "
            print(f"  {monitored} {tipo} | {dialog.name[:40]:<40} | ID: {dialog.id} | {members} membros")

    print(f"\n💡 Para adicionar: python3 telegram_shopee.py --add-channel ID_OU_NOME")
    await client.disconnect()


# === ADICIONAR CANAL ===

async def add_channel(config, channel_input):
    """Adiciona canal para monitorar"""
    client = await get_client(config)
    if not client:
        return

    await client.start(phone=config.get("phone", ""))

    try:
        # Tentar como ID numérico
        try:
            channel_id = int(channel_input)
            entity = await client.get_entity(channel_id)
        except ValueError:
            # Tentar como username
            entity = await client.get_entity(channel_input)

        channel_info = {
            "id": entity.id,
            "name": getattr(entity, 'title', str(entity.id)),
            "username": getattr(entity, 'username', None),
            "added": datetime.now().isoformat(),
        }

        channels = config.get("channels", [])
        # Evitar duplicatas
        existing_ids = [c["id"] if isinstance(c, dict) else c for c in channels]
        if entity.id not in existing_ids:
            channels.append(channel_info)
            config["channels"] = channels
            save_config(config)
            log(f"✅ Canal adicionado: {channel_info['name']} (ID: {entity.id})")
        else:
            log(f"⚠️ Canal já está na lista: {channel_info['name']}")

    except Exception as e:
        log(f"❌ Erro ao adicionar canal: {e}")

    await client.disconnect()


# === MONITOR DE CANAIS ===

async def monitor_channels(config):
    """Monitora canais e baixa vídeos de produtos"""
    client = await get_client(config)
    if not client:
        return

    await client.start(phone=config.get("phone", ""))
    me = await client.get_me()
    log(f"✅ Logado: {me.first_name}")

    channels = config.get("channels", [])
    if not channels:
        log("⚠️ Nenhum canal configurado! Use --list-channels e --add-channel")
        await client.disconnect()
        return

    channel_ids = [c["id"] if isinstance(c, dict) else c for c in channels]
    channel_names = {(c["id"] if isinstance(c, dict) else c): (c.get("name", "?") if isinstance(c, dict) else "?") for c in channels}

    log(f"👁️ Monitorando {len(channel_ids)} canais:")
    for cid in channel_ids:
        log(f"  📢 {channel_names.get(cid, cid)}")

    pending = load_pending()
    downloaded_ids = {p.get("msg_id") for p in pending}
    filter_kw = config.get("filter_keywords", True)

    # Handler para novas mensagens
    @client.on(events.NewMessage(chats=channel_ids))
    async def handler(event):
        nonlocal pending, downloaded_ids

        msg = event.message
        text = msg.text or msg.message or ""

        # Verificar se é vídeo
        if not msg.media or not isinstance(msg.media, MessageMediaDocument):
            return

        doc = msg.media.document
        if not doc or not doc.mime_type or 'video' not in doc.mime_type:
            return

        # Filtrar por keywords se ativado
        if filter_kw and text:
            has_keyword = any(kw.lower() in text.lower() for kw in KEYWORDS_SHOPEE)
            if not has_keyword:
                log(f"  ⏭️ Vídeo ignorado (sem keyword): {text[:50]}")
                return

        # Evitar duplicatas
        msg_id = f"{msg.chat_id}_{msg.id}"
        if msg_id in downloaded_ids:
            return

        # Download
        chat_name = channel_names.get(msg.chat_id, str(msg.chat_id))
        video_hash = hashlib.md5(f"{msg_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:10]
        video_path = os.path.join(VIDEOS_DIR, f"tg_{video_hash}.mp4")

        log(f"📥 Baixando vídeo de [{chat_name}]: {text[:60]}")
        try:
            await client.download_media(msg, file=video_path)

            if os.path.exists(video_path) and os.path.getsize(video_path) > 10000:
                size_mb = os.path.getsize(video_path) / (1024 * 1024)
                shopee_link = extract_shopee_link(text)

                entry = {
                    "msg_id": msg_id,
                    "channel": chat_name,
                    "channel_id": msg.chat_id,
                    "text": text[:500],
                    "shopee_link": shopee_link,
                    "video_path": video_path,
                    "size_mb": round(size_mb, 2),
                    "downloaded_at": datetime.now().isoformat(),
                    "posted_to_shopee": False,
                }
                pending.append(entry)
                downloaded_ids.add(msg_id)
                save_pending(pending)

                log(f"  ✅ Salvo: {os.path.basename(video_path)} ({size_mb:.1f}MB)")
                if shopee_link:
                    log(f"  🔗 Link Shopee: {shopee_link}")

                # Auto-post se configurado
                if config.get("auto_post"):
                    await auto_post_single(entry)
            else:
                log(f"  ⚠️ Download falhou ou arquivo muito pequeno")
                if os.path.exists(video_path):
                    os.remove(video_path)

        except Exception as e:
            log(f"  ❌ Erro download: {e}")

    # Também buscar mensagens recentes dos canais (últimas 24h)
    log("\n📂 Buscando vídeos recentes nos canais...")
    max_per_channel = config.get("max_videos_per_channel", 10)

    for cid in channel_ids:
        try:
            count = 0
            async for msg in client.iter_messages(cid, limit=50):
                if count >= max_per_channel:
                    break

                if not msg.media or not isinstance(msg.media, MessageMediaDocument):
                    continue

                doc = msg.media.document
                if not doc or not doc.mime_type or 'video' not in doc.mime_type:
                    continue

                text = msg.text or msg.message or ""
                msg_id = f"{msg.chat_id}_{msg.id}"

                if msg_id in downloaded_ids:
                    continue

                if filter_kw and text and not any(kw.lower() in text.lower() for kw in KEYWORDS_SHOPEE):
                    continue

                video_hash = hashlib.md5(f"{msg_id}".encode()).hexdigest()[:10]
                video_path = os.path.join(VIDEOS_DIR, f"tg_{video_hash}.mp4")

                log(f"📥 [{channel_names.get(cid, cid)}] Baixando: {text[:50]}")
                try:
                    await client.download_media(msg, file=video_path)
                    if os.path.exists(video_path) and os.path.getsize(video_path) > 10000:
                        size_mb = os.path.getsize(video_path) / (1024 * 1024)
                        shopee_link = extract_shopee_link(text)
                        entry = {
                            "msg_id": msg_id,
                            "channel": channel_names.get(cid, str(cid)),
                            "channel_id": cid,
                            "text": text[:500],
                            "shopee_link": shopee_link,
                            "video_path": video_path,
                            "size_mb": round(size_mb, 2),
                            "downloaded_at": datetime.now().isoformat(),
                            "posted_to_shopee": False,
                        }
                        pending.append(entry)
                        downloaded_ids.add(msg_id)
                        count += 1
                        log(f"  ✅ {os.path.basename(video_path)} ({size_mb:.1f}MB)")
                    else:
                        if os.path.exists(video_path):
                            os.remove(video_path)
                except Exception as e:
                    log(f"  ⚠️ {e}")

            save_pending(pending)
            log(f"  📢 {channel_names.get(cid, cid)}: {count} vídeos baixados")

        except Exception as e:
            log(f"  ❌ Erro no canal {cid}: {e}")

    total_pending = sum(1 for p in pending if not p.get("posted_to_shopee"))
    log(f"\n📊 Total pendentes para Shopee: {total_pending}")
    log("👁️ Monitorando novas mensagens... (Ctrl+C para parar)")

    # Ficar online monitorando
    await client.run_until_disconnected()


# === BOT MODE (recebe vídeos encaminhados) ===

async def bot_mode(config):
    """Modo bot: recebe vídeos encaminhados pelo usuário"""
    client = await get_client(config)
    if not client:
        return

    await client.start(phone=config.get("phone", ""))
    me = await client.get_me()
    log(f"✅ Bot mode ativo - Logado: {me.first_name}")
    log("📩 Encaminhe vídeos de canais para o chat 'Mensagens Salvas'")

    pending = load_pending()
    downloaded_ids = {p.get("msg_id") for p in pending}

    # Monitorar Mensagens Salvas (Saved Messages)
    @client.on(events.NewMessage(from_users='me'))
    async def saved_handler(event):
        nonlocal pending, downloaded_ids
        msg = event.message

        # Só processar se for vídeo
        if not msg.media or not isinstance(msg.media, MessageMediaDocument):
            return

        doc = msg.media.document
        if not doc or not doc.mime_type or 'video' not in doc.mime_type:
            return

        text = msg.text or msg.message or ""
        msg_id = f"saved_{msg.id}"

        if msg_id in downloaded_ids:
            return

        video_hash = hashlib.md5(f"{msg_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:10]
        video_path = os.path.join(VIDEOS_DIR, f"tg_manual_{video_hash}.mp4")

        log(f"📩 Vídeo recebido (manual): {text[:60]}")
        try:
            await client.download_media(msg, file=video_path)

            if os.path.exists(video_path) and os.path.getsize(video_path) > 10000:
                size_mb = os.path.getsize(video_path) / (1024 * 1024)
                shopee_link = extract_shopee_link(text)

                entry = {
                    "msg_id": msg_id,
                    "channel": "Manual (Saved Messages)",
                    "channel_id": "saved",
                    "text": text[:500],
                    "shopee_link": shopee_link,
                    "video_path": video_path,
                    "size_mb": round(size_mb, 2),
                    "downloaded_at": datetime.now().isoformat(),
                    "posted_to_shopee": False,
                }
                pending.append(entry)
                downloaded_ids.add(msg_id)
                save_pending(pending)

                log(f"  ✅ Salvo: {os.path.basename(video_path)} ({size_mb:.1f}MB)")

                # Responder confirmando
                await event.reply(f"✅ Vídeo salvo!\n📁 {os.path.basename(video_path)}\n💾 {size_mb:.1f}MB\n🔗 {shopee_link or 'Sem link Shopee'}")
        except Exception as e:
            log(f"  ❌ Erro: {e}")

    log("👁️ Aguardando vídeos... (encaminhe para Saved Messages)")
    await client.run_until_disconnected()


# === POSTAR PENDENTES NO SHOPEE ===

async def post_pending_to_shopee():
    """Posta vídeos pendentes no Shopee Video"""
    pending = load_pending()
    not_posted = [p for p in pending if not p.get("posted_to_shopee")]

    if not not_posted:
        log("✅ Nenhum vídeo pendente para postar!")
        return

    log(f"📤 {len(not_posted)} vídeos pendentes para Shopee Video")

    # Importar função de posting do pipeline
    from shopee_pipeline import post_to_shopee_video

    for i, entry in enumerate(not_posted):
        video_path = entry.get("video_path", "")
        if not os.path.exists(video_path):
            log(f"  ⚠️ Vídeo não encontrado: {video_path}")
            continue

        # Usar descrição com link de afiliado próprio se disponível
        if entry.get("clean_description"):
            description = entry["clean_description"]
        else:
            text = entry.get("text", "")
            my_link = entry.get("my_affiliate_link", "")
            shopee_link = my_link or entry.get("shopee_link", "")
            hashtags = "#shopee #shopeehaul #shopeefinds #achadosshopee #review"

            desc_parts = []
            if text:
                first_line = text.split("\n")[0].split("https")[0][:80].strip()
                if first_line:
                    desc_parts.append(first_line)
            desc_parts.append(hashtags)
            if shopee_link:
                desc_parts.append(f"🔗 {shopee_link}")

            description = "\n".join(desc_parts)

        log(f"📤 [{i+1}/{len(not_posted)}] Postando: {os.path.basename(video_path)}")
        try:
            posted = await post_to_shopee_video(video_path, description)

            if posted:
                entry["posted_to_shopee"] = True
                entry["posted_at"] = datetime.now().isoformat()
                save_pending(pending)
                log(f"  ✅ Postado com sucesso!")
            else:
                log(f"  ❌ Falha ao postar")
        except Exception as e:
            log(f"  ❌ Erro: {e}")

        # Intervalo entre posts
        if i < len(not_posted) - 1:
            import random
            wait = random.randint(60, 180)
            log(f"  💤 Aguardando {wait}s...")
            await asyncio.sleep(wait)

    posted_count = sum(1 for p in pending if p.get("posted_to_shopee"))
    log(f"\n📊 Resumo: {posted_count}/{len(pending)} vídeos postados no Shopee")


async def auto_post_single(entry):
    """Posta um único vídeo automaticamente"""
    try:
        from shopee_pipeline import post_to_shopee_video

        video_path = entry.get("video_path", "")
        text = entry.get("text", "")
        shopee_link = entry.get("shopee_link", "")
        hashtags = "#shopee #shopeehaul #shopeefinds #achadosshopee"

        description = f"{text[:80]}\n{hashtags}"
        if shopee_link:
            description += f"\n🔗 {shopee_link}"

        log(f"[AUTO-POST] Postando: {os.path.basename(video_path)}")
        posted = await post_to_shopee_video(video_path, description)

        if posted:
            entry["posted_to_shopee"] = True
            entry["posted_at"] = datetime.now().isoformat()
            pending = load_pending()
            for p in pending:
                if p.get("msg_id") == entry.get("msg_id"):
                    p["posted_to_shopee"] = True
                    p["posted_at"] = entry["posted_at"]
            save_pending(pending)
            log(f"[AUTO-POST] ✅ OK!")
    except Exception as e:
        log(f"[AUTO-POST] ❌ {e}")


# === BOTH MODE ===

async def both_mode(config):
    """Monitor + Bot simultâneo"""
    client = await get_client(config)
    if not client:
        return

    await client.start(phone=config.get("phone", ""))
    me = await client.get_me()
    log(f"✅ Modo completo - Logado: {me.first_name}")

    channels = config.get("channels", [])
    channel_ids = [c["id"] if isinstance(c, dict) else c for c in channels]
    channel_names = {(c["id"] if isinstance(c, dict) else c): (c.get("name", "?") if isinstance(c, dict) else "?") for c in channels}

    pending = load_pending()
    downloaded_ids = {p.get("msg_id") for p in pending}
    filter_kw = config.get("filter_keywords", True)

    # Handler para canais monitorados
    if channel_ids:
        @client.on(events.NewMessage(chats=channel_ids))
        async def channel_handler(event):
            nonlocal pending, downloaded_ids
            msg = event.message

            if not msg.media or not isinstance(msg.media, MessageMediaDocument):
                return

            doc = msg.media.document
            if not doc or not doc.mime_type or 'video' not in doc.mime_type:
                return

            text = msg.text or msg.message or ""
            msg_id = f"{msg.chat_id}_{msg.id}"

            if msg_id in downloaded_ids:
                return

            if filter_kw and text and not any(kw.lower() in text.lower() for kw in KEYWORDS_SHOPEE):
                return

            video_hash = hashlib.md5(f"{msg_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:10]
            video_path = os.path.join(VIDEOS_DIR, f"tg_{video_hash}.mp4")

            chat_name = channel_names.get(msg.chat_id, str(msg.chat_id))
            log(f"📥 [{chat_name}] Novo vídeo: {text[:50]}")

            try:
                await client.download_media(msg, file=video_path)
                if os.path.exists(video_path) and os.path.getsize(video_path) > 10000:
                    size_mb = os.path.getsize(video_path) / (1024 * 1024)
                    entry = {
                        "msg_id": msg_id,
                        "channel": chat_name,
                        "channel_id": msg.chat_id,
                        "text": text[:500],
                        "shopee_link": extract_shopee_link(text),
                        "video_path": video_path,
                        "size_mb": round(size_mb, 2),
                        "downloaded_at": datetime.now().isoformat(),
                        "posted_to_shopee": False,
                    }
                    pending.append(entry)
                    downloaded_ids.add(msg_id)
                    save_pending(pending)
                    log(f"  ✅ {os.path.basename(video_path)} ({size_mb:.1f}MB)")

                    if config.get("auto_post"):
                        await auto_post_single(entry)
            except Exception as e:
                log(f"  ❌ {e}")

        log(f"👁️ Monitorando {len(channel_ids)} canais")

    # Handler para Saved Messages (manual)
    @client.on(events.NewMessage(from_users='me'))
    async def manual_handler(event):
        nonlocal pending, downloaded_ids
        msg = event.message

        if not msg.media or not isinstance(msg.media, MessageMediaDocument):
            return

        doc = msg.media.document
        if not doc or not doc.mime_type or 'video' not in doc.mime_type:
            return

        text = msg.text or msg.message or ""
        msg_id = f"saved_{msg.id}"

        if msg_id in downloaded_ids:
            return

        video_hash = hashlib.md5(f"{msg_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:10]
        video_path = os.path.join(VIDEOS_DIR, f"tg_manual_{video_hash}.mp4")

        log(f"📩 Vídeo manual recebido: {text[:50]}")
        try:
            await client.download_media(msg, file=video_path)
            if os.path.exists(video_path) and os.path.getsize(video_path) > 10000:
                size_mb = os.path.getsize(video_path) / (1024 * 1024)
                entry = {
                    "msg_id": msg_id,
                    "channel": "Manual",
                    "channel_id": "saved",
                    "text": text[:500],
                    "shopee_link": extract_shopee_link(text),
                    "video_path": video_path,
                    "size_mb": round(size_mb, 2),
                    "downloaded_at": datetime.now().isoformat(),
                    "posted_to_shopee": False,
                }
                pending.append(entry)
                downloaded_ids.add(msg_id)
                save_pending(pending)
                log(f"  ✅ {os.path.basename(video_path)} ({size_mb:.1f}MB)")
                await event.reply(f"✅ Salvo! {size_mb:.1f}MB")
        except Exception as e:
            log(f"  ❌ {e}")

    log("📩 Recebendo vídeos manuais via Saved Messages")
    log("🔄 Ctrl+C para parar\n")

    await client.run_until_disconnected()


# === STATUS ===

def show_status():
    """Mostra status dos vídeos"""
    pending = load_pending()
    total = len(pending)
    posted = sum(1 for p in pending if p.get("posted_to_shopee"))
    not_posted = total - posted

    print(f"\n📊 Status Telegram → Shopee")
    print(f"{'='*50}")
    print(f"  📥 Total baixados:     {total}")
    print(f"  ✅ Postados no Shopee: {posted}")
    print(f"  ⏳ Pendentes:          {not_posted}")

    if pending:
        print(f"\n  Últimos 5:")
        for p in pending[-5:]:
            status = "✅" if p.get("posted_to_shopee") else "⏳"
            print(f"  {status} {p.get('channel', '?')[:20]} | {os.path.basename(p.get('video_path', '?'))} | {p.get('size_mb', 0)}MB")

    # Config
    config = load_config()
    channels = config.get("channels", [])
    print(f"\n  📢 Canais monitorados: {len(channels)}")
    for c in channels:
        name = c.get("name", c) if isinstance(c, dict) else c
        print(f"    - {name}")
    print()


# === CLI ===

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telegram → Shopee Video Pipeline")
    parser.add_argument("--login", action="store_true", help="Login no Telegram (envia SMS)")
    parser.add_argument("--code", type=str, help="Código SMS recebido")
    parser.add_argument("--password", type=str, help="Senha 2FA (se tiver)")
    parser.add_argument("--monitor", action="store_true", help="Monitorar canais")
    parser.add_argument("--bot", action="store_true", help="Modo bot (recebe vídeos)")
    parser.add_argument("--both", action="store_true", help="Monitor + Bot")
    parser.add_argument("--list-channels", action="store_true", help="Listar canais")
    parser.add_argument("--add-channel", type=str, help="Adicionar canal (ID ou @username)")
    parser.add_argument("--post-pending", action="store_true", help="Postar pendentes no Shopee")
    parser.add_argument("--status", action="store_true", help="Status dos vídeos")
    parser.add_argument("--setup", action="store_true", help="Configuração inicial")
    args = parser.parse_args()

    config = load_config()

    if args.setup or (not config.get("api_id") and not args.status):
        print("\n🔧 Configuração do Telegram API")
        print("="*50)
        print("Acesse: https://my.telegram.org → API development tools\n")
        api_id = input("api_id: ").strip()
        api_hash = input("api_hash: ").strip()
        phone = input("Telefone (ex: +5511999999999): ").strip()
        config["api_id"] = api_id
        config["api_hash"] = api_hash
        config["phone"] = phone
        save_config(config)
        print(f"\n✅ Config salva em {CONFIG_FILE}")
        print("Agora rode: python3 telegram_shopee.py --login")

    elif args.login or args.code:
        asyncio.run(telegram_login(config, code=args.code))
    elif args.list_channels:
        asyncio.run(list_channels(config))
    elif args.add_channel:
        asyncio.run(add_channel(config, args.add_channel))
    elif args.monitor:
        asyncio.run(monitor_channels(config))
    elif args.bot:
        asyncio.run(bot_mode(config))
    elif args.both:
        asyncio.run(both_mode(config))
    elif args.post_pending:
        asyncio.run(post_pending_to_shopee())
    elif args.status:
        show_status()
    else:
        parser.print_help()
