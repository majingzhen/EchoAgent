from app.platforms.base import PlatformModel


class XiaohongshuModel(PlatformModel):
    def __init__(self) -> None:
        super().__init__(
            name="小红书",
            tone_note="种草感、生活化、强调真实体验",
            title_pattern="{hook}｜这次真的被说服了",
            cta="评论区说说你最在意的购买因素",
        )
