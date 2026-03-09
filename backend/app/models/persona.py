from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PersonaPersonality(BaseModel):
    mbti: str
    communication_style: str
    description: str


class PersonaConsumerProfile(BaseModel):
    price_sensitivity: float
    brand_loyalty: float
    decision_factors: list[str]
    purchase_frequency: str
    monthly_disposable: int


class PersonaMediaBehavior(BaseModel):
    platforms: list[str]
    content_preference: list[str]
    influence_susceptibility: float
    influence_power: float


class PersonaSocialBehavior(BaseModel):
    post_frequency: str
    interaction_style: str
    stance_on_ads: str


class PersonaAgentConfig(BaseModel):
    activity_level: float
    sentiment_bias: float
    critical_thinking: float
    herd_mentality: float


class PersonaProfile(BaseModel):
    id: int
    group_id: int
    tenant_id: int
    name: str
    age: int
    gender: str
    city: str
    occupation: str
    monthly_income: int
    personality: PersonaPersonality
    consumer_profile: PersonaConsumerProfile
    media_behavior: PersonaMediaBehavior
    social_behavior: PersonaSocialBehavior
    agent_config: PersonaAgentConfig
    backstory: str


class PersonaGenerateRequest(BaseModel):
    group_name: str = "默认画像组"
    description: str
    count: int = Field(default=10, ge=3, le=50)


class PersonaGroupSummary(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: str
    source: str = "description"
    persona_count: int
    created_at: datetime
    updated_at: datetime


class PersonaGroupDetail(PersonaGroupSummary):
    personas: list[PersonaProfile]


class PersonaGenerateResponse(BaseModel):
    group: PersonaGroupSummary
    personas: list[PersonaProfile]
    planner_analysis: str
    distribution: dict[str, str]


class FocusGroupProductContext(BaseModel):
    """焦点小组的产品上下文，画像作答时的依据。"""
    raw_text: str = ""


class FocusGroupCreateRequest(BaseModel):
    persona_group_id: int
    topic: str
    product_context: FocusGroupProductContext = Field(default_factory=FocusGroupProductContext)


class FocusGroupAskRequest(BaseModel):
    question: str


class FocusGroupMessage(BaseModel):
    sender_type: str
    persona_id: int | None = None
    persona_name: str | None = None
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FocusGroupSession(BaseModel):
    id: int
    tenant_id: int
    persona_group_id: int
    topic: str
    product_context: dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    messages: list[FocusGroupMessage] = Field(default_factory=list)
    summary: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PersonaMemory(BaseModel):
    id: int
    persona_id: int
    session_type: str
    session_id: int
    memory_summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

