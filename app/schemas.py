from pydantic import BaseModel, Field


class Recommendation(BaseModel):
  recommended_mode: str
  recommended_duration_minutes: int = Field(ge=1)
  explanation_for_user: str
  steps: list[str]
  optional_audio_type: str
  suggest_alarm: bool
  confidence_label: str
