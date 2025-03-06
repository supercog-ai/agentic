from typing import Any, Callable, Optional, Dict
import requests
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from openai import OpenAI
import json, os

from .base import BaseAgenticTool
from .registry import tool_registry, Dependency, ConfigRequirement
from agentic.agentic_secrets import agentic_secrets
from agentic.common import RunContext
from agentic.utils.rag_helper import init_weaviate, create_collection, init_embedding_model, init_chunker
import logging  

# Configure logging  
# logging.basicConfig(  
#     level=logging.INFO,  # Set the minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)  
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Set the log format  
#     datefmt="%Y-%m-%d %H:%M:%S",  # Set the date format  
# )  
# logger = logging.getLogger(__name__)

Base = declarative_base()

class Meeting(Base):
    __tablename__ = 'meetings'
    
    id = Column(String, primary_key=True)
    name = Column(String)
    url = Column(String)
    start_time = Column(String)
    end_time = Column(String)
    duration = Column(Integer)
    transcript = Column(Text)
    summary = Column(Text)
    attendees = Column(Text)
    status = Column(String)
    recording_url = Column(String)

@tool_registry.register(
    name="MeetingTool",
    description="A tool for managing video meetings, recording transcripts, and generating summaries",
    dependencies=[
        Dependency("openai", type="pip", version="1.63.2")
    ],
    config_requirements=[
        ConfigRequirement("MEETINGBAAS_API_KEY", description="MEETINGBAAS API key", required=True),
        ConfigRequirement("OPENAI_API_KEY", description="OpenAI API key", required=True),
    ],
)


