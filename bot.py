import discord
from discord.ext import commands

from modules.config import (
    DISCORD_TOKEN,
    MAX_HISTORY,
)

from modules.memory import MemoryManager
from modules.profile import ProfileManager
from modules.thumbnail import (
    ThumbnailManager,
    ThumbnailMode,
)

from modules.ai import AIClient
from modules.openrouter_manager import AllKeysExhaustedError

from modules.prompts import (
    BASE_PROMPT,
    MEMORY_EXTRACTION_PROMPT,

)


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True


class HerbokologBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
        )

        self.memory = MemoryManager(MAX_HISTORY)
        self.profile = ProfileManager()
        self.thumbnail = ThumbnailManager()
        self.ai = AIClient()
        self.last_thumbnail = {}

    async def setup_hook(self):
        print("Herbokolog hazırlanıyor...")

    async def on_ready(self):
        print("-" * 40)
        print(f"Giriş yapıldı: {self.user}")
        print(f"Sunucu sayısı: {len(self.guilds)}")
        print("Uzun dönem hafıza aktif.")
        print("Thumbnail sistemi aktif.")
        print("-" * 40)

    # --------------------------------------------------

    def is_called(self, message):

        content = message.content.lower()

        mentioned = self.user in message.mentions
        called = "herbokolog" in content

        return mentioned or called

    # --------------------------------------------------

    def clean_prompt(self, message):

        prompt = message.content

        if self.user in message.mentions:
            prompt = prompt.replace(
                self.user.mention,
                ""
            )

        return prompt.strip()

    # --------------------------------------------------

    async def process_text(self, message):

        prompt = self.clean_prompt(message)

        user_id = message.author.id

        self.profile.ensure_user(
            user_id,
            message.author.name,
            message.author.display_name,
        )

        self.profile.update_last_seen(user_id)

        self.memory.add(
            message.channel.id,
            message.author.display_name,
            prompt,
        )

        extracted = self.ai.extract_profile_info(
            prompt,
            MEMORY_EXTRACTION_PROMPT,
        )

        for interest in extracted["interests"]:
            self.profile.add_interest(
                user_id,
                interest,
            )

        for project in extracted["projects"]:
            self.profile.add_project(
                user_id,
                project,
            )

        for preference in extracted["preferences"]:
            self.profile.add_preference(
                user_id,
                preference,
            )

        for fact in extracted["facts"]:
            self.profile.add_fact(
                user_id,
                fact,
            )

        history = self.memory.history_text(
            message.channel.id
        )

        profile_prompt = self.profile.build_profile_prompt(
            user_id
        )

        messages = [
            {
                "role": "system",
                "content": BASE_PROMPT,
            }
        ]

        if profile_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": profile_prompt,
                }
            )

        if history:
            messages.append(
                {
                    "role": "system",
                    "content": "Son konuşmalar:\n" + history,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        response = self.ai.chat(messages)

        self.memory.add(
            message.channel.id,
            "Herbokolog",
            response,
        )

        self.profile.add_history(
            user_id,
            "user",
            prompt,
        )

        self.profile.add_history(
            user_id,
            "assistant",
            response,
        )

        await self.send_response(
            message,
            response,
        )
    # --------------------------------------------------

    async def process_image(self, message, attachments=None):
        
        if attachments is None:
            attachments = [
                a for a in message.attachments
                if a.content_type and a.content_type.startswith("image")
            ]

            # Sadece yeni yüklenen resimleri kaydet
            self.last_thumbnail[message.channel.id] = attachments
        if not attachments:

            await self.send_response(
                message,
                "❌ Lütfen en az bir resim gönder.",
            )
            return

        mode = self.thumbnail.detect_mode(message)
        prompt = self.thumbnail.get_prompt(mode)

        # İki görsel karşılaştırma
        if mode == ThumbnailMode.COMPARE:

            if len(attachments) < 2:

                await self.send_response(
                    message,
                    "❌ Karşılaştırma yapmak için 2 görsel göndermelisin.",
                )
                return

            response = self.ai.compare_images(
                attachments[0].url,
                attachments[1].url,
                prompt,
            )

        # Tek görsel analizi
        else:

            response = self.ai.analyze_image_url(
                attachments[0].url,
                prompt,
            )

        await self.send_response(
            message,
            response,
        )
    # --------------------------------------------------

    async def send_response(
        self,
        message,
        response,
    ):

        await message.reply(
            response,
            mention_author=False,
        )

    # --------------------------------------------------

    async def handle_error(
        self,
        message,
        error,
    ):

        await message.reply(
            f"❌ Bir hata oluştu.\n```{error}```",
            mention_author=False,
        )

    # --------------------------------------------------

    async def on_message(self, message):

        if message.author.bot:
            return

        if not self.is_called(message):
            return

        async with message.channel.typing():

            try:

                if message.attachments:

                    await self.process_image(message)

                else:

                    text = message.content.lower()

                    thumbnail_keywords = [
                        "incele",
                        "geliştir",
                        "iyileştir",
                        "ctr",
                        "başlık",
                        "title",
                        "renk",
                        "font",
                        "yazı",
                        "efekt",
                        "karşılaştır",
                        "compare",
                    ]

                    if (
                        any(keyword in text for keyword in thumbnail_keywords)
                        and message.channel.id in self.last_thumbnail
                    ):
                

                        await self.process_image(
                            message,
                            attachments=self.last_thumbnail[
                                message.channel.id
                            ]
                        )

                    else:

                        await self.process_text(message)

            except Exception as e:

                await self.handle_error(
                    message,
                    e,
                )
                
bot = HerbokologBot()

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)