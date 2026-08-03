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
from modules.logger import logger

from modules.prompts import (
    BASE_PROMPT,
    MEMORY_EXTRACTION_PROMPT,
    TARGET_MEMORY_EXTRACTION_PROMPT,
    CASUAL_IMAGE_PROMPT,

)


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True


CATEGORY_ALIASES = {
    "facts": "facts",
    "fact": "facts",
    "bilgi": "facts",
    "bilgiler": "facts",
    "projects": "projects",
    "project": "projects",
    "proje": "projects",
    "projeler": "projects",
    "interests": "interests",
    "interest": "interests",
    "ilgi": "interests",
    "ilgialani": "interests",
    "ilgialanlari": "interests",
    "preferences": "preferences",
    "preference": "preferences",
    "tercih": "preferences",
    "tercihler": "preferences",
}

CATEGORY_LABELS = {
    "interests": "İlgi Alanları",
    "projects": "Projeler",
    "preferences": "Tercihler",
    "facts": "Bilinen Bilgiler",
}


def build_profile_pages(profile):
    """
    get_profile_detailed() ciktisindan, her satiri gercek DB id'siyle
    birlikte gosteren, sayfalara bolunmus metin listesi uretir. Her
    sayfa Discord'un 2000 karakter sinirinin altinda kalacak sekilde
    bolunur.
    """

    header_lines = [
        f"**Kullanıcı ID:** {profile['user_id']}",
        f"**Username:** {profile['username']}",
        f"**Display name:** {profile['display_name']}",
        f"**Son görülme:** {profile['last_seen']}",
        "",
    ]

    body_lines = []

    has_any = False

    for category in ("interests", "projects", "preferences", "facts"):

        entries = profile[category]

        if not entries:
            continue

        has_any = True

        body_lines.append(f"**{CATEGORY_LABELS[category]}:**")

        for row_id, value in entries:
            body_lines.append(f"`[{row_id}]` {value}")

        body_lines.append("")

    if not has_any:
        body_lines.append(
            "_Hiçbir interest/project/preference/fact kaydı yok._"
        )

    pages = []

    current = list(header_lines)
    current_len = sum(len(l) + 1 for l in current)

    for line in body_lines:

        line_len = len(line) + 1

        if current_len + line_len > 1800 and len(current) > len(header_lines):

            pages.append("\n".join(current))
            current = list(header_lines)
            current_len = sum(len(l) + 1 for l in current)

        current.append(line)
        current_len += line_len

    pages.append("\n".join(current))

    return pages


class EditEntryModal(discord.ui.Modal):
    """
    'Düzenle' butonuna basinca acilan form -- secili kaydin metnini
    duzenlemek icin bir metin kutusu gosterir.
    """

    def __init__(self, view, category, row_id, current_value):

        super().__init__(title=f"Kaydı Düzenle [{row_id}]")

        self.view_ref = view
        self.category = category
        self.row_id = row_id

        self.value_input = discord.ui.TextInput(
            label="Yeni metin",
            style=discord.TextStyle.paragraph,
            default=current_value[:4000],
            max_length=500,
        )

        self.add_item(self.value_input)

    async def on_submit(self, interaction: discord.Interaction):

        if interaction.user.id not in TRUSTED_USER_IDS:
            await interaction.response.send_message(
                "❌ Bu paneli sadece güvenilir kullanıcılar kullanabilir.",
                ephemeral=True,
            )
            return

        self.view_ref.profile.update_entry(
            self.category,
            self.row_id,
            self.view_ref.user_id,
            str(self.value_input.value),
        )

        await self.view_ref.refresh()

        await interaction.response.send_message(
            "✅ Güncellendi.",
            ephemeral=True,
        )


class AddEntryModal(discord.ui.Modal):
    """
    'Ekle' butonuna basinca acilan form -- yeni kategori + metin
    girisi icin iki alan gosterir.
    """

    def __init__(self, view):

        super().__init__(title="Yeni Kayıt Ekle")

        self.view_ref = view

        self.category_input = discord.ui.TextInput(
            label="Kategori",
            placeholder="facts / projects / interests / preferences",
            max_length=30,
        )

        self.value_input = discord.ui.TextInput(
            label="Metin",
            style=discord.TextStyle.paragraph,
            max_length=500,
        )

        self.add_item(self.category_input)
        self.add_item(self.value_input)

    async def on_submit(self, interaction: discord.Interaction):

        if interaction.user.id not in TRUSTED_USER_IDS:
            await interaction.response.send_message(
                "❌ Bu paneli sadece güvenilir kullanıcılar kullanabilir.",
                ephemeral=True,
            )
            return

        category = CATEGORY_ALIASES.get(
            str(self.category_input.value).strip().lower()
        )

        if category is None:
            await interaction.response.send_message(
                "❌ Geçersiz kategori. facts/projects/interests/"
                "preferences (ya da bilgi/proje/ilgi/tercih) kullan.",
                ephemeral=True,
            )
            return

        self.view_ref.profile.ensure_user(
            self.view_ref.user_id,
            str(self.view_ref.user_id),
            str(self.view_ref.user_id),
        )

        self.view_ref.profile.add_entry(
            category,
            self.view_ref.user_id,
            str(self.value_input.value),
        )

        await self.view_ref.refresh()

        await interaction.response.send_message(
            "✅ Eklendi.",
            ephemeral=True,
        )


