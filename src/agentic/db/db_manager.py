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
from agentic.utils.directory_management import get_runtime_filepath

# Database migration helper
# TODO: Remove after migrations are complete (07/14/25)
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

# TODO: Remove after migrations are complete (07/14/25)
def _add_depth_column_if_missing(db_path: str):
    """Add depth column to thread_logs table if it doesn't exist."""
    if db_path:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if depth column exists
        cursor.execute("PRAGMA table_info(thread_logs);")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'depth' not in columns:
            print("Adding depth column to thread_logs table...")
            try:
                cursor.execute("ALTER TABLE thread_logs ADD COLUMN depth INTEGER DEFAULT 0;")
                conn.commit()
                print("Depth column added successfully!")
            except sqlite3.OperationalError as e:
                print(f"Error adding depth column: {e}")
        
        conn.close()

# Database setup and management
class DatabaseManager:
    def __init__(self, db_path: str = "agent_threads.db"):
        if 'AGENTIC_DATABASE_URL' in os.environ:
            # Use the database URL from environment variable if set
            dburl = os.environ['AGENTIC_DATABASE_URL']
            _add_depth_column_if_missing(self.db_path)
            self.engine = create_engine(dburl, echo=False)
            self.db_path = None
        else:
            self.db_path = get_runtime_filepath(db_path)
            # Check and perform migration if needed
            _check_and_migrate_database(self.db_path)
            _add_depth_column_if_missing(self.db_path)
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
                   thread_metadata: Dict = None) -> Thread:
        thread = Thread(
            id=thread_id,
            agent_id=agent_id,
            user_id=user_id,
            initial_prompt=initial_prompt,
            description=description,
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
                  depth: int,
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
                depth=depth,
                created_at=thread_timestamp,
                event_name=event_name,
                event=event_data,
            )
            session.add(log)
            
            # Update the parent thread
            thread = session.get(Thread, thread_id)
            if thread:
                thread.updated_at = thread_timestamp
                session.add(thread)
            
            session.commit()
            session.refresh(log)
            return log

    def update_thread(self,
                   thread_id: int,
                   description: Optional[str] = None,
                   thread_metadata: Optional[Dict] = None) -> Optional[Thread]:
        with self.get_session() as session:
            thread = session.get(Thread, thread_id)
            if thread:
                if description is not None:
                    thread.description = description
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

    def get_thread_usage(self, thread_id: str) -> Dict[str, Dict[str, float]]:
        """Calculate total usage for a thread by summing completion events"""
        logs = self.get_thread_logs(thread_id)
        
        usage_by_model = {}
        for log in logs:
            if log.event_name == "completion_end" and "usage" in log.event:
                usage = log.event["usage"]
                model = usage.get("model", "unknown")
                
                if model not in usage_by_model:
                    usage_by_model[model] = {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cost": 0,
                        "elapsed_time": 0,
                        "call_count": 0
                    }
                
                usage_by_model[model]["input_tokens"] += usage.get("input_tokens", 0)
                usage_by_model[model]["output_tokens"] += usage.get("output_tokens", 0)
                usage_by_model[model]["cost"] += usage.get("cost", 0)
                usage_by_model[model]["elapsed_time"] += usage.get("elapsed_time", 0)
                usage_by_model[model]["call_count"] += 1
        
        return usage_by_model
    
    def get_thread_summary(self, thread_id: str) -> Dict:
        """Get thread summary including usage statistics"""
        thread = self.get_thread(thread_id)
        if not thread:
            return None
        
        usage = self.get_thread_usage(thread_id)
        
        # Calculate totals
        total_cost = sum(model_usage["cost"] for model_usage in usage.values())
        total_tokens = sum(
            model_usage["input_tokens"] + model_usage["output_tokens"] 
            for model_usage in usage.values()
        )
        
        return {
            "thread_id": thread.id,
            "agent_id": thread.agent_id,
            "created_at": thread.created_at,
            "updated_at": thread.updated_at,
            "initial_prompt": thread.initial_prompt,
            "usage_by_model": usage,
            "total_cost": total_cost,
            "total_tokens": total_tokens
        }
