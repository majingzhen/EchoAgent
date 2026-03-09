from app.platforms.base import PlatformModel


class WechatModel(PlatformModel):
    def __init__(self) -> None:
        super().__init__(
            name="微信",
            tone_note="结构清晰、可信背书、强调长期价值",
            title_pattern="{hook}：一篇讲清关键决策",
            cta="转发给正在犹豫的朋友，一起讨论",
        )
