from __future__ import annotations

import asyncio

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .fantacalcio import FantacalcioClient, extract_trunk_players
from .storage import Storage


class PremioTronchiBot:
    def __init__(self, token: str, storage: Storage, fantacalcio_client: FantacalcioClient) -> None:
        self._storage = storage
        self._fantacalcio = fantacalcio_client
        self._application = Application.builder().token(token).build()

        self._application.add_handler(CommandHandler("start", self.start))
        self._application.add_handler(CommandHandler("aggiorna", self.aggiorna))
        self._application.add_handler(CommandHandler("classifica", self.classifica))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        if update.message is None:
            return

        await update.message.reply_text(
            "Bot attivo. Comandi disponibili:\n"
            "/aggiorna - inizializza/aggiorna la classifica fino all'ultima giornata disponibile\n"
            "/classifica - mostra la classifica tronchi"
        )

    async def aggiorna(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        if update.message is None:
            return

        try:
            sheets = self._fantacalcio.download_available_votes_sheets()
            new_sheets = [s for s in sheets if not self._storage.is_source_processed(s.source_id)]
            if not new_sheets:
                await update.message.reply_text(
                    "La classifica e' gia' aggiornata all'ultima giornata disponibile."
                )
                return

            updated_count = 0
            for sheet in new_sheets:
                players = extract_trunk_players(sheet.raw_bytes)
                updated_count += self._storage.apply_penalties(players, source_id=sheet.source_id)

            latest_source = new_sheets[-1].source_url
            await update.message.reply_text(
                "Aggiornamento completato. "
                f"Giornate elaborate: {len(new_sheets)}. "
                f"Nuovi tronchi registrati: {updated_count}.\n"
                f"Ultima sorgente: {latest_source}"
            )
        except Exception as exc:
            await update.message.reply_text(f"Errore durante l'aggiornamento: {exc}")

    async def classifica(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        if update.message is None:
            return

        ranking = self._storage.get_ranking(limit=30)
        if not ranking:
            await update.message.reply_text(
                "Classifica vuota. Esegui /aggiorna dopo una giornata per popolarla."
            )
            return

        lines = ["La classifica aggiornata per il tronco dell’anno é:\n"]
        for idx, row in enumerate(ranking, start=1):
            lines.append(f"{idx}. {row.player_name} - {row.score}")
        
        lines.append(
            "\nRicordiamo a tutti la definizione di tronco: \"Dicasi tronco la punta di una squadra di serie A, idealmente grossa e limitata nei movimenti, la cui caratteristica principale è la finalizzazione. Se questa non avviene, la presenza del tronco su un campo da calcio ha un’utilità modesta, se non dannosa.\"\n\n"
            "La commissione tronchi si riserva di aggiungere eventuali nuovi tronchi, la cui legnosità si distingua nel corso della stagione.\n"
            "\nCordialmente, \nOsservatorio tronchi Serie A"
        )

        await update.message.reply_text("\n".join(lines))

    def run_polling(self) -> None:
        # Python 3.14 no longer provides an implicit default loop in main thread.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self._application.run_polling(allowed_updates=Update.ALL_TYPES)
        finally:
            loop.close()

    def run_webhook(self, webhook_url: str, port: int) -> None:
        # Python 3.14 no longer provides an implicit default loop in main thread.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self._application.run_webhook(
                listen="0.0.0.0",
                port=port,
                webhook_url=webhook_url,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )
        finally:
            loop.close()
