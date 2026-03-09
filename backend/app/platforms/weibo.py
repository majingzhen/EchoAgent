from app.platforms.base import PlatformModel


class WeiboModel(PlatformModel):
    def __init__(self) -> None:
        super().__init__(
            name="微博",
            tone_note="观点鲜明、信息密度高、便于转发讨论",
            title_pattern="{hook}，这波我站实证派",
            cta="带话题参与讨论，看看大家怎么看",
        )
