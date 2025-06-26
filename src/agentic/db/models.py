from datetime import datetime
from typing import Dict, Optional
from sqlmodel import Field, SQLModel, JSON, Column
from uuid import uuid4

# Define database models
class Thread(SQLModel, table=True):
    __tablename__ = "threads"
    
    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    agent_id: str = Field(index=True)
    user_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    initial_prompt: str
    description: Optional[str] = None
    thread_metadata: Dict = Field(default={}, sa_column=Column(JSON))

class ThreadLog(SQLModel, table=True):
    __tablename__ = "thread_logs"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    thread_id: str = Field(index=True, foreign_key="threads.id")
    agent_id: str = Field(index=True)
    user_id: str = Field(index=True)
    role: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    event_name: str
    event: Dict = Field(sa_column=Column(JSON))
    depth: int = Field(default=0)
    version: int = Field(default=1)
