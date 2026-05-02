from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Stats:
    questions: int = 0
    ideas: int = 0
    bugs: int = 0
    start_time: datetime = field(default_factory=datetime.now)

    def add_question(self) -> None:
        self.questions += 1

    def add_idea(self) -> None:
        self.ideas += 1

    def add_bug(self) -> None:
        self.bugs += 1

    def total(self) -> int:
        return self.questions + self.ideas + self.bugs

    def uptime(self) -> str:
        delta = datetime.now() - self.start_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        parts = []
        if days:
            parts.append(f"{days} дн.")
        if hours:
            parts.append(f"{hours} ч.")
        parts.append(f"{minutes} мин.")
        return " ".join(parts)

    def format_stats(self) -> str:
        total = self.total()
        q_pct = round(self.questions / total * 100) if total else 0
        i_pct = round(self.ideas / total * 100) if total else 0
        b_pct = round(self.bugs / total * 100) if total else 0

        return (
            "📊 <b>Статистика обращений</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"❓ <b>Вопросы:</b> {self.questions} шт. ({q_pct}%)\n"
            f"💡 <b>Идеи:</b> {self.ideas} шт. ({i_pct}%)\n"
            f"🐛 <b>Баги:</b> {self.bugs} шт. ({b_pct}%)\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"📬 <b>Всего обращений:</b> {total} шт.\n"
            f"⏱ <b>Работаю уже:</b> {self.uptime()}"
        )

stats = Stats()
