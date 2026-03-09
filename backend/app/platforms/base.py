from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PlatformModel:
    name: str
    tone_note: str
    title_pattern: str
    cta: str

    def render(self, brief: str, angle: dict[str, str], brand_tone: str) -> dict[str, str]:
        title = self.title_pattern.format(hook=angle["hook"])
        body = (
            f"{angle['core_message']}。\n"
            f"围绕 {brief} 展开，突出 {angle['audience']} 的真实痛点。\n"
            f"表达风格：{self.tone_note}；品牌调性：{brand_tone}。\n"
            f"互动引导：{self.cta}"
        )
        tags = "#新品 #体验分享 #真实测评"
        return {
            "title": title,
            "body": body,
            "tags": tags,
        }
