from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class AlertItem(BaseModel):
    status: str = "firing"
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None
    generatorURL: Optional[str] = None

class AlertmanagerWebhook(BaseModel):
    version: Optional[str] = "4"
    groupKey: Optional[str] = None
    status: str = "firing"
    receiver: Optional[str] = None
    groupLabels: Dict[str, str] = Field(default_factory=dict)
    commonLabels: Dict[str, str] = Field(default_factory=dict)
    commonAnnotations: Dict[str, str] = Field(default_factory=dict)
    alerts: List[AlertItem] = Field(default_factory=list)

class IncidentReport(BaseModel):
    incident_id: str
    created_at: str
    status: str
    severity: str
    summary: str
    affected_components: List[str]
    probable_root_cause: str
    impact_assessment: str
    remediation_steps: List[str]
    prevention_recommendations: List[str]
    raw_alert_count: int
