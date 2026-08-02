import discord
from discord.ext import commands
from modules.preview import PreviewGenerator
from PIL import Image

import io
import re
import aiohttp

from modules.config import (
    DISCORD_TOKEN,
    MAX_HISTORY,
    TASARIM_KANALI,
    SOHBET_KANALLARI,
    TRUSTED_USER_IDS,
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
    TARGET_MEMORY_EXTRACTION_PROMPT,
    CASUAL_IMAGE_PROMPT,

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
        self.last_mentioned_user = {}

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

    def is_design_channel(self, message):
        """
        Sadece TASARIM_KANALI'nda katı thumbnail analiz sistemi
        (mod tespiti, puanlama, önizleme vb.) calisir. Diger her
        kanal (SOHBET_KANALLARI dahil, hatta listede olmayan bir
        kanal olsa bile) "sohbet" kanali sayilir ve gorsellere
        normal/dogal bir tepki verilir.
        """

        return message.channel.id == TASARIM_KANALI

    # --------------------------------------------------

    def clean_prompt(self, message):

        prompt = message.content

        if self.user in message.mentions:
            prompt = prompt.replace(
                self.user.mention,
                ""
            )

        # Duz yazilan "herbokolog" kelimesini de temizle -- yoksa bu
        # kelime modele giden metnin icinde kalip, model kendi adini
        # kullanicinin mesaji sanip kafasi karisiyor.
        prompt = re.sub(
            r"herbokolog",
            "",
            prompt,
            flags=re.IGNORECASE,
        )

        return prompt.strip()

    # --------------------------------------------------

    @staticmethod
    def _image_attachments(attachments):

        return [
            a for a in attachments
            if a.content_type and a.content_type.startswith("image")
        ]

    # --------------------------------------------------

    async def resolve_attachments(self, message):
        """
        Mesajin kendi ekleri varsa onlari kullanir. Yoksa, mesaj bir
        reply ise (gecmis bir gorsele @herbokolog yazarak cevap
        verilmisse) o orijinal mesajin eklerini bulup doner.
        """

        own = self._image_attachments(message.attachments)

        if own:
            return own

        if message.reference is None:
            return []

        replied = message.reference.resolved

        if replied is None or isinstance(replied, discord.DeletedReferencedMessage):

            try:
                replied = await message.channel.fetch_message(
                    message.reference.message_id
                )
            except (discord.NotFound, discord.HTTPException):
                return []

        return self._image_attachments(replied.attachments)

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

        # Mesajda BAŞKA kullanıcılar etiketlenmiş olabilir (botun
        # kendisi haric). Bunlari once okunakli isme cevirelim ki
        # model ham "<@id>" yerine gercek ismi gorsun, sonra o
        # kisi(ler)in KENDI profilini ayri ve net etiketli sekilde
        # modele verelim -- yoksa model, sadece elinde olan tek
        # profil bloğu (mesaji yazanin profili) kimden bahsediliyorsa
        # o sanip kisileri birbirine karistiriyor.
        mentioned_users = [
            u for u in message.mentions
            if u.id != self.user.id
        ]

        for u in mentioned_users:

            prompt = prompt.replace(
                u.mention,
                f"@{u.display_name}",
            )

            self.profile.ensure_user(
                u.id,
                u.name,
                u.display_name,
            )

        if mentioned_users:

            # Bu mesajda gercekten etiketlenen kisi(ler) varsa, kanal
            # icin "en son bahsedilen kisi" olarak kaydet -- boylece
            # bir sonraki takip mesajinda (yeni etiket olmasa bile)
            # kimden bahsedildigini hatirlayabiliriz.
            self.last_mentioned_user[message.channel.id] = mentioned_users

        # Hafiza YAZMA (kaydetme) icin hedef kisi listesi. Eger bu
        # mesajda kimse etiketlenmemisse ama GUVENILIR bir kullanici
        # konusuyorsa ve kanalda yakin zamanda birinden bahsedilmisse,
        # "hala o kisiden bahsediliyor" varsayimiyla o kisiyi hedef al.
        # Boylece "o bilgiyi X olarak guncelle" gibi yeniden etiket
        # icermeyen takip mesajlari da dogru kisiye kaydolur.
        extraction_targets = mentioned_users

        if (
            not extraction_targets
            and message.author.id in TRUSTED_USER_IDS
        ):
            extraction_targets = self.last_mentioned_user.get(
                message.channel.id,
                [],
            )

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

        # Mesajda baska kullanicilar hakkinda soylenen kalici bilgiler
        # varsa, bunlari ONLARIN kendi profiline kaydet -- boylece bot
        # sadece kendisiyle konusan kisiyi degil, hakkinda konusulan
        # herkesi de zamanla "taniyabilir".
        #
        # GUVENLIK: bu SADECE guvenilir kullanicilardan (TRUSTED_USER_IDS)
        # gelen mesajlarda calisir. Yoksa herhangi biri baskasi hakkinda
        # asilsiz/kotu niyetli bir "bilgi" soyleyip onu kalici hafizaya
        # yazdirabilir. Guvenilir olmayan biri baskasindan bahsettiginde
        # bot o mesaja o an normal cevap verir ama hicbir sey kaydetmez.
        if message.author.id in TRUSTED_USER_IDS:

            for u in extraction_targets:

                target_prompt = TARGET_MEMORY_EXTRACTION_PROMPT.replace(
                    "{target_name}",
                    u.display_name,
                )

                target_extracted = self.ai.extract_profile_info(
                    prompt,
                    target_prompt,
                )

                for interest in target_extracted["interests"]:
                    self.profile.add_interest(
                        u.id,
                        interest,
                    )

                for project in target_extracted["projects"]:
                    self.profile.add_project(
                        u.id,
                        project,
                    )

                for preference in target_extracted["preferences"]:
                    self.profile.add_preference(
                        u.id,
                        preference,
                    )

                for fact in target_extracted["facts"]:
                    self.profile.add_fact(
                        u.id,
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
                    "content": (
                        f"SANA YAZAN KİŞİNİN ({message.author.display_name}) "
                        "PROFİLİ:\n\n" + profile_prompt
                    ),
                }
            )

        # Etiketlenen kisi(ler)in KENDI profilini ayri sistem
        # mesaji olarak ekle, net sekilde kim oldugunu belirterek.
        for u in mentioned_users:

            mentioned_profile = self.profile.build_profile_prompt(
                u.id
            )

            if mentioned_profile:
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            f"MESAJDA BAHSEDİLEN/ETİKETLENEN KİŞİNİN "
                            f"({u.display_name}) PROFİLİ — bu SANA YAZAN "
                            f"kişiden FARKLI bir kişidir, karıştırma:\n\n"
                            + mentioned_profile
                        ),
                    }
                )

        if mentioned_users:

            names = ", ".join(
                u.display_name for u in mentioned_users
            )

            messages.append(
                {
                    "role": "system",
                    "content": (
                        f"ÖNEMLİ: Bu mesajda {names} adlı kullanıcı(lar) "
                        "etiketleniyor/bahsediliyor. Kullanıcı bu kişi(ler) "
                        "hakkında bir şey soruyorsa, cevabını SADECE bu "
                        "kişi(ler) hakkında ver. Sana yazan kişiyle "
                        "karıştırma, onlar farklı kişiler. Aşağıdaki "
                        "'Son konuşmalar' geçmişinde her satırın başındaki "
                        "isim o mesajı kimin yazdığını gösterir, ona göre "
                        "ayır."
                    ),
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

    async def generate_preview(self, message, attachments):

        if not attachments:
            await self.send_response(
                message,
                "❌ Lütfen bir thumbnail görseli gönder (ya da görselli bir mesaja "
                "cevap verip beni etiketle).",
            )
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(attachments[0].url) as resp:
                data = await resp.read()

        thumbnail = Image.open(io.BytesIO(data)).convert("RGB")

        generator = PreviewGenerator(
            thumbnail=thumbnail,
            title="Video Başlığı",
            channel=message.author.display_name,
            duration="12:48",
        )

        image = generator.render()

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        await message.reply(
            file=discord.File(
                buffer,
                filename="preview.png",
            ),
            mention_author=False,
        )

    # --------------------------------------------------

    async def process_image(self, message, attachments):

        if not attachments:

            await self.send_response(
                message,
                "❌ Lütfen en az bir resim gönder (ya da görselli bir mesaja "
                "cevap verip beni etiketle).",
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

    async def process_image_casual(self, message, attachments):
        """
        Tasarim odasi disindaki (sohbet) kanallarda gorsel atildiginda
        calisir. Thumbnail kriterleri/puanlama YOK -- bot sadece kendi
        normal kisiligiyle (BASE_PROMPT) gorsele dogal bir tepki verir.
        """

        user_text = self.clean_prompt(message)

        if not user_text:
            user_text = (
                "Biri sana bir görsel gönderdi. Discord'da bir "
                "arkadaşın tepki verir gibi, doğal ve kısa bir "
                "tepki ver. Teknik/tasarım analizi yapma, puan verme."
            )

        response = self.ai.analyze_image_with_context(
            attachments[0].url,
            CASUAL_IMAGE_PROMPT,
            user_text,
        )

        self.memory.add(
            message.channel.id,
            message.author.display_name,
            "[görsel gönderdi] " + user_text,
        )

        self.memory.add(
            message.channel.id,
            "Herbokolog",
            response,
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

                text = message.content.lower()

                # Ya mesajin kendi eki, ya da (ek yoksa) reply attigi
                # gecmis mesajin eki kullanilir.
                attachments = await self.resolve_attachments(message)

                design_channel = self.is_design_channel(message)

                if attachments:

                    if design_channel:

                        # Yeni/kullanilan gorseli hafizaya al ki sonraki
                        # "incele/geliştir" gibi takip mesajlarinda
                        # tekrar kullanilabilsin.
                        self.last_thumbnail[message.channel.id] = attachments

                        if (
                            "önizleme" in text
                            or "preview" in text
                            or "mockup" in text
                        ):
                            await self.generate_preview(message, attachments)

                        else:
                            await self.process_image(message, attachments)

                    else:

                        # Tasarim odasi disinda: katı analiz yok,
                        # botun normal kisiligiyle dogal bir tepki.
                        await self.process_image_casual(message, attachments)

                elif design_channel:

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
                            ],
                        )

                    else:

                        await self.process_text(message)

                else:

                    # Sohbet kanalinda ek yok -> normal sohbet.
                    await self.process_text(message)

            except Exception as e:

                await self.handle_error(
                    message,
                    e,
                )

bot = HerbokologBot()

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)