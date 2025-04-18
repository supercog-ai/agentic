import aiohttp
import json
import os
import requests
import weaviate

from datetime import datetime, timedelta
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Callable, Optional, List

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, Dependency, ConfigRequirement
from agentic.agentic_secrets import agentic_secrets
from agentic.common import RunContext
from agentic.utils.directory_management import get_runtime_directory
from agentic.utils.rag_helper import init_weaviate, create_collection, init_embedding_model, init_chunker, search_collection


class MeetingSummary(BaseModel):
    meeting_name: str
    meeting_summary: str
    attendees: List[str]

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
    name="MeetingBaasTool",
    description="A tool for managing video meetings, recording transcripts, getting meeting info and summaries",
    dependencies=[
        Dependency(
            name="openai",
            version="1.75.0",
            type="pip",
        ),
        Dependency(
            name="sqlalchemy",
            version="2.0.26",
            type="pip",
        )
    ],
    config_requirements=[
        ConfigRequirement(
            key="MEETINGBAAS_API_KEY",
            description="MEETINGBAAS API key",
            required=True
        ),
        ConfigRequirement(
            key="OPENAI_API_KEY",
            description="OpenAI API key",
            required=True
        ),
    ],
)


class MeetingBaasTool(BaseAgenticTool):

    def __init__(self):
        self.db_path = os.path.join(get_runtime_directory(), "meetings.db")
        self.Session = None
        self._engine = None
        self._initialized = False
        self._weaviate_client = None
        self._vector_store = None
        self._embed_model = None
        self._rag_initialized = False
        self.webhook_addr = ""
        try:
            self.openai_api_key = agentic_secrets.get_required_secret("OPENAI_API_KEY")
        except ValueError as e:
            self.openai_api_key = None
        try:
            self.meeting_baas_api_key = agentic_secrets.get_required_secret("MEETING_BAAS_API_KEY")
        except ValueError as e:
            print(f"Error initializing MEETING_BAAS_Tool: {e}")
            self.meeting_baas_api_key = None

    def get_tools(self) -> list[Callable]:
        return [
            self.join_meeting,
            self.get_meeting_transcript,
            self.get_meeting_summary,
            self.list_meetings,
            self.get_meeting_info,
            self.process_webhook,
            self.check_bot_status
        ]

    def _initialize_rag(self):
        """Initialize the RAG components if not already initialized"""
        if not self._rag_initialized:
            try:
                # First try to connect to existing instance
                self._weaviate_client = weaviate.connect_to_local(
                    port=8079,
                    grpc_port=50060
                )
                print("Connected to existing Weaviate instance")
            except Exception as e:
                print(f"Could not connect to existing instance: {e}")
                print("Creating new embedded instance...")
                # If connection fails, create new embedded instance
                self._weaviate_client = init_weaviate()
                
            try:
                create_collection(self._weaviate_client, "meeting_summaries")
                self._vector_store = self._weaviate_client.collections.get("meeting_summaries")
                self._embed_model = init_embedding_model("BAAI/bge-small-en-v1.5")
                self._rag_initialized = True
            except Exception as e:
                if self._weaviate_client:
                    self._weaviate_client.close()
                self._weaviate_client = None
                self._vector_store = None
                self._embed_model = None
                print(f"Error initializing RAG: {e}")
                raise

    def _get_session(self):
        """Lazy initialization of the database session."""
        if not self._initialized:
            self._engine = create_engine(f'sqlite:///{self.db_path}')
            Base.metadata.create_all(self._engine)
            self.Session = sessionmaker(bind=self._engine)
            self._initialized = True
        return self.Session()

    def __getstate__(self):
        """Custom serialization for Ray."""
        state = self.__dict__.copy()
        if self._weaviate_client:
            self._weaviate_client.close()
        state.pop('_weaviate_client', None)
        state.pop('_vector_store', None)
        state.pop('_embed_model', None)
        state.pop('_engine', None)
        state.pop('Session', None)
        return state

    def __setstate__(self, state):
        """Custom deserialization for Ray."""
        self.__dict__.update(state)
        self._initialized = False
        self._engine = None
        self.Session = None
        self._rag_initialized = False
        self._weaviate_client = None
        self._vector_store = None
        self._embed_model = None

    def join_meeting(
        self, 
        meeting_url: str,
        run_context: RunContext,
        bot_name: str = "Meeting Assistant"
    ) -> dict:
        """Dispatches a bot to join a meeting and return the bot id"""
        print("Joining call.....")
        
        try:
            headers = {
                "Content-Type": "application/json",
                "x-meeting-baas-api-key": self.meeting_baas_api_key
            }
            self.webhook_addr = os.environ.get("DEVTUNNEL_HOST")
            if not self.webhook_addr:
                return {
                    "status": "error", 
                    "message": "DEVTUNNEL_HOST environment variable not set. Please run 'devtunnel' and set DEVTUNNEL_HOST=your_tunnel_url"
                }
            
            # Get the agent's safe name for URL routing
            agent_safe_name = "".join(c if c.isalnum() else "_" for c in run_context.agent_name).lower()
            # Create the full base URL with the safe name path
            agent_base_url = f"{self.webhook_addr}/{agent_safe_name}"
            
            run_context.api_endpoint = agent_base_url
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
                bot_id = meeting_data["bot_id"]
                # Store meeting in database
                session = self._get_session()
                meeting = Meeting(
                    id=bot_id,
                    url=meeting_url,
                    start_time=datetime.now().isoformat(),
                    status="joining_call"
                )
                session.add(meeting)
                session.commit()
                
                return {
                    "joining_call": f"Joining call... The bot will join the meeting and take notes. Your bot_id is {bot_id}"
                }
            else:
                return {
                    "message": f"Failed to join meeting: {response.text}"
                }
                
        except Exception as e:
            return {
                "message": f"Error joining meeting: {str(e)}"
            }

    def get_meeting_transcript(self, meeting_id: str) -> dict:  
        """Get the transcript for a specific meeting and save it to the database if not already present"""  
        print('getting meeting transcript........')
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


    def get_meeting_summary(self, meeting_id: str) -> dict:
        """Get summary for a specific meeting"""
        print('getting meeting summary........')
        try:
            # First check if summary exists in database
            session = self._get_session()
            meeting = session.query(Meeting).filter_by(id=meeting_id).first()
            
            if meeting and meeting.summary:
                return {
                    "status": "success",
                    "summary": meeting.summary
                }
            
            # If no summary exists, get transcript and generate one
            transcript_result = self.get_meeting_transcript(meeting_id)
            if transcript_result["status"] == "error":
                return transcript_result
                
            transcript = transcript_result["transcript"]
            
            # Generate summary using helper method
            summary_result = self._generate_meeting_summary(transcript, meeting.start_time if meeting else None)
            if summary_result["status"] == "error":
                return summary_result
                
            detailed_summary = summary_result["response"].meeting_summary
            
            # Save to database
            if meeting:
                meeting.summary = detailed_summary
                session.commit()
            
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
        print('listing meetings........')
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

    def get_meeting_info(self, meeting_id: str = None, user_query: str = None) -> dict:  
        """  
        Retrieve information about meetings.
        If meeting_id is provided, search only that meeting.
        If user_query is provided, search the knowledge index.
        Falls back to database if knowledge search fails or no query provided.
        """  
        print('getting meeting info.........')
        try:  
            # If we have a query, try searching the knowledge index first
            if user_query:
                try:
                    # Initialize RAG components if needed
                    self._initialize_rag()
                    
                    # Set filters only if meeting_id is provided
                    filters = {"document_id": meeting_id} if meeting_id else None
                    
                    # Search the knowledge index using our stored components
                    search_results = search_collection(
                        collection=self._vector_store,
                        query=user_query,
                        embed_model=self._embed_model,
                        limit=5 if not meeting_id else 1,
                        filters=filters
                    )

                    if search_results and not search_results[0].get("error"):
                        return {
                            "status": "success",
                            "content": search_results[0]["content"] if meeting_id else [r["content"] for r in search_results]
                        }
                except Exception as e:
                    print(f"Knowledge index search failed: {str(e)}")

            # Fall back to database query
            session = self._get_session()
            if meeting_id:
                meeting = session.query(Meeting).filter_by(id=meeting_id).first()  
            
                if not meeting:  
                    return {"status": "error", "message": f"Meeting with ID '{meeting_id}' not found"}  

                meeting_info = {  
                    "id": meeting.id,  
                    "name": meeting.name or "Untitled",  
                    "start_time": meeting.start_time,  
                    "end_time": meeting.end_time,  
                    "duration": str(timedelta(seconds=meeting.duration)) if meeting.duration else "Unknown",  
                    "status": meeting.status
                }  

                return {"status": "success", "meeting_info": meeting_info}  

            return {"status": "error", "message": "No meeting ID provided"}

        except Exception as e:
            return {"status": "error", "message": f"Error fetching meeting info: {str(e)}"}

    def _generate_meeting_summary(self, transcript_data: list, meeting_time: str = None) -> dict:
        """Generate meeting summary using OpenAI GPT-4o"""
        try:
            # Convert transcript data to a format suitable for GPT
            formatted_transcript = ""
            for entry in transcript_data:
                if entry.get('words'):
                    words = ' '.join([word['text'] for word in entry['words']])
                    start_time = entry['start_time']
                    timestamp = f"{int(start_time//60):02d}:{int(start_time%60):02d}"
                    speaker = entry['speaker']
                    formatted_transcript += f"[{timestamp}] {speaker}: {words}\n"

            # Format meeting time if provided
            time_str = "unknown time"
            if meeting_time:
                try:
                    dt = datetime.fromisoformat(meeting_time)
                    time_str = dt.strftime("%B %d, %Y at %I:%M %p")
                except ValueError:
                    print(f"Warning: Could not parse meeting time: {meeting_time}")

            system_prompt = f"""You will be provided with the transcript of a meeting, 
                        and your goal will be to output the summary of the meeting, along with the meeting name and meeting attendees.
                        Please provide the meeting summary in markdown format. 
                        The summary should use the following format. Each meeting section summary should cover approximately 5 mins of elapsed time in the transcript. Follow this report format for the meeting summary:
                        --------------
                        ## Meeting at {time_str} with {{number of attendees}} attendees
                        ### Attendees: {{command separated list of meeting attendees, in alphabetical order}}

                        ### {{Topic: write summary of the meeting topics}}

                        #### {{Section 1 - heading}}
                        Summary of the first topic discussed in the meeting.

                        #### {{Section 2 - heading}}
                        Write additional sections for each major topic of discussion in the meeting.
                        """

            client = OpenAI(api_key=agentic_secrets.get_required_secret("OPENAI_API_KEY"))

            completion = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": formatted_transcript},
                ],
                response_format=MeetingSummary,
            )

            event = completion.choices[0].message.parsed
            return {
                "status": "success",
                "response": event
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _save_to_knowledge_index(self, bot_id: str, meeting_name: str, meeting_summary: str, attendees: list) -> None:
        """Save meeting data to the knowledge index"""
        try:
            # This will initialize if needed
            self._initialize_rag()

            # Initialize chunker
            chunker = init_chunker(threshold=0.5, delimiters=".,!,?,\n")

            # Prepare metadata
            metadata = {
                "content": meeting_summary,
                "document_id": bot_id,
                "filename": f"meeting_{bot_id}_summary.md",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "mime_type": "text/markdown",
                "source_url": "None",
                "summary": meeting_summary,
                "fingerprint": bot_id,
            }

            # Generate chunks and embeddings
            chunks = chunker(meeting_summary)
            chunks_text = [chunk.text for chunk in chunks]
            if not chunks_text:
                raise ValueError("No text chunks generated from document")
            
            batch_size = 128
            embeddings = []
            for i in range(0, len(chunks_text), batch_size):
                batch = chunks_text[i:i+batch_size]
                embeddings.extend(list(self._embed_model.embed(batch)))

            # Index chunks in Weaviate
            with self._vector_store.batch.dynamic() as batch:
                for i, chunk in enumerate(chunks):
                    vector = embeddings[i].tolist()
                    batch.add_object(
                        properties={
                            **metadata,
                            "content": chunk.text,
                            "chunk_index": i,
                        },
                        vector=vector
                    )
        except Exception as e:
            print(f"Error saving to knowledge index: {e}")
            raise

    def clean_markdown(self, markdown_text):
        """Clean markdown text by removing heading markers and extra whitespace"""
        if not markdown_text:
            return ""
        lines = markdown_text.split('\n')
        cleaned_lines = []
        for line in lines:
            cleaned_line = line.lstrip('#').strip()
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        return '\n'.join(cleaned_lines)

    async def process_webhook(self, webhook_data: dict) -> dict:
        """Process incoming webhook data from MeetingBaaS"""
        session = None
        try:
            session = self._get_session()
            
            print(f"Processing webhook data: {webhook_data}")
            event = webhook_data.get('event')
            if event is None:
                raise RuntimeError("Webhook event key was None")

            event_data = webhook_data.get('data')
            if event_data is None:
                raise RuntimeError("Webhook event data was None")

            bot_id = event_data.get("bot_id")           
            if bot_id is None:
                raise RuntimeError("Webhook bot_id was None")            
            
            # Get existing meeting URL
            existing_status = session.query(Meeting).filter_by(
                id=bot_id,
            ).first()
            meeting_url = existing_status.url if existing_status else None
            
            if event == "complete":
                print("Processing complete event")
                meeting_data = await self._fetch_meeting_data(bot_id)
                if meeting_data and meeting_data.get("bot_data"):
                    transcripts = meeting_data["bot_data"]["transcripts"]
                    created_at = meeting_data["bot_data"]["bot"].get("created_at")
                    ended_at = meeting_data["bot_data"]["bot"].get("ended_at")

                    # Generate meeting summary using helper method
                    summary_result = self._generate_meeting_summary(transcripts, created_at)
                    meeting_name = ""
                    meeting_summary = ""
                    attendees = []

                    if summary_result["status"] == "success":
                        meeting_name = summary_result["response"].meeting_name
                        meeting_summary = self.clean_markdown(summary_result["response"].meeting_summary)
                        attendees = summary_result["response"].attendees

                    # Save to database
                    meeting = Meeting(
                        id=bot_id,
                        name=meeting_name,
                        url=meeting_url,
                        start_time=created_at,
                        end_time=ended_at,
                        duration=meeting_data.get("duration", 0),
                        transcript=json.dumps(transcripts),
                        summary=meeting_summary,
                        attendees=json.dumps(attendees),
                        status="completed",
                        recording_url=meeting_data.get("mp4", "")
                    )
                    session.merge(meeting)
                    session.commit()

                    # Save to knowledge index
                    self._save_to_knowledge_index(bot_id, meeting_name, meeting_summary, attendees)

                    print(f"Successfully indexed meeting summary")
                    return {"status": "success", "message": "Meeting completed and indexed"}

            elif event == "failed":
                print("Processing failed event")
                error_code = event_data.get("error", "UnknownError")
                meeting = Meeting(
                    id=bot_id,
                    url=meeting_url,
                    status=error_code,
                    transcript="",
                    summary=f"Meeting failed with error: {error_code}"
                )
                session.merge(meeting)
                session.commit()
                return {"status": "failed", "error": error_code}
            
            elif event == "bot.status_change":
                print("Bot status changed event")
                status_code = event_data["status"]["code"]
                meeting = Meeting(
                    id=bot_id,
                    url=meeting_url,
                    status=status_code
                )
                session.merge(meeting)
                session.commit()
                return {"status": "updated", "new_status": status_code}

            return {"status": "success", "message": "Webhook processed"}
            
        except Exception as e:
            print(f"Error processing webhook: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing webhook: {str(e)}"
            }
        finally:
            if session:
                session.close()

    async def _fetch_meeting_data(self, bot_id: str) -> Optional[dict]:
        """Fetch meeting data from MeetingBaaS API"""
        try:
            url = f"https://api.meetingbaas.com/bots/meeting_data"
            api_key = self.meeting_baas_api_key
            if not api_key:
                return {"error": "No API key available for MeetingBaaS"}

            headers = {
                "x-meeting-baas-api-key": api_key
            }
            params = {"bot_id": bot_id}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
                    
        except Exception as e:
            return {"error": f"Exception occurred: {str(e)}"}

    async def check_bot_status(self, bot_id: str) -> dict:
        """Check the current status of a bot"""
        print('checking bot status.........')
        try:
            session = self._get_session()
            
            # First check meeting_status for current status or failures
            status = session.query(Meeting).filter_by(id=bot_id).first()
            
            if status:
                # Map status codes to more descriptive states
                status_descriptions = {
                    "joining_call": "Bot is attempting to join the meeting",
                    "in_waiting_room": "Bot is waiting to be admitted",
                    "in_call_not_recording": "Bot has joined but not yet recording",
                    "in_call_recording": "Bot is in the meeting and recording",
                    "call_ended": "Meeting has ended",
                    "completed": "Meeting has been successfully recorded",
                    # Error states
                    "CannotJoinMeeting": "Failed: Unable to join meeting - check meeting URL and permissions",
                    "TimeoutWaitingToStart": "Failed: Timed out waiting to be admitted",
                    "BotNotAccepted": "Failed: Bot was not accepted into the meeting",
                    "InternalError": "Failed: Internal system error occurred",
                    "InvalidMeetingUrl": "Failed: Invalid meeting URL provided"
                }

                description = status_descriptions.get(status.status, "Unknown status")

                # If call has ended, get additional details
                if status.status == "call_ended":
                    return {
                        "status": "completed",
                        "error": None,
                        "details": {
                            "meeting_name": status.name,
                            "created_at": status.start_time,
                            "ended_at": status.end_time,
                            "duration": status.duration,
                            "description": description
                        },
                        "timestamp": status.end_time
                    }

                return {
                    "status": status.status,
                    "error": None,
                    "details": {
                        "description": description
                    },
                    "timestamp": status.start_time
                }
            
            return {
                "status": "not_found",
                "error": "Bot ID not found in system",
                "details": None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "details": None,
                "timestamp": datetime.now().isoformat()
            }

    def __del__(self):
        """Cleanup when the tool is destroyed"""
        if self._weaviate_client:
            try:
                self._weaviate_client.close()
            except:
                pass
