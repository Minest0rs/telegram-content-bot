"""Lightweight in-memory i18n.

Avoids gettext/.mo compile dance for now. Strings are defined per locale
in a Python dict; falls back to English then to the key itself.
"""

from __future__ import annotations

from typing import Any, cast

from src.core.config import Locale, settings

# fmt: off
_TRANSLATIONS: dict[Locale, dict[str, str]] = {
    "ru": {
        "start.greeting": (
            "Привет, {name}!\n\n"
            "Я ИИ-бот, который пишет посты для твоих Telegram-каналов.\n"
            "Я могу:\n"
            "• собирать новости из веба, RSS и других каналов\n"
            "• писать пост в стиле твоего канала\n"
            "• подбирать или генерировать картинку\n\n"
            "Нажми /menu чтобы начать."
        ),
        "menu.title": "Главное меню",
        "menu.generate": "✨ Создать пост",
        "menu.channels": "📢 Мои каналы",
        "menu.sources": "📰 Источники",
        "menu.style": "🎨 Стиль и промт",
        "menu.subscription": "💎 Подписка",
        "menu.language": "🌐 Язык",
        "menu.help": "❓ Помощь",
        "menu.cancel": "Отмена",
        "menu.back": "← Назад",
        "menu.next": "Далее →",
        "menu.skip": "Пропустить",
        "menu.confirm": "Подтвердить",

        "language.choose": "Выбери язык интерфейса:",
        "language.changed": "Язык изменён ✓",

        "subscription.tiers": (
            "Твой текущий тариф: <b>{current}</b>\n"
            "Постов в этом месяце: <b>{used}/{limit}</b>\n\n"
            "Доступные тарифы:\n\n"
            "🆓 <b>Free</b> — 3 поста/мес\n"
            "  • базовая модель, водяной знак, реклама бота\n\n"
            "⭐ <b>Pro</b> — 50 поста/мес — 100 ⭐\n"
            "  • генерация картинок, без рекламы бота\n\n"
            "💎 <b>Premium</b> — безлимит — 500 ⭐\n"
            "  • кастомный промт, анализ стиля канала, без водяного знака"
        ),
        "subscription.buy_pro": "Купить Pro (100 ⭐)",
        "subscription.buy_premium": "Купить Premium (500 ⭐)",
        "subscription.bought": "Спасибо! Тариф <b>{tier}</b> активирован до {until}.",

        "channels.empty": "У тебя пока нет привязанных каналов.\nНажми «Добавить канал».",
        "channels.add": "➕ Добавить канал",
        "channels.add_prompt": (
            "Перешли мне любое сообщение из канала, или отправь его @username.\n\n"
            "<b>Важно:</b> добавь меня в канал как админа с правами на публикацию и "
            "редактирование сообщений."
        ),
        "channels.added": "Канал <b>{title}</b> добавлен ✓",
        "channels.not_admin": (
            "Я не вижу прав администратора в этом канале. "
            "Добавь меня админом и попробуй ещё раз."
        ),
        "channels.list_title": "Твои каналы:",
        "channels.removed": "Канал удалён ✓",

        "sources.title": "Настрой откуда брать информацию:",
        "sources.web": "🔍 Веб-поиск",
        "sources.rss": "📡 RSS-ленты",
        "sources.telegram": "📨 Telegram-каналы",
        "sources.add_rss_prompt": "Пришли URL RSS-ленты:",
        "sources.add_tg_prompt": "Пришли @username канала или ссылку:",
        "sources.added": "Источник добавлен ✓",
        "sources.removed": "Источник удалён ✓",
        "sources.invalid_rss": "Не получилось прочитать эту RSS-ленту. Проверь URL.",

        "style.title": "Настройки стиля и промта",
        "style.system_prompt": "📝 Системный промт",
        "style.system_prompt_prompt": (
            "Опиши как ты хочешь, чтобы бот писал посты. Например:\n"
            "<i>«Пиши кратко, по делу, в дружеском тоне. Используй эмодзи и хештеги. "
            "Не больше 5 предложений.»</i>\n\n"
            "Текущий: <code>{current}</code>"
        ),
        "style.system_prompt_premium_only": (
            "Кастомный системный промт доступен только на тарифе Premium 💎"
        ),
        "style.style_analyze": "🎨 Анализ стиля канала",
        "style.style_analyze_premium_only": (
            "Анализ стиля канала доступен только на тарифе Premium 💎"
        ),
        "style.style_analyzed": (
            "Стиль канала проанализирован ✓\n"
            "Теперь бот будет писать в этой манере."
        ),
        "style.saved": "Сохранено ✓",

        "generate.choose_channel": "В какой канал публиковать?",
        "generate.choose_period": "За какой период собирать информацию?",
        "generate.period.hour": "Последний час",
        "generate.period.day": "Последние 24 часа",
        "generate.period.week": "Последняя неделя",
        "generate.period.month": "Последний месяц",
        "generate.topic_prompt": (
            "О чём писать пост?\n"
            "Можешь указать тему, ключевые слова, или нажать «Пропустить» — "
            "тогда бот возьмёт самое интересное из источников."
        ),
        "generate.no_topic": "—",
        "generate.working": "🔄 Собираю информацию и пишу пост...",
        "generate.collecting": "🔎 Ищу актуальную инфу...",
        "generate.writing": "✍️ Пишу пост...",
        "generate.image": "🎨 Подбираю картинку...",
        "generate.preview_caption": "Вот что получилось. Опубликовать?",
        "generate.publish": "📤 Опубликовать",
        "generate.regenerate": "🔄 Перегенерить",
        "generate.cancel": "❌ Отмена",
        "generate.published": "Пост опубликован ✓",
        "generate.no_sources": (
            "У тебя нет настроенных источников. "
            "Добавь хотя бы один в /menu → Источники."
        ),
        "generate.limit_reached": (
            "Ты исчерпал лимит постов на тарифе <b>{tier}</b> ({limit}/мес). "
            "Обнови тариф через /menu → Подписка."
        ),
        "generate.failed": "Что-то пошло не так: {error}",

        "publish.mode_title": "Режим публикации:",
        "publish.mode_auto": "🤖 Авто (сразу в канал)",
        "publish.mode_preview": "👀 Превью (с подтверждением)",
        "publish.mode_set": "Режим публикации обновлён ✓",

        "watermark.signature": "🤖 Сгенерировано через @{bot_username}",

        "promo.in_channel": (
            "Этот канал ведёт ИИ-бот <b>@{bot_username}</b>.\n"
            "Хочешь так же — пиши: https://t.me/{bot_username}"
        ),

        "errors.generic": "Ой, что-то сломалось. Попробуй ещё раз.",
        "errors.not_admin": "Сделай меня админом канала, иначе я не смогу постить.",
    },
    "en": {
        "start.greeting": (
            "Hi, {name}!\n\n"
            "I'm an AI bot that writes posts for your Telegram channels.\n"
            "I can:\n"
            "• collect news from web, RSS, and other channels\n"
            "• write a post in your channel's style\n"
            "• find or generate an image\n\n"
            "Hit /menu to begin."
        ),
        "menu.title": "Main menu",
        "menu.generate": "✨ Create post",
        "menu.channels": "📢 My channels",
        "menu.sources": "📰 Sources",
        "menu.style": "🎨 Style & prompt",
        "menu.subscription": "💎 Subscription",
        "menu.language": "🌐 Language",
        "menu.help": "❓ Help",
        "menu.cancel": "Cancel",
        "menu.back": "← Back",
        "menu.next": "Next →",
        "menu.skip": "Skip",
        "menu.confirm": "Confirm",

        "language.choose": "Choose interface language:",
        "language.changed": "Language updated ✓",

        "subscription.tiers": (
            "Your current tier: <b>{current}</b>\n"
            "Posts this month: <b>{used}/{limit}</b>\n\n"
            "Available tiers:\n\n"
            "🆓 <b>Free</b> — 3 posts/mo\n"
            "  • basic model, watermark, bot promo\n\n"
            "⭐ <b>Pro</b> — 50 posts/mo — 100 ⭐\n"
            "  • image generation, no bot promo\n\n"
            "💎 <b>Premium</b> — unlimited — 500 ⭐\n"
            "  • custom prompt, channel style analysis, no watermark"
        ),
        "subscription.buy_pro": "Buy Pro (100 ⭐)",
        "subscription.buy_premium": "Buy Premium (500 ⭐)",
        "subscription.bought": "Thanks! <b>{tier}</b> tier active until {until}.",

        "channels.empty": "No channels yet.\nTap «Add channel».",
        "channels.add": "➕ Add channel",
        "channels.add_prompt": (
            "Forward me any message from the channel, or send its @username.\n\n"
            "<b>Important:</b> add me as admin with rights to post and edit messages."
        ),
        "channels.added": "Channel <b>{title}</b> added ✓",
        "channels.not_admin": (
            "I don't see admin rights in that channel. "
            "Add me as admin and try again."
        ),
        "channels.list_title": "Your channels:",
        "channels.removed": "Channel removed ✓",

        "sources.title": "Configure where to pull info from:",
        "sources.web": "🔍 Web search",
        "sources.rss": "📡 RSS feeds",
        "sources.telegram": "📨 Telegram channels",
        "sources.add_rss_prompt": "Send the RSS feed URL:",
        "sources.add_tg_prompt": "Send the channel's @username or link:",
        "sources.added": "Source added ✓",
        "sources.removed": "Source removed ✓",
        "sources.invalid_rss": "Can't read this RSS feed. Check the URL.",

        "style.title": "Style & prompt settings",
        "style.system_prompt": "📝 System prompt",
        "style.system_prompt_prompt": (
            "Describe how you want the bot to write. Example:\n"
            "<i>«Be concise, friendly. Use emoji and hashtags. Max 5 sentences.»</i>\n\n"
            "Current: <code>{current}</code>"
        ),
        "style.system_prompt_premium_only": (
            "Custom system prompt is Premium-only 💎"
        ),
        "style.style_analyze": "🎨 Analyze channel style",
        "style.style_analyze_premium_only": (
            "Channel style analysis is Premium-only 💎"
        ),
        "style.style_analyzed": (
            "Channel style analyzed ✓\n"
            "The bot will now write in this manner."
        ),
        "style.saved": "Saved ✓",

        "generate.choose_channel": "Which channel to publish to?",
        "generate.choose_period": "What time period to pull info from?",
        "generate.period.hour": "Last hour",
        "generate.period.day": "Last 24 hours",
        "generate.period.week": "Last week",
        "generate.period.month": "Last month",
        "generate.topic_prompt": (
            "What's the post about?\n"
            "Specify a topic or keywords, or skip — the bot will pick the best of the sources."
        ),
        "generate.no_topic": "—",
        "generate.working": "🔄 Collecting info and writing the post...",
        "generate.collecting": "🔎 Fetching info...",
        "generate.writing": "✍️ Writing the post...",
        "generate.image": "🎨 Choosing an image...",
        "generate.preview_caption": "Here's the draft. Publish?",
        "generate.publish": "📤 Publish",
        "generate.regenerate": "🔄 Regenerate",
        "generate.cancel": "❌ Cancel",
        "generate.published": "Post published ✓",
        "generate.no_sources": (
            "You have no sources configured. "
            "Add at least one in /menu → Sources."
        ),
        "generate.limit_reached": (
            "You've hit your monthly limit on the <b>{tier}</b> tier ({limit}/mo). "
            "Upgrade via /menu → Subscription."
        ),
        "generate.failed": "Something went wrong: {error}",

        "publish.mode_title": "Publishing mode:",
        "publish.mode_auto": "🤖 Auto (publish immediately)",
        "publish.mode_preview": "👀 Preview (with confirmation)",
        "publish.mode_set": "Publishing mode updated ✓",

        "watermark.signature": "🤖 Generated via @{bot_username}",

        "promo.in_channel": (
            "This channel is run by AI bot <b>@{bot_username}</b>.\n"
            "Want the same? https://t.me/{bot_username}"
        ),

        "errors.generic": "Something broke. Try again.",
        "errors.not_admin": "Make me a channel admin, otherwise I can't post.",
    },
    "es": {
        "start.greeting": (
            "¡Hola, {name}!\n\n"
            "Soy un bot de IA que escribe publicaciones para tus canales de Telegram.\n"
            "Puedo:\n"
            "• recopilar noticias de la web, RSS y otros canales\n"
            "• escribir en el estilo de tu canal\n"
            "• buscar o generar una imagen\n\n"
            "Pulsa /menu para empezar."
        ),
        "menu.title": "Menú principal",
        "menu.generate": "✨ Crear publicación",
        "menu.channels": "📢 Mis canales",
        "menu.sources": "📰 Fuentes",
        "menu.style": "🎨 Estilo y prompt",
        "menu.subscription": "💎 Suscripción",
        "menu.language": "🌐 Idioma",
        "menu.help": "❓ Ayuda",
        "menu.cancel": "Cancelar",
        "menu.back": "← Volver",
        "menu.next": "Siguiente →",
        "menu.skip": "Saltar",
        "menu.confirm": "Confirmar",

        "language.choose": "Elige el idioma de la interfaz:",
        "language.changed": "Idioma actualizado ✓",

        "subscription.tiers": (
            "Tu plan actual: <b>{current}</b>\n"
            "Publicaciones este mes: <b>{used}/{limit}</b>\n\n"
            "Planes disponibles:\n\n"
            "🆓 <b>Free</b> — 3 publicaciones/mes\n"
            "  • modelo básica, marca de agua, anuncio del bot\n\n"
            "⭐ <b>Pro</b> — 50 publicaciones/mes — 100 ⭐\n"
            "  • generación de imágenes, sin anuncio del bot\n\n"
            "💎 <b>Premium</b> — ilimitado — 500 ⭐\n"
            "  • prompt personalizado, análisis de estilo, sin marca de agua"
        ),
        "subscription.buy_pro": "Comprar Pro (100 ⭐)",
        "subscription.buy_premium": "Comprar Premium (500 ⭐)",
        "subscription.bought": "¡Gracias! Plan <b>{tier}</b> activo hasta {until}.",

        "channels.empty": "Aún no tienes canales.\nPulsa «Añadir canal».",
        "channels.add": "➕ Añadir canal",
        "channels.add_prompt": (
            "Reenvía cualquier mensaje del canal, o envía su @username.\n\n"
            "<b>Importante:</b> añádeme como admin con permisos para publicar y editar."
        ),
        "channels.added": "Canal <b>{title}</b> añadido ✓",
        "channels.not_admin": (
            "No veo permisos de administrador en ese canal. "
            "Añádeme como admin y vuelve a intentarlo."
        ),
        "channels.list_title": "Tus canales:",
        "channels.removed": "Canal eliminado ✓",

        "sources.title": "Configura de dónde sacar la información:",
        "sources.web": "🔍 Búsqueda web",
        "sources.rss": "📡 Feeds RSS",
        "sources.telegram": "📨 Canales de Telegram",
        "sources.add_rss_prompt": "Envía la URL del feed RSS:",
        "sources.add_tg_prompt": "Envía el @username o el enlace del canal:",
        "sources.added": "Fuente añadida ✓",
        "sources.removed": "Fuente eliminada ✓",
        "sources.invalid_rss": "No puedo leer este feed RSS. Comprueba la URL.",

        "style.title": "Configuración de estilo y prompt",
        "style.system_prompt": "📝 Prompt del sistema",
        "style.system_prompt_prompt": (
            "Describe cómo quieres que el bot escriba. Ejemplo:\n"
            "<i>«Sé conciso, amistoso. Usa emojis y hashtags. Máximo 5 frases.»</i>\n\n"
            "Actual: <code>{current}</code>"
        ),
        "style.system_prompt_premium_only": (
            "El prompt personalizado es solo Premium 💎"
        ),
        "style.style_analyze": "🎨 Analizar estilo del canal",
        "style.style_analyze_premium_only": (
            "El análisis de estilo es solo Premium 💎"
        ),
        "style.style_analyzed": (
            "Estilo del canal analizado ✓\n"
            "El bot ahora escribirá en este tono."
        ),
        "style.saved": "Guardado ✓",

        "generate.choose_channel": "¿En qué canal publicar?",
        "generate.choose_period": "¿De qué periodo recopilar información?",
        "generate.period.hour": "Última hora",
        "generate.period.day": "Últimas 24 horas",
        "generate.period.week": "Última semana",
        "generate.period.month": "Último mes",
        "generate.topic_prompt": (
            "¿Sobre qué quieres la publicación?\n"
            "Indica un tema o palabras clave, o salta — el bot tomará lo mejor de las fuentes."
        ),
        "generate.no_topic": "—",
        "generate.working": "🔄 Recopilando información y redactando...",
        "generate.collecting": "🔎 Buscando información...",
        "generate.writing": "✍️ Redactando...",
        "generate.image": "🎨 Eligiendo imagen...",
        "generate.preview_caption": "Aquí está el borrador. ¿Publicar?",
        "generate.publish": "📤 Publicar",
        "generate.regenerate": "🔄 Regenerar",
        "generate.cancel": "❌ Cancelar",
        "generate.published": "Publicación enviada ✓",
        "generate.no_sources": (
            "No tienes fuentes configuradas. "
            "Añade al menos una en /menu → Fuentes."
        ),
        "generate.limit_reached": (
            "Has alcanzado tu límite mensual del plan <b>{tier}</b> ({limit}/mes). "
            "Mejora el plan en /menu → Suscripción."
        ),
        "generate.failed": "Algo falló: {error}",

        "publish.mode_title": "Modo de publicación:",
        "publish.mode_auto": "🤖 Auto (publicar al instante)",
        "publish.mode_preview": "👀 Vista previa (con confirmación)",
        "publish.mode_set": "Modo de publicación actualizado ✓",

        "watermark.signature": "🤖 Generado por @{bot_username}",

        "promo.in_channel": (
            "Este canal está gestionado por el bot de IA <b>@{bot_username}</b>.\n"
            "¿Quieres lo mismo? https://t.me/{bot_username}"
        ),

        "errors.generic": "Algo se rompió. Inténtalo de nuevo.",
        "errors.not_admin": "Hazme admin del canal, si no, no puedo publicar.",
    },
}
# fmt: on


class I18n:
    """Tiny i18n helper.

    Usage: ``i18n.t("menu.title", locale="ru")`` or ``i18n.t("menu.title", locale="ru", name="John")``.
    """

    def __init__(self, default_locale: Locale = "ru") -> None:
        self.default_locale: Locale = default_locale

    def t(self, key: str, *, locale: str | None = None, **kwargs: Any) -> str:
        loc: Locale = cast(Locale, locale) if locale in _TRANSLATIONS else self.default_locale
        bundle = _TRANSLATIONS.get(loc) or _TRANSLATIONS["en"]
        text = bundle.get(key)
        if text is None:
            text = _TRANSLATIONS["en"].get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text

    @staticmethod
    def supported() -> list[Locale]:
        return cast(list[Locale], list(_TRANSLATIONS.keys()))


i18n = I18n(default_locale=settings.default_locale)
