from datetime import datetime
from typing import Dict, Optional
from sqlmodel import Field, SQLModel, JSON, Column
from uuid import uuid4

# Define database models
class Run(SQLModel, table=True):
    __tablename__ = "runs"
    
    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    agent_id: str = Field(index=True)
    user_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    initial_prompt: str
    description: Optional[str] = None
    usage_data: Dict = Field(default={}, sa_column=Column(JSON))
    run_metadata: Dict = Field(default={}, sa_column=Column(JSON))

class RunLog(SQLModel, table=True):
    __tablename__ = "run_logs"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    run_id: int = Field(index=True, foreign_key="runs.id")
    agent_id: str = Field(index=True)
    user_id: str = Field(index=True)
    role: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    event_name: str
    event: Dict = Field(sa_column=Column(JSON))
    version: int = Field(default=1)