class ProfileManagementView(discord.ui.View):
    """
    'bilgi <id>' ciktisina eklenen interaktif yonetim paneli:
    - Dropdown ile bir kayit sec
    - Duzenle / Sil / Ekle butonlari
    - Duzenleme ve ekleme gercek Discord formlariyla (modal) yapilir

    Discord'un Select bileseni en fazla 25 secenek destekler, o
    yuzden ilk 25 kayit gosterilir -- cok daha fazla kaydi olan bir
    kullanici icin metin komutlariyla (sil/ekle/duzenle) devam
    edilebilir.
    """

    def __init__(self, profile_manager, user_id, timeout=300):

        super().__init__(timeout=timeout)

        self.profile = profile_manager
        self.user_id = user_id
        self.message = None
        self.selected = None

        self._build_select()
        self._sync_button_states()

    # --------------------------------------------------

    def _flatten_entries(self):

        detailed = self.profile.get_profile_detailed(self.user_id)

        entries = []

        if detailed:
            for category in ("interests", "projects", "preferences", "facts"):
                for row_id, value in detailed[category]:
                    entries.append((category, row_id, value))

        return entries

    # --------------------------------------------------

    def _build_select(self):

        for item in list(self.children):
            if isinstance(item, discord.ui.Select):
                self.remove_item(item)

        entries = self._flatten_entries()[:25]

        options = [
            discord.SelectOption(
                label=f"[{row_id}] {CATEGORY_LABELS[category]}"[:100],
                description=value[:100],
                value=f"{category}:{row_id}",
            )
            for category, row_id, value in entries
        ]

        if not options:
            options = [discord.SelectOption(label="Kayıt yok", value="none")]

        select = discord.ui.Select(
            placeholder="Düzenlemek/silmek için bir kayıt seç...",
            options=options,
            disabled=not entries,
            row=0,
        )

        async def on_select(interaction: discord.Interaction):

            if not await self._check_authorized(interaction):
                return

            value = select.values[0]

            if value == "none":
                await interaction.response.defer()
                return

            category, row_id = value.split(":", 1)

            self.selected = (category, int(row_id))

            self._sync_button_states()

            await interaction.response.edit_message(view=self)

        select.callback = on_select

        self.add_item(select)

    # --------------------------------------------------

    async def _check_authorized(self, interaction: discord.Interaction) -> bool:
        """
        Bu paneldeki HERHANGI bir bilesene (dropdown, buton) sadece
        guvenilir kullanicilar tiklayabilir -- mesaji kimin gonderdigi
        onemli degil, mesaji goren HERKES aslinda etkilesime
        girebilir, bu yuzden her tikta ayrica kontrol ediyoruz.
        """

        if interaction.user.id in TRUSTED_USER_IDS:
            return True

        await interaction.response.send_message(
            "❌ Bu paneli sadece güvenilir kullanıcılar kullanabilir.",
            ephemeral=True,
        )

        return False

    # --------------------------------------------------

    def _sync_button_states(self):

        has_selection = self.selected is not None

        self.edit_button.disabled = not has_selection
        self.delete_button.disabled = not has_selection

    # --------------------------------------------------

    async def refresh(self):

        self.selected = None

        self._build_select()
        self._sync_button_states()

        if self.message:

            profile = self.profile.get_profile_detailed(self.user_id)

            content = build_profile_pages(profile)[0]

            await self.message.edit(content=content, view=self)

    # --------------------------------------------------

    @discord.ui.button(
        label="✏️ Düzenle",
        style=discord.ButtonStyle.primary,
        row=1,
    )
    async def edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not await self._check_authorized(interaction):
            return

        if not self.selected:
            await interaction.response.send_message(
                "Önce dropdown'dan bir kayıt seç.",
                ephemeral=True,
            )
            return

        category, row_id = self.selected

        entries = self._flatten_entries()

        current = next(
            (v for c, r, v in entries if c == category and r == row_id),
            "",
        )

        await interaction.response.send_modal(
            EditEntryModal(self, category, row_id, current)
        )

    # --------------------------------------------------

    @discord.ui.button(
        label="🗑️ Sil",
        style=discord.ButtonStyle.danger,
        row=1,
    )
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not await self._check_authorized(interaction):
            return

        if not self.selected:
            await interaction.response.send_message(
                "Önce dropdown'dan bir kayıt seç.",
                ephemeral=True,
            )
            return

        category, row_id = self.selected

        self.profile.delete_entry(category, row_id, self.user_id)

        await self.refresh()

        await interaction.response.send_message(
            "✅ Silindi.",
            ephemeral=True,
        )

    # --------------------------------------------------

    @discord.ui.button(
        label="➕ Ekle",
        style=discord.ButtonStyle.success,
        row=1,
    )
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not await self._check_authorized(interaction):
            return

        await interaction.response.send_modal(AddEntryModal(self))

    # --------------------------------------------------

    async def on_timeout(self):

        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


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

        logger.debug(
            "process_text: author=%s (trusted=%s) mentioned=%s "
            "extraction_targets=%s",
            message.author.display_name,
            message.author.id in TRUSTED_USER_IDS,
            [u.display_name for u in mentioned_users],
            [u.display_name for u in extraction_targets],
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

                logger.info(
                    "target extraction (%s) -> %s",
                    u.display_name,
                    target_extracted,
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

            logger.debug(
                "profile lookup (%s, id=%s) -> %s",
                u.display_name,
                u.id,
                "bulundu" if mentioned_profile else "BOS/yok",
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

    def resolve_category(self, raw):

        return CATEGORY_ALIASES.get(raw.strip().lower())

    # --------------------------------------------------

    def parse_info_command(self, message):
        """
        "@herbokolog bilgi <id>" ya da "@herbokolog bilgi @kullanici"
        komutunu yakalar. Bu komut normal process_text/AI akisina hic
        girmez -- DB'deki HAM profili (yorum/filtre olmadan) direkt
        geri doner, interaktif yonetim menusuyle birlikte.

        Eslesme yoksa None doner.
        """

        prompt = self.clean_prompt(message)

        match = re.match(
            r"^bilgi\s+(?:<@!?(\d+)>|(\d+))\s*$",
            prompt.strip(),
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        return int(match.group(1) or match.group(2))

    # --------------------------------------------------

    def parse_delete_command(self, message):
        """
        "@herbokolog sil <id> <kategori> <kayit_id>" komutunu yakalar.
        Ornek: "sil 604008871274741800 facts 42"
        Eslesme yoksa None doner, eslesirse
        (user_id, category, row_id) tuple'i doner.
        """

        prompt = self.clean_prompt(message)

        match = re.match(
            r"^sil\s+(?:<@!?(\d+)>|(\d+))\s+(\S+)\s+(\d+)\s*$",
            prompt.strip(),
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        user_id = int(match.group(1) or match.group(2))
        category = self.resolve_category(match.group(3))
        row_id = int(match.group(4))

        return user_id, category, row_id

    # --------------------------------------------------

    def parse_add_command(self, message):
        """
        "@herbokolog ekle <id> <kategori> <metin>" komutunu yakalar.
        Ornek: "ekle 604008871274741800 facts Azerbaycan'da yasiyor"
        Eslesme yoksa None doner, eslesirse
        (user_id, category, value) tuple'i doner.
        """

        prompt = self.clean_prompt(message)

        match = re.match(
            r"^ekle\s+(?:<@!?(\d+)>|(\d+))\s+(\S+)\s+(.+)$",
            prompt.strip(),
            flags=re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return None

        user_id = int(match.group(1) or match.group(2))
        category = self.resolve_category(match.group(3))
        value = match.group(4).strip()

        return user_id, category, value

    # --------------------------------------------------

    def parse_edit_command(self, message):
        """
        "@herbokolog duzenle <id> <kategori> <kayit_id> <yeni metin>"
        komutunu yakalar.
        Eslesme yoksa None doner, eslesirse
        (user_id, category, row_id, new_value) tuple'i doner.
        """

        prompt = self.clean_prompt(message)

        match = re.match(
            r"^d[uü]zenle\s+(?:<@!?(\d+)>|(\d+))\s+(\S+)\s+(\d+)\s+(.+)$",
            prompt.strip(),
            flags=re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return None

        user_id = int(match.group(1) or match.group(2))
        category = self.resolve_category(match.group(3))
        row_id = int(match.group(4))
        new_value = match.group(5).strip()

        return user_id, category, row_id, new_value

    # --------------------------------------------------

    async def send_info_command(self, message, user_id):

        profile = self.profile.get_profile_detailed(user_id)

        if profile is None:
            await self.send_response(
                message,
                f"❌ `{user_id}` için kayıtlı bir profil yok.",
            )
            return

        pages = build_profile_pages(profile)

        content = pages[0]

        if len(pages) > 1:
            content += (
                f"\n\n_(Toplam {len(pages)} sayfa var, ama aşağıdaki "
                "yönetim menüsü ilk 25 kaydı gösterir. Metin "
                "komutlarıyla (`sil`/`ekle`/`düzenle`) diğerlerine "
                "de ulaşabilirsin.)_"
            )

        view = ProfileManagementView(self.profile, user_id)

        sent = await message.reply(
            content,
            view=view,
            mention_author=False,
        )

        view.message = sent

    # --------------------------------------------------

    async def send_delete_command(self, message, user_id, category, row_id):

        if category is None:
            await self.send_response(
                message,
                "❌ Geçersiz kategori. Kullanılabilir: "
                "facts, projects, interests, preferences "
                "(bilgi, proje, ilgi, tercih de olur).",
            )
            return

        deleted = self.profile.delete_entry(category, row_id, user_id)

        if deleted:
            await self.send_response(
                message,
                f"✅ Silindi: `{category}` kategorisinden `[{row_id}]` "
                f"numaralı kayıt (kullanıcı `{user_id}`).",
            )
        else:
            await self.send_response(
                message,
                f"❌ `[{row_id}]` numaralı kayıt `{category}` "
                f"kategorisinde ve `{user_id}` kullanıcısında bulunamadı.",
            )

    # --------------------------------------------------

    async def send_add_command(self, message, user_id, category, value):

        if category is None:
            await self.send_response(
                message,
                "❌ Geçersiz kategori. Kullanılabilir: "
                "facts, projects, interests, preferences "
                "(bilgi, proje, ilgi, tercih de olur).",
            )
            return

        if not value:
            await self.send_response(
                message,
                "❌ Eklenecek metin boş olamaz.",
            )
            return

        self.profile.ensure_user(user_id, str(user_id), str(user_id))
        self.profile.add_entry(category, user_id, value)

        await self.send_response(
            message,
            f"✅ Eklendi: `{category}` kategorisine (kullanıcı `{user_id}`)\n"
            f"> {value}",
        )

    # --------------------------------------------------

    async def send_edit_command(
        self, message, user_id, category, row_id, new_value,
    ):

        if category is None:
            await self.send_response(
                message,
                "❌ Geçersiz kategori. Kullanılabilir: "
                "facts, projects, interests, preferences "
                "(bilgi, proje, ilgi, tercih de olur).",
            )
            return

        updated = self.profile.update_entry(
            category, row_id, user_id, new_value,
        )

        if updated:
            await self.send_response(
                message,
                f"✅ Güncellendi: `{category}` `[{row_id}]`\n"
                f"> {new_value}",
            )
        else:
            await self.send_response(
                message,
                f"❌ `[{row_id}]` numaralı kayıt `{category}` "
                f"kategorisinde ve `{user_id}` kullanıcısında bulunamadı.",
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

        info_target_id = self.parse_info_command(message)

        if info_target_id is not None:

            if message.author.id not in TRUSTED_USER_IDS:
                await self.send_response(
                    message,
                    "❌ Bu komutu sadece güvenilir kullanıcılar kullanabilir.",
                )
                return

            await self.send_info_command(message, info_target_id)
            return

        delete_args = self.parse_delete_command(message)

        if delete_args is not None:

            if message.author.id not in TRUSTED_USER_IDS:
                await self.send_response(
                    message,
                    "❌ Bu komutu sadece güvenilir kullanıcılar kullanabilir.",
                )
                return

            await self.send_delete_command(message, *delete_args)
            return

        add_args = self.parse_add_command(message)

        if add_args is not None:

            if message.author.id not in TRUSTED_USER_IDS:
                await self.send_response(
                    message,
                    "❌ Bu komutu sadece güvenilir kullanıcılar kullanabilir.",
                )
                return

            await self.send_add_command(message, *add_args)
            return

        edit_args = self.parse_edit_command(message)

        if edit_args is not None:

            if message.author.id not in TRUSTED_USER_IDS:
                await self.send_response(
                    message,
                    "❌ Bu komutu sadece güvenilir kullanıcılar kullanabilir.",
                )
                return

            await self.send_edit_command(message, *edit_args)
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