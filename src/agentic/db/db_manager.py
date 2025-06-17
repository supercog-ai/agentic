from datetime import datetime, UTC
import os
from typing import Dict, Optional
from sqlmodel import Session, SQLModel, create_engine, select, asc, desc
from pathlib import Path
from copy import deepcopy
import sqlite3
import shutil
from agentic.utils.json import make_json_serializable
from agentic.db.models import Thread, ThreadLog
from agentic.events import FinishCompletion
from agentic.utils.directory_management import get_runtime_filepath

# Database migration helper
# TODO: Remove after migrations are complete
def _check_and_migrate_database(db_path: str):
    """Check if database migration is needed and perform it if necessary."""
    runtime_dir = Path(db_path).parent
    old_db_path = runtime_dir / "agent_runs.db"
    new_db_path = runtime_dir / "agent_threads.db"
    
    # If old database exists but new one doesn't, perform migration
    if old_db_path.exists() and not new_db_path.exists():
        print("Detected old database schema. Performing automatic migration...")
        
        try:
            # Connect to the old database
            conn = sqlite3.connect(old_db_path)
            cursor = conn.cursor()
            
            # Check if it's actually the old schema
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='runs';")
            if cursor.fetchone():
                # Begin transaction
                conn.execute("BEGIN TRANSACTION;")
                
                # Rename columns
                try:
                    cursor.execute("ALTER TABLE runs RENAME COLUMN run_metadata TO thread_metadata;")
                except sqlite3.OperationalError:
                    pass  # Column might already be renamed
                
                try:
                    cursor.execute("ALTER TABLE run_logs RENAME COLUMN run_id TO thread_id;")
                except sqlite3.OperationalError:
                    pass  # Column might already be renamed
                
                # Rename tables
                cursor.execute("ALTER TABLE runs RENAME TO threads;")
                cursor.execute("ALTER TABLE run_logs RENAME TO thread_logs;")
                
                # Commit the transaction
                conn.commit()
                conn.close()
                
                # Rename the database file
                shutil.move(old_db_path, new_db_path)
                print("Migration completed successfully!")
            else:
                conn.close()
        except Exception as e:
            print(f"Error during migration: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            raise

# Database setup and management
class DatabaseManager:
    def __init__(self, db_path: str = "agent_threads.db"):
        if 'AGENTIC_DATABASE_URL' in os.environ:
            # Use the database URL from environment variable if set
            dburl = os.environ['AGENTIC_DATABASE_URL']
            self.engine = create_engine(dburl, echo=False)
            self.db_path = None
        else:
            self.db_path = get_runtime_filepath(db_path)
            # Check and perform migration if needed
            _check_and_migrate_database(self.db_path)
            self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)

        self.create_db_and_tables()

    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        return Session(self.engine)

    def create_thread(self,
                   agent_id: str,
                   user_id: str,
                   initial_prompt: str,
                   thread_id: Optional[str] = None,
                   description: Optional[str] = None,
                   usage_data: Dict = None,
                   thread_metadata: Dict = None) -> Thread:
        thread = Thread(
            id=thread_id,
            agent_id=agent_id,
            user_id=user_id,
            initial_prompt=initial_prompt,
            description=description,
            usage_data=usage_data or {},
            thread_metadata=thread_metadata or {}
        )
        
        with self.get_session() as session:
            session.add(thread)
            session.commit()
            session.refresh(thread)
            return thread

    def log_event(self,
                  thread_id: int,
                  agent_id: str,
                  user_id: str,
                  role: str,
                  event_name: str,
                  event_data: Dict) -> ThreadLog:
        event_data = make_json_serializable(event_data.copy())

        with self.get_session() as session:
            thread_timestamp = datetime.now(UTC)
            # Create the log entry
            log = ThreadLog(
                thread_id=thread_id,
                agent_id=agent_id,
                user_id=user_id,
                role=role,
                created_at=thread_timestamp,
                event_name=event_name,
                event=event_data
            )
            session.add(log)
            
            # Update the parent thread
            thread = session.get(Thread, thread_id)
            if thread:
                thread.updated_at = thread_timestamp
                # Update usage data if event contains it
                if event_name == "completion_end":
                    usage = event_data["usage"]

                    # Make a copy so changes are detected
                    usage_data = deepcopy(thread.usage_data)
                    for model in usage:
                        if model not in usage_data:
                            usage_data[model] = usage[model]
                        else:
                            usage_data[model][FinishCompletion.INPUT_TOKENS_KEY] += usage[model].get(FinishCompletion.INPUT_TOKENS_KEY, 0)
                            usage_data[model][FinishCompletion.OUTPUT_TOKENS_KEY] += usage[model].get(FinishCompletion.OUTPUT_TOKENS_KEY, 0)
                            usage_data[model][FinishCompletion.COST_KEY] += usage[model].get(FinishCompletion.COST_KEY, 0)
                    
                    thread.usage_data = usage_data
                session.add(thread)
            
            session.commit()
            session.refresh(log)
            return log

    def update_thread(self,
                   thread_id: int,
                   description: Optional[str] = None,
                   usage_data: Optional[Dict] = None,
                   thread_metadata: Optional[Dict] = None) -> Optional[Thread]:
        with self.get_session() as session:
            thread = session.get(Thread, thread_id)
            if thread:
                if description is not None:
                    thread.description = description
                if usage_data is not None:
                    updated_usage_data = deepcopy(thread.usage_data)
                    updated_usage_data.update(usage_data)
                    thread.usage_data = updated_usage_data
                if thread_metadata is not None:
                    updated_thread_metadata = deepcopy(thread.thread_metadata)
                    updated_thread_metadata.update(thread_metadata)
                    thread.thread_metadata = updated_thread_metadata
                thread.updated_at = datetime.now(UTC)
                session.add(thread)
                session.commit()
                session.refresh(thread)
                return thread
            return None

    def get_thread(self, thread_id: int) -> Optional[Thread]:
        with self.get_session() as session:
            return session.get(Thread, thread_id)

    def get_thread_logs(self, thread_id: int) -> list[ThreadLog]:
        with self.get_session() as session:
            return session.exec(select(ThreadLog).where(ThreadLog.thread_id == thread_id).order_by(asc(ThreadLog.created_at))).all()

    def get_threads_by_user(self, user_id: str) -> list[Thread]:
        with self.get_session() as session:
            return session.exec(select(Thread).where(Thread.user_id == user_id).order_by(desc(Thread.updated_at))).all()

    def get_threads_by_agent(self, agent_id: str, user_id: str|None) -> list[Thread]:
        with self.get_session() as session:
            query = select(Thread).where(Thread.agent_id == agent_id)
        
            # Add user_id filter if it's not None
            if user_id is not None:
                query = query.where(Thread.user_id == user_id)
            
            return session.exec(query.order_by(desc(Thread.updated_at))).all()
