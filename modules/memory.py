from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MessageData:
    author: str
    content: str
    timestamp: datetime


class MemoryManager:

    def __init__(self, max_history: int = 20):
        self.max_history = max_history

        self.channels = defaultdict(
            lambda: deque(maxlen=max_history)
        )

    # --------------------------------------------------

    def add(
        self,
        channel_id: int,
        author: str,
        content: str,
    ):

        self.channels[channel_id].append(
            MessageData(
                author=author,
                content=content,
                timestamp=datetime.now(),
            )
        )

    # --------------------------------------------------

    def history_text(
        self,
        channel_id: int,
    ) -> str:

        if channel_id not in self.channels:
            return ""

        return "\n".join(
            f"{m.author}: {m.content}"
            for m in self.channels[channel_id]
        )

    # --------------------------------------------------

    def clear(
        self,
        channel_id: int,
    ):

        self.channels[channel_id].clear()