class MEETING_BAAS_Tool(BaseAgenticTool):

    def __init__(self):
        self.db_path = "meetings.db"
        # Do not initialize engine here, will be done when needed.
        self.Session = None
        self._engine = None
        self._initialized = False
        self._vector_store = None
        self._rag_initialized = False
        self.webhook_addr = ""
        try:
            self.openai_api_key = agentic_secrets.get_required_secret("OPENAI_API_KEY")
        except ValueError as e:
            self.openai_api_key = None
        try:
            
            self.meeting_baas_api_key = agentic_secrets.get_required_secret("MEETING_BAAS_API_KEY")
        except ValueError as e:
            logger.error(f"Error initializing MEETING_BAAS_Tool: {e}")
            self.meeting_baas_api_key = None

    def get_tools(self) -> list[Callable]:
        return [
            self.join_meeting,
            self.get_transcript,
            self.get_summary,
            self.list_meetings,
            self.get_meeting_info,
            self.answer_question,
            self.process_webhook
        ]

    def _initialize_rag(self):
        """Initialize the RAG components"""
        if not self._rag_initialized:
            self._weaviate_client = init_weaviate()
            create_collection(self._weaviate_client, "meeting_summaries")
            self._vector_store = self._weaviate_client.collections.get("meeting_summaries")
            self._embed_model = init_embedding_model("BAAI/bge-small-en-v1.5")
            self._rag_initialized = True

    def _get_session(self):
        """Lazy initialization of the database session."""
        if not self._initialized:
            self._engine = create_engine(f'sqlite:///{self.db_path}')
            Base.metadata.create_all(self._engine)
            self.Session = sessionmaker(bind=self._engine)
            self._initialized = True
        return self.Session()

    def __setstate__(self, state):
        """Custom deserialization for Ray."""
        self.__dict__.update(state)

    def join_meeting(
        self, 
        meeting_url: str,
        run_context: RunContext,
        bot_name: str = "Meeting Assistant"
    ) -> dict:
        """Join a video meeting and start recording"""
        logger.info(self.meeting_baas_api_key)
        
        try:
            headers = {
                "Content-Type": "application/json",
                "x-meeting-baas-api-key": self.meeting_baas_api_key
            }
            self.webhook_addr = os.environ.get("DEVTUNNEL_HOST")
            run_context.api_endpoint = self.webhook_addr
            webhook_url = run_context.get_webhook_endpoint("process_webhook")

            data = {
                "meeting_url": meeting_url,
                "bot_name": bot_name,
                "bot_image": None,
                "entry_message": "This is the Supercog meeting bot, sent by supercog support", 
                "recording_mode": "audio_only",
                "reserved": False,
                "speech_to_text": {
                    "provider": "Default"
                },
                "automatic_leave": {
                    "waiting_room_timeout": 600
                },
                "webhook_url": webhook_url
            }
            
            response = requests.post(
                "https://api.meetingbaas.com/bots",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                meeting_data = response.json()
                
                # Store meeting in database
                session = self._get_session()
                meeting = Meeting(
                    id=meeting_data["bot_id"],
                    url=meeting_url,
                    start_time=datetime.now().isoformat(),
                    status="joining"
                )
                session.add(meeting)
                session.commit()
                
                return {
                    "status": "success",
                    "meeting_id": meeting_data["bot_id"],
                    "message": "Bot is joining the meeting"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to join meeting: {response.text}"
                }
                
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Error joining meeting: {str(e)}"
            }

    def get_transcript(self, meeting_id: str) -> dict:  
        """Get the transcript for a specific meeting and save it to the database if not already present"""  
        try:  
            session = self._get_session()  
            meeting = session.query(Meeting).filter_by(id=meeting_id).first()  
            
            if not meeting:  
                return {"status": "error", "message": "Meeting not found"}  
            
            if not meeting.transcript:  
                # Fetch transcript from MeetingBaaS API  
                if not self.meeting_baas_api_key:  
                    self.meeting_baas_api_key = agentic_secrets.get_required_secret("MEETING_BAAS_API_KEY")  
                    
                headers = {"x-meeting-baas-api-key": self.meeting_baas_api_key}  
                response = requests.get(  
                    f"https://api.meetingbaas.com/bots/meeting_data",  
                    headers=headers,  
                    params={"bot_id": meeting_id}  
                )  
                
                if response.status_code == 200:  
                    data = response.json()  
                    transcripts = json.dumps(data.get("bot_data", {}).get("transcripts", []))  
                    meeting.transcript = transcripts  
                    session.commit()  
                else:  
                    return {"status": "error", "message": f"Failed to fetch transcript: {response.text}"}  
            
            return {"status": "success", "transcript": json.loads(meeting.transcript)}  
        
        except Exception as e:  
            return {"status": "error", "message": f"Error fetching transcript: {str(e)}"}  


    def get_summary(self, meeting_id: str) -> dict:
        """Generate a detailed summary of the meeting"""
        try:
            transcript_result = self.get_transcript(meeting_id)
            if transcript_result["status"] == "error":
                return transcript_result
                
            transcript = transcript_result["transcript"]
            
            formatted_transcript = ""
            for entry in transcript:
                if entry.get('words'):
                    words = ' '.join([word['text'] for word in entry['words']])
                    speaker = entry['speaker']
                    formatted_transcript += f"{speaker}: {words}\n"

            system_prompt = """
                                Please provide a detailed summary of this meeting transcript. Include:
                                1. Main topics discussed
                                2. Key decisions made
                                3. Action items and assignments
                                4. Important points raised by each participant
                                5. Timeline of major discussion points
                                Format the summary in clear sections with headers.

                                """

            client = OpenAI(api_key=self.openai_api_key)

            response = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": formatted_transcript},
                ]
            )
            
            detailed_summary = response.choices[0].message.parsed
            
            session = self._get_session()
            meeting = session.query(Meeting).filter_by(id=meeting_id).first()
            if meeting:
                meeting.summary = detailed_summary
                session.commit()
            
            # Initialize RAG if needed
            self._initialize_rag()
            
            # Use chonkie for semantic chunking (imported via rag_helper)
            chunker = init_chunker(threshold=0.5, delim=".,!,?,\n")
            chunks = chunker(detailed_summary)
            chunks_text = [chunk.text for chunk in chunks]
            
            # Generate embeddings for chunks
            embeddings = list(self._embed_model.embed(chunks_text))
            
            # Index chunks in Weaviate
            with self._vector_store.batch.dynamic() as batch:
                for i, chunk in enumerate(chunks):
                    vector = embeddings[i].tolist()
                    batch.add_object(
                        properties={
                            "content": chunk.text,
                            "document_id": meeting_id,
                            "chunk_index": i,
                            "filename": f"meeting_{meeting_id}_summary",
                            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "mime_type": "text/plain",
                            "source_url": "None",
                            "summary": "Meeting summary chunk",
                            "fingerprint": meeting_id,
                        },
                        vector=vector
                    )
            
            return {
                "status": "success",
                "summary": detailed_summary
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error generating summary: {str(e)}"
            }

    def list_meetings(self) -> dict:
        """List all recorded meetings"""
        try:
            session = self._get_session()
            meetings = session.query(Meeting).all()
            
            meeting_list = []
            for meeting in meetings:
                meeting_list.append({
                    "id": meeting.id,
                    "name": meeting.name,
                    "start_time": meeting.start_time,
                    "end_time": meeting.end_time,
                    "duration": meeting.duration,
                    "status": meeting.status
                })
                
            return {
                "status": "success",
                "meetings": meeting_list
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error listing meetings: {str(e)}"
            }

    def get_meeting_info(self, meeting_id: str) -> dict:  
        """  
        Retrieve detailed information about a specific meeting.  
        Includes metadata, transcript, and summary if available.  
        """  
        try:  
            # Establish a database session  
            session = self._get_session()  
            meeting = session.query(Meeting).filter_by(id=meeting_id).first()  
            
            # Check whether the meeting exists  
            if not meeting:  
                return {"status": "error", "message": f"Meeting with ID '{meeting_id}' not found"}  

            # Fetch meeting metadata  
            meeting_info = {  
                "id": meeting.id,  
                "name": meeting.name or "Untitled",  
                "start_time": meeting.start_time,  
                "end_time": meeting.end_time,  
                "duration": str(timedelta(seconds=meeting.duration)) if meeting.duration else "Unknown",  
                "status": meeting.status,  
            }  

            # Fetch transcript  
            transcript_result = self.get_transcript(meeting_id)  
            if transcript_result["status"] == "success":  
                meeting_info["transcript"] = transcript_result["transcript"]  
            else:  
                meeting_info["transcript_error"] = transcript_result["message"]  

            # Fetch summary  
            summary_result = self.get_summary(meeting_id)  
            if summary_result["status"] == "success":  
                meeting_info["summary"] = summary_result["summary"]  
            else:  
                meeting_info["summary_error"] = summary_result["message"]  

            return {"status": "success", "meeting_info": meeting_info}  

        except Exception as e:  
            return {"status": "error", "message": f"Error fetching meeting info: {str(e)}"}

    def answer_question(self, meeting_id: str, question: str) -> dict:
        """Answer a question related to a specific meeting"""
        try:
            self._initialize_rag()
        
            # First try to get relevant chunks from vector store
            if self._vector_store:
                # Search for relevant chunks in the vector database
                query_embedding = self._embed_model.embed(question)
                search_results = self._vector_store.query.near_vector(
                    vector=query_embedding.tolist(),
                    limit=3,
                    return_properties=["content", "document_id"],
                    where={"document_id": meeting_id}
                )
                
                if search_results.objects:
                    # Return the relevant chunks as context
                    context_chunks = [obj.properties["content"] for obj in search_results.objects]
                    return {
                        "status": "success",
                        "context": "\n\n".join(context_chunks),
                        "source": "vector_search"
                    }
            
            # Fallback to using the full summary if vector search fails or returns no results
            meeting_summary_result = self.get_summary(meeting_id)
            if meeting_summary_result["status"] == "error":
                return meeting_summary_result
                
            summary = meeting_summary_result["summary"]
            
            return {
                "status": "success",
                "context": summary,
                "source": "full_summary"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error answering question: {str(e)}"
            }

    def process_webhook(self, webhook_data: dict) -> dict:  
        """  
        Process webhook data received from MeetingBaaS.  

        This function parses the webhook data and updates the meeting object in the database.  
        
        Args:  
            webhook_data (dict): The webhook data received from MeetingBaaS.  
            
        Returns:  
            dict: A dictionary containing the processing status and any updated meeting information.  
        """  
        session = None  
        try:  
            session = self._get_session()  
            meeting_id = webhook_data.get("bot_id")  

            if not meeting_id:  
                return {  
                    "status": "error",  
                    "message": "No bot_id found in webhook data"  
                }  

            # Fetch the meeting from the database.  
            meeting = session.query(Meeting).filter_by(id=meeting_id).first()  
            if not meeting:  
                return {  
                    "status": "error",  
                    "message": f"Meeting with ID {meeting_id} not found"  
                }  

            event_type = webhook_data.get("event", "unknown_event")  
            logger.info(f"Processing webhook for Meeting ID: {meeting_id}, Event: {event_type}")  

            # Detailed handling logic based on event type.  
            if event_type == "complete":  
                logger.info(f"Webhook indicates meeting '{meeting_id}' is complete")  

                # Update recording URL and transcript from bot data.  
                bot_data = webhook_data.get("bot_data", {})  
                if bot_data:  
                    # Save the transcript.  
                    meeting.transcript = json.dumps(bot_data.get("transcripts", []))  

                    # Save the recording URL (if available).  
                    meeting.recording_url = bot_data.get("mp4", None)  

                # Set end time and calculate duration.  
                meeting.end_time = datetime.now().isoformat()  
                if meeting.start_time:  
                    start_dt = datetime.fromisoformat(meeting.start_time)  
                    end_dt = datetime.fromisoformat(meeting.end_time)  
                    meeting.duration = int((end_dt - start_dt).total_seconds())  
                
                # Fetch or generate a summary if needed.  
                if not meeting.summary and meeting.transcript:  
                    summary_result = self.get_summary(meeting_id)  
                    if summary_result.get("status") == "success":  
                        meeting.summary = summary_result["summary"]  

                meeting.status = "completed"  

            elif event_type == "failed":  
                error_code = webhook_data.get("error", "UnknownError")  
                logger.warning(f"Webhook indicates meeting '{meeting_id}' failed with error: {error_code}")  
                meeting.status = "failed"  
            
            elif event_type == "bot.status_change":  
                status_code = webhook_data.get("status", {}).get("code", "unknown_status")  
                logger.info(f"Bot status changed for meeting '{meeting_id}', new status: {status_code}")  
                meeting.status = status_code  
            
            else:  
                logger.warning(f"Unhandled webhook event type: {event_type} for meeting: {meeting_id}")  

            # Commit all updates to the database.  
            session.commit()  

            return {  
                "status": "success",  
                "message": f"Webhook processed successfully for event '{event_type}'",  
                "meeting_id": meeting_id  
            }  

        except Exception as e:  
            logger.error(f"Error processing webhook: {str(e)}")  
            return {  
                "status": "error",  
                "message": f"Error processing webhook: {str(e)}",  
                "meeting_id": webhook_data.get("bot_id", "unknown")  
            }
