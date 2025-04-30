from datetime import datetime, UTC
from typing import Dict, Optional
from sqlmodel import Session, SQLModel, create_engine, select, asc, desc
from pathlib import Path
from copy import deepcopy

from agentic.db.models import Run, RunLog
from agentic.events import FinishCompletion
from agentic.utils.directory_management import get_runtime_filepath

# Database setup and management
class DatabaseManager:
    def __init__(self, db_path: str = "agent_runs.db"):
        self.db_path = get_runtime_filepath(db_path)
        self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        self.create_db_and_tables()

    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        return Session(self.engine)

    def create_run(self,
                   agent_id: str,
                   user_id: str,
                   initial_prompt: str,
                   run_id: Optional[str] = None,
                   description: Optional[str] = None,
                   usage_data: Dict = None,
                   run_metadata: Dict = None) -> Run:
        run = Run(
            id=run_id,
            agent_id=agent_id,
            user_id=user_id,
            initial_prompt=initial_prompt,
            description=description,
            usage_data=usage_data or {},
            run_metadata=run_metadata or {}
        )
        
        with self.get_session() as session:
            session.add(run)
            session.commit()
            session.refresh(run)
            return run

    def log_event(self,
                  run_id: int,
                  agent_id: str,
                  user_id: str,
                  role: str,
                  event_name: str,
                  event_data: Dict) -> RunLog:
        with self.get_session() as session:
            run_timestamp = datetime.now(UTC)
            # Create the log entry
            log = RunLog(
                run_id=run_id,
                agent_id=agent_id,
                user_id=user_id,
                role=role,
                created_at=run_timestamp,
                event_name=event_name,
                event=event_data
            )
            session.add(log)
            
            # Update the parent run
            run = session.get(Run, run_id)
            if run:
                run.updated_at = run_timestamp
                # Update usage data if event contains it
                if event_name == "completion_end":
                    usage = event_data["usage"]

                    # Make a copy so changes are detected
                    usage_data = deepcopy(run.usage_data)
                    for model in usage:
                        if model not in usage_data:
                            usage_data[model] = usage[model]
                        else:
                            usage_data[model][FinishCompletion.INPUT_TOKENS_KEY] += usage[model].get(FinishCompletion.INPUT_TOKENS_KEY, 0)
                            usage_data[model][FinishCompletion.OUTPUT_TOKENS_KEY] += usage[model].get(FinishCompletion.OUTPUT_TOKENS_KEY, 0)
                            usage_data[model][FinishCompletion.COST_KEY] += usage[model].get(FinishCompletion.COST_KEY, 0)
                    
                    run.usage_data = usage_data
                session.add(run)
            
            session.commit()
            session.refresh(log)
            return log

    def update_run(self,
                   run_id: int,
                   description: Optional[str] = None,
                   usage_data: Optional[Dict] = None,
                   run_metadata: Optional[Dict] = None) -> Optional[Run]:
        with self.get_session() as session:
            run = session.get(Run, run_id)
            if run:
                if description is not None:
                    run.description = description
                if usage_data is not None:
                    updated_usage_data = deepcopy(run.usage_data)
                    updated_usage_data.update(usage_data)
                    run.usage_data = updated_usage_data
                if run_metadata is not None:
                    updated_run_metadata = deepcopy(run.run_metadata)
                    updated_run_metadata.update(run_metadata)
                    run.run_metadata = updated_run_metadata
                    run.run_metadata.update(run_metadata)
                run.updated_at = datetime.now(UTC)
                session.add(run)
                session.commit()
                session.refresh(run)
                return run
            return None

    def get_run(self, run_id: int) -> Optional[Run]:
        with self.get_session() as session:
            return session.get(Run, run_id)

    def get_run_logs(self, run_id: int) -> list[RunLog]:
        with self.get_session() as session:
            return session.exec(select(RunLog).where(RunLog.run_id == run_id).order_by(asc(RunLog.created_at))).all()

    def get_runs_by_user(self, user_id: str) -> list[Run]:
        with self.get_session() as session:
            return session.exec(select(Run).where(Run.user_id == user_id).order_by(desc(Run.updated_at))).all()

    def get_runs_by_agent(self, agent_id: str, user_id: str|None) -> list[Run]:
        with self.get_session() as session:
            query = select(Run).where(Run.agent_id == agent_id)
        
            # Add user_id filter if it's not None
            if user_id is not None:
                query = query.where(Run.user_id == user_id)
            
            return session.exec(query.order_by(desc(Run.updated_at))).all()
