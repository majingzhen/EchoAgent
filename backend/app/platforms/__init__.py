from app.platforms.base import PlatformModel
from app.platforms.douyin import DouyinModel
from app.platforms.wechat import WechatModel
from app.platforms.weibo import WeiboModel
from app.platforms.xiaohongshu import XiaohongshuModel


def get_platform_model(name: str) -> PlatformModel:
    normalized = name.strip().lower()
    if "抖音" in name or "douyin" in normalized:
        return DouyinModel()
    if "微博" in name or "weibo" in normalized:
        return WeiboModel()
    if "微信" in name or "wechat" in normalized:
        return WechatModel()
    return XiaohongshuModel()


__all__ = [
    "PlatformModel",
    "DouyinModel",
    "WechatModel",
    "WeiboModel",
    "XiaohongshuModel",
    "get_platform_model",
]
