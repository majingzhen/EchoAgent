from app.platforms.base import PlatformModel


class DouyinModel(PlatformModel):
    def __init__(self) -> None:
        super().__init__(
            name="抖音",
            tone_note="节奏快、冲突感强、开场即给结论",
            title_pattern="{hook}，30秒看懂值不值",
            cta="点个关注，下条继续拆细节",
        )
