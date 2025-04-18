# pip install beautifulsoup4
# pip install sqlmodel

import os
import re
import imaplib
import email.message
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Callable, List, Dict, Optional
from datetime import datetime, timedelta
import smtplib

from bs4 import BeautifulSoup
from agentic.common import RunContext
from agentic.tools.utils.registry import tool_registry, Dependency
from agentic.tools.base import BaseAgenticTool

from sqlmodel import SQLModel, Field, Session, select


class EmailMsgsProcessed(SQLModel, table=True):
    #    uid:  Optional[int] = Field(default=None, primary_key=True)          # the uid of a message
    uid: Optional[str] = Field(default=None, primary_key=True)
    from_field: str  # save some info in case multiple mailboxes or servers where UIDs might overlap..
    to_field: str  #
    subject_field: str  #
    processed: Optional[int]  #
    agent_id: str  # Save the agent as another agen may want to see this message.


@tool_registry.register(
    name="IMAPTool",
    description="Email Inbox access with IMAP",
    dependencies=[
        Dependency(
            name="beautifulsoup4",
            version="4.13.4",
            type="pip",
        ),
    ],
)
class IMAPTool(BaseAgenticTool):
    """Access an Email Inbox using IMAP protocol."""

    email_address: Optional[str] = None
    app_password: Optional[str] = None

    def __init__(self):
        pass

    def required_secrets(self) -> dict[str, str]:
        return {"IMAP_USERNAME": "Email username", "IMAP_PASSWORD": "Email password"}

    def help(self) -> str:
        return """
Create an [App Password](https://myaccount.google.com/apppasswords) to use with this connector.  

Please visit [Google's documentation](https://support.google.com/accounts/answer/185833?hl=en) 
to learn how to create an app password. You need to supply this password to use the Gmail tool.
"""

    def get_tools(self) -> list[Callable]:
        return [
            self.save_email_draft,
            self.send_email,
            self.retrieve_emails,
            self.retrieve_emails_once,
            self.list_emails,
            self.list_folders,
        ]

    def _get_gmail_folder_name(self, folder: str = "INBOX") -> str:
        """
        Convert user-friendly folder names to Gmail's internal folder names with proper quoting.

        Args:
            folder: User-provided folder name (default: "INBOX")

        Returns:
            Properly formatted and quoted Gmail folder name

        Example:
            "Sent" -> '"[Gmail]/Sent Mail"'
            "My Folder" -> '"My Folder"'
        """
        gmail_folders = {
            "Sent": '"[Gmail]/Sent Mail"',
            "Drafts": '"[Gmail]/Drafts"',
            "Spam": '"[Gmail]/Spam"',
            "Trash": '"[Gmail]/Trash"',
            "All Mail": '"[Gmail]/All Mail"',
            "Starred": '"[Gmail]/Starred"',
            "Important": '"[Gmail]/Important"',
            "INBOX": '"INBOX"',
        }

        return gmail_folders.get(folder, f'"{folder}"')

    def list_folders(self, run_context: RunContext) -> List[str]:
        """
        List all available folders in the email account.

        :return: List of folder names
        """
        self.email_address = run_context.get_secret("IMAP_USERNAME")
        self.app_password = run_context.get_secret("IMAP_PASSWORD")
        imap = None
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            imap.login(self.email_address, self.app_password)

            _, folders = imap.list()
            folder_list = []

            for folder in folders:
                # Decode and parse folder name
                decoded = folder.decode("utf-8")
                # Extract folder name from response (e.g., '(\\HasNoChildren) "/" "INBOX"')
                match = re.search(r'"([^"]+)"$', decoded)
                if match:
                    folder_list.append(match.group(1))

            return folder_list
        finally:
            if imap:
                imap.logout()

    def list_emails(
        self,
        run_context: RunContext,
        limit: int = 50,
        subject_words: str = None,
        days_back_from_today: int = 1,
        direct_mail_only: bool = True,
        folder: str = "INBOX",
    ) -> List[Dict[str, Any]]:
        """
        List emails in the inbox, optionally filtering by subject words. days_back_from_today is the number of days back
        to retrieve, so 1 means mail today, 2 means mail from yesterday, etc.

        Args:
            direct_mail_only: if True, only return emails to the user's email address

        Returns:
            List of dictionaries containing email information
        """
        self.email_address = run_context.get_secret("IMAP_USERNAME")
        self.app_password = run_context.get_secret("IMAP_PASSWORD")
        imap_server = "imap.gmail.com"
        imap_port = 993

        run_context.info(f"Starting to list emails with limit={limit}")

        imap = None
        try:
            run_context.info(f"Connecting to IMAP server: {imap_server}:{imap_port}")
            imap = imaplib.IMAP4_SSL(imap_server, imap_port)

            run_context.info(f"Logging in with email: {self.email_address}")
            imap.login(self.email_address, self.app_password)

            # Select the specified folder
            actual_folder = self._get_gmail_folder_name(folder)
            run_context.info(f"Selecting folder: {actual_folder}")
            status, folder_info = imap.select(actual_folder)
            if status != "OK":
                raise ValueError(
                    f"Failed to select folder '{actual_folder}'. Status: {status}"
                )

            # Construct search criteria
            if subject_words:
                # Properly format subject search with quotes
                search_criteria = [f'SUBJECT "{subject_words}"']
                run_context.info(
                    f"Searching for emails with subject containing: {subject_words}"
                )
            else:
                search_criteria = ["ALL"]
                run_context.info("Searching for all emails")

            # Use 'days_back' to limit the search to emails within the last 'days_back' days
            if days_back_from_today > 0:
                today = datetime.now() - timedelta(days=(days_back_from_today - 1))
                tomorrow = today + timedelta(days=1)

                # Format dates in DD-Mon-YYYY format as required by IMAP
                today_str = today.strftime("%d-%b-%Y")
                tomorrow_str = tomorrow.strftime("%d-%b-%Y")

                date_criterion = f'SINCE "{today_str}" BEFORE "{tomorrow_str}"'
                search_criteria.append(date_criterion)

            if direct_mail_only:
                search_criteria.append('NOT BODY "unsubscribe"')
                search_criteria.append('NOT BODY "Manage preferences"')
                search_criteria.append('NOT BODY "subscription"')

            # Perform the search
            run_context.info(f"Executing search with criteria: {search_criteria}")
            _, message_numbers = imap.search(None, *search_criteria)
            message_numbers = message_numbers[0].split()

            run_context.info(f"Found {len(message_numbers)} matching messages")

            # Get the most recent 'limit' emails
            message_numbers = message_numbers[-limit:]

            email_list = []
            for num in reversed(message_numbers):
                run_context.info(f"Fetching message ID: {num.decode()}")
                _, msg_data = imap.fetch(num, "(RFC822.HEADER)")
                email_header = msg_data[0][1]
                email_message = email.message_from_bytes(email_header)

                # Extract and decode email information
                subject = IMAPTool.decode_email_header(email_message["subject"])
                sender = IMAPTool.decode_email_header(email_message["from"])
                date_str = email_message["date"]

                email_list.append(
                    {
                        "id": num.decode(),
                        "subject": subject,
                        "sender": sender,
                        "date": date_str,
                    }
                )

            run_context.info(f"Successfully retrieved {len(email_list)} emails")
            return email_list

        except imaplib.IMAP4.error as e:
            run_context.info(f"IMAP error: {str(e)}")
            return [{"error": f"IMAP error: {str(e)}"}]
        except Exception as e:
            run_context.info(f"Error listing emails: {str(e)}")
            import traceback

            run_context.info(traceback.format_exc())
            return [{"error": f"Error: {str(e)}"}]
        finally:
            if imap:
                try:
                    run_context.info("Closing IMAP connection")
                    imap.close()
                    run_context.info("Logging out from IMAP server")
                    imap.logout()
                except Exception as e:
                    run_context.info(f"Error during IMAP cleanup: {str(e)[0:50]}")

    def date_based_search(
        self, imap, limit: int, search_criteria: List[str]
    ) -> List[bytes]:
        """Helper method for date-based search when SORT is not available."""
        email_ids = []
        date = datetime.now()
        while len(email_ids) < limit:
            date_criterion = f'(SINCE "{date.strftime("%d-%b-%Y")}")'
            full_criteria = search_criteria + [date_criterion]
            _, message_numbers = imap.search(None, *full_criteria)
            message_numbers = message_numbers[0].split()

            if not message_numbers:
                # If no emails found, move date back by a week
                date -= timedelta(days=7)
                continue

            email_ids.extend(message_numbers)

            # Move the date back by a day for the next iteration if needed
            date -= timedelta(days=1)

        return email_ids[-limit:]  # Return only the most recent 'limit' email IDs

    def send_email(
        self,
        run_context: RunContext,
        to: str,
        subject: str,
        body: str,
        save_draft: bool = True,
    ) -> str:
        """Drafts or sends an email message. By default messages are saved as drafts, but you can override with save_draft=False."""

        if save_draft:
            return self.save_email_draft(run_context, to, subject, body)

        self.email_address = run_context.get_secret("IMAP_USERNAME")
        self.app_password = run_context.get_secret("IMAP_PASSWORD")
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = self.email_address
        smtp_password = self.app_password

        # Create a multipart message
        msg = MIMEMultipart()
        sender_email = self.email_address
        msg["From"] = sender_email
        msg["To"] = to
        msg["Subject"] = subject

        # Body of the email
        msg.attach(MIMEText(body, "plain"))

        try:
            # Create a secure SSL context
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # Secure the connection
            server.login(smtp_username, smtp_password)
            text = msg.as_string()
            server.sendmail(sender_email, to, text)
            return f"Sent message to {to} with subject '{subject}'."
        except Exception as e:
            # Print any error messages to stdout
            return f"Error: SMTP sender error: {e}."
        finally:
            server.quit()

    def save_email_draft(
        self, run_context: RunContext, to: str, subject: str, body: str
    ) -> str:
        """Save a draft email message"""
        self.email_address = run_context.get_secret("IMAP_USERNAME")
        self.app_password = run_context.get_secret("IMAP_PASSWORD")

        # Create a multipart message
        msg = MIMEMultipart()
        sender_email = self.email_address
        msg["From"] = sender_email
        msg["To"] = to
        msg["Subject"] = subject

        # Body of the email
        msg.attach(MIMEText(body, "plain"))

        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            imap.login(self.email_address, self.app_password)

            imap.select('"[Gmail]/Drafts"')  # for Gmail
            message_bytes = msg.as_bytes()
            imap.append('"[Gmail]/Drafts"', "\\Draft", None, message_bytes)

            return f"Saved draft message to {to}."
        except Exception as e:
            # Print any error messages to stdout
            return f"Error: IMAP error: {e}."

    def retrieve_emails(
        self,
        run_context: RunContext,
        limit: int = 5,
        search_criteria: str = "",
        since_date: Optional[str | datetime] = None,
        to_address: Optional[str] = None,
        subject_words: Optional[str] = None,
        folder: str = "INBOX",
    ) -> List[Dict[str, Any]]:
        """
        Retrieve emails from the specified folder without tracking read status.
        Retrieves the same emails each time if the search criteria match.

        Args:
            limit: Maximum number of emails to retrieve (default: 5)
            search_criteria: IMAP search string for filtering emails
            since_date: Only retrieve emails after this date (string or datetime)
            to_address: Filter emails sent to this address
            subject_words: Filter emails containing these words in subject
            folder: Email folder to search in (default: "INBOX")

        Returns:
            List of dictionaries containing email data (subject, sender, date, body, attachments)
        """
        return self.retrieve_emails_base(
            run_context=run_context,
            limit=limit,
            search_criteria=search_criteria,
            since_date=since_date,
            to_address=to_address,
            subject_words=subject_words,
            folder=folder,
            mark_as_read_func=self.dummy_mark_as_read,
            is_read_func=self.dummy_is_read,
        )

    def retrieve_emails_once(
        self,
        run_context: RunContext,
        limit: int = 5,
        search_criteria: str = "",
        since_date: Optional[str | datetime] = None,
        to_address: Optional[str] = None,
        subject_words: Optional[str] = None,
        folder: str = "INBOX",
    ) -> List[Dict[str, Any]]:
        """
        Retrieve emails from the specified folder while tracking which emails have been read.
        Only returns emails that haven't been processed before.

        Args:
            limit:           Maximum number of emails to retrieve (default: 5)
            search_criteria: IMAP search string for filtering emails
            since_date:      Only retrieve emails after this date (string or datetime)
            to_address:      Filter emails sent to this address
            subject_words:   Filter emails containing these words in subject
            folder:          Email folder to search in (default: "INBOX")

        Returns:
            List of dictionaries containing email data (subject, sender, date, body, attachments)
        """
        result = self.retrieve_emails_base(
            run_context=run_context,
            limit=limit,
            search_criteria=search_criteria,
            since_date=since_date,
            to_address=to_address,
            subject_words=subject_words,
            folder=folder,
            mark_as_read_func=self.mark_email_as_read,
            is_read_func=self.is_email_read,
        )

        run_context.info(
            f"No new emails found in folder '{folder}' matching the criteria."
        )

        return result

    def retrieve_emails_base(
        self,
        run_context: RunContext,
        limit: int,
        search_criteria: str,
        mark_as_read_func: Callable,
        is_read_func: Callable,
        since_date: Optional[str | datetime] = None,
        to_address: Optional[str] = None,
        subject_words: Optional[str] = None,
        folder: str = "INBOX",
    ) -> List[Dict[str, Any]]:
        """
        Base function for retrieving and processing emails from a specified IMAP folder.

        This method connects to the IMAP server, searches for emails based on the provided criteria,
        and processes them according to the specified reading tracking functions. It supports
        various search parameters and can handle different email folder locations.

        Notes:
            - The folder parameter should use the exact IMAP folder name (case-sensitive)
            - Common Gmail folders include:
            * "INBOX" (default inbox)
            * "[Gmail]/Sent Mail" (sent emails)
            * "[Gmail]/Drafts" (draft emails)
            * "[Gmail]/Spam" (spam folder)
            * "[Gmail]/All Mail" (all emails)
            - For Gmail, folder names may vary based on account language settings
            - The search_criteria parameter accepts standard IMAP search criteria:
            * "ALL": All messages in the mailbox
            * "UNSEEN": Unread messages
            * "SEEN": Read messages
            * "FLAGGED": Starred/flagged messages
            * "UNFLAGGED": Unstarred/unflagged messages
            - The method uses the provided mark_as_read_func and is_read_func to track
            which emails have been processed, allowing for different tracking implementations
        """
        run_context.debug(
            f"Starting retrieve_emails with limit={limit}, "
            f"search_criteria='{search_criteria}', "
            f"since_date={since_date}, "
            f"to_address={to_address}, "
            f"subject_words={subject_words}"
        )

        if search_criteria:
            is_valid, message = IMAPTool.validate_imap_search_criteria(
                search_criteria, auto_fix=True
            )
            if not is_valid:
                return [{"error": message}]
            elif isinstance(message, str):
                search_criteria = message

        self.email_address = run_context.get_secret("IMAP_USERNAME")
        self.app_password = run_context.get_secret("IMAP_PASSWORD")
        imap_server = "imap.gmail.com"
        imap_port = 993

        # Handle since_date conversion
        if since_date:
            try:
                if isinstance(since_date, str):
                    # Try different date formats
                    date_formats = [
                        "%Y-%m-%d",
                        "%Y-%m-%dT%H:%M:%S",
                        "%d-%b-%Y",
                        "%Y/%m/%d",
                    ]
                    parsed_date = None
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(since_date, fmt)
                            break
                        except ValueError:
                            continue

                    if parsed_date is None:
                        raise ValueError(f"Could not parse date: {since_date}")

                    since_date = parsed_date
                elif not isinstance(since_date, datetime):
                    raise ValueError("since_date must be a string or datetime object")

                date_criterion = since_date.strftime("%d-%b-%Y")
            except Exception as e:
                run_context.info(f"Error parsing since_date: {str(e)}")
                # Default to 30 days ago if date parsing fails
                since_date = datetime.now() - timedelta(days=30)
                date_criterion = since_date.strftime("%d-%b-%Y")
        else:
            # Default to 30 days ago if no date provided
            since_date = datetime.now() - timedelta(days=30)
            date_criterion = since_date.strftime("%d-%b-%Y")

        imap = None
        try:
            imap = imaplib.IMAP4_SSL(imap_server, imap_port)
            imap.login(self.email_address, self.app_password)

            actual_folder = self._get_gmail_folder_name(folder)
            run_context.debug(f"Selecting folder: {actual_folder}")
            status, folder_info = imap.select(actual_folder)
            if status != "OK":
                raise ValueError(
                    f"Failed to select folder '{actual_folder}'. Status: {status}"
                )

            # Build search criteria list
            search_terms = [search_criteria] if search_criteria else []

            # Add date criterion
            search_terms.append(f'SINCE "{date_criterion}"')

            # Add recipient criterion if specified
            if to_address:
                search_terms.append(f'TO "{to_address}"')
            # Add subject criterion if specified
            if subject_words:
                search_terms.append(f'HEADER Subject "{subject_words}"')

            # Combine all criteria with AND logic
            final_search_criteria = "(" + ") (".join(search_terms) + ")"

            run_context.debug(
                f"Searching for emails with criteria: {final_search_criteria}"
            )
            try:
                _, message_numbers = imap.search(None, final_search_criteria)
            except imaplib.IMAP4.error as e:
                run_context.error(f"IMAP SEARCH error: {str(e)}")
                fallback_criteria = f'SINCE "{date_criterion}"'
                _, message_numbers = imap.search(None, fallback_criteria)
                run_context.debug(
                    f"Falling back to retrieving all emails since {date_criterion}"
                )

            message_numbers = message_numbers[0].split()
            run_context.debug(f"Search returned: {len(message_numbers)} messages")

            message_ids = message_numbers[-limit:]

            email_list = []
            processed_count = 0
            for num in reversed(message_numbers):  # Process all found messages
                if processed_count >= limit:
                    break

                run_context.debug(f"Fetching message ID: {num}")
                _, msg_data = imap.fetch(num, "(RFC822)")
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)

                uid = str(int.from_bytes(num, "big"))

                processed_email = self.process_email(email_message, "/tmp")
                processed_email["to"] = email_message["To"]
                email_list.append(processed_email)

                processed_count += 1

            run_context.debug(f"Successfully retrieved {len(email_list)} emails")
            return email_list

        except ValueError as ve:
            run_context.error(f"Validation error: {str(ve)}")
            raise
        except Exception as e:
            run_context.error(f"Error retrieving emails: {str(e)}")
            return []

    @staticmethod
    def validate_imap_search_criteria(
        criteria: str, auto_fix: bool = False
    ) -> tuple[bool, str]:
        """
        Validate IMAP search criteria and provide helpful guidance or fix simple issues.
        Returns (is_valid, message_or_fixed_criteria).
        If auto_fix=True, attempts to correct simple mistakes in the criteria.
        """
        valid_operators = {
            "ALL",
            "ANSWERED",
            "BCC",
            "BEFORE",
            "BODY",
            "CC",
            "DELETED",
            "FLAGGED",
            "FROM",
            "KEYWORD",
            "NEW",
            "OLD",
            "ON",
            "RECENT",
            "SEEN",
            "SINCE",
            "SUBJECT",
            "TEXT",
            "TO",
            "UNANSWERED",
            "UNDELETED",
            "UNFLAGGED",
            "UNKEYWORD",
            "UNSEEN",
        }

        if not criteria or criteria.isspace():
            help_msg = """
            IMAP Search Syntax Help:
            - Use operators like: FROM, TO, SUBJECT, BODY
            - Examples:
              * FROM "amazon.com"
              * SUBJECT "payment"
              * FROM "someone@example.com"
              * UNSEEN
              * SINCE "1-Jan-2024"
            - Combine with AND/OR:
              * (FROM "amazon.com") AND (SUBJECT "order")
            """
            return False, help_msg

        if auto_fix:
            # Normalize operator case and remove colons
            criteria = re.sub(
                r"(?i)(from|to|subject|cc|bcc):",
                lambda m: m.group(1).upper() + " ",
                criteria,
            )
            # Ensure proper spacing
            criteria = re.sub(r"\s+", " ", criteria).strip()

        # Validate parentheses balance
        if criteria.count("(") != criteria.count(")"):
            return False, "Unbalanced parentheses in search criteria."

        tokens = re.findall(r'\(|\)|"[^"]*"|\S+', criteria)
        fixed_tokens = []
        i = 0

        while i < len(tokens):
            token = tokens[i].upper()

            # Logical operators and parentheses
            if token in {"AND", "OR", "NOT", "(", ")"}:
                fixed_tokens.append(token)
                i += 1
                continue

            # Check if token is a valid operator
            if token in valid_operators:
                if (
                    token == "FROM"
                    and i + 1 < len(tokens)
                    and tokens[i + 1].startswith("(")
                ):
                    # Handle grouped conditions for FROM operator
                    grouped_emails = []
                    i += 2  # Skip the opening parenthesis
                    while i < len(tokens) and tokens[i] != ")":
                        email = tokens[i]
                        if (
                            email.upper() != "OR"
                        ):  # Skip logical operators within the group
                            if not (email.startswith('"') and email.endswith('"')):
                                email = f'"{email}"'
                            grouped_emails.append(f"FROM {email}")
                        i += 1
                    if i >= len(tokens) or tokens[i] != ")":
                        return False, "Unbalanced parentheses in FROM grouping."
                    fixed_tokens.append(f"({' OR '.join(grouped_emails)})")
                else:
                    fixed_tokens.append(token)
                    if token in {"FROM", "TO", "BCC", "CC", "SUBJECT", "BODY", "TEXT"}:
                        if i + 1 < len(tokens):
                            next_token = tokens[i + 1]
                            # Quote the next token if it's not already quoted
                            if not (
                                next_token.startswith('"') and next_token.endswith('"')
                            ):
                                if auto_fix:
                                    next_token = f'"{next_token}"'
                                else:
                                    return (
                                        False,
                                        f'{token} requires a quoted value. Example: {token} "value"',
                                    )
                            fixed_tokens.append(next_token)
                            i += 1
                        else:
                            return (
                                False,
                                f'{token} requires a value. Example: {token} "value"',
                            )
                i += 1
            else:
                # Invalid token => Insert SUBJECT as fallback for single tokens
                if auto_fix:
                    fixed_tokens.append("SUBJECT")
                    if not (token.startswith('"') and token.endswith('"')):
                        token = f'"{token}"'
                    fixed_tokens.append(token)
                else:
                    return (
                        False,
                        f"Invalid token '{token}'. Use operators like FROM, SUBJECT, TO, etc.",
                    )
                i += 1

        # Check if all parentheses are balanced
        if "(" in fixed_tokens or ")" in fixed_tokens:
            if fixed_tokens.count("(") != fixed_tokens.count(")"):
                return False, "Unbalanced parentheses in search criteria."

        # Join the fixed tokens into a validated search criteria
        fixed_criteria = " ".join(fixed_tokens)
        return True, fixed_criteria

    @staticmethod
    def mark_email_as_read(
        session: Session,
        uid: str,
        agent_id: str,
        email_message: email.message.EmailMessage,
    ):
        """Mark an email as read in the database."""
        email_msg_info = EmailMsgsProcessed(
            uid=uid,
            from_field=email_message["From"],
            to_field=email_message["To"],
            subject_field=email_message["Subject"],
            processed=1,
            agent_id=agent_id,
        )
        session.add(email_msg_info)
        session.commit()
        session.refresh(email_msg_info)

    @staticmethod
    def is_email_read(session: Session, uid: str, agent_id: str) -> bool:
        """Check if an email has been read."""
        statement = select(EmailMsgsProcessed.processed).where(
            (EmailMsgsProcessed.uid == uid) & (EmailMsgsProcessed.agent_id == agent_id)
        )
        result = session.exec(statement).first()
        return result is not None and result == 1

    @staticmethod
    def dummy_mark_as_read(
        session: Session,
        uid: str,
        agent_id: str,
        email_message: email.message.EmailMessage,
    ):
        """Dummy function that does nothing."""
        pass

    @staticmethod
    def dummy_is_read(session: Session, uid: str, agent_id: str) -> bool:
        """Dummy function that always returns False."""
        return False

    @staticmethod
    def process_email(
        email_message: email.message.EmailMessage, agent_dir: str
    ) -> Dict[str, Any]:
        """
        Process an email message, extracting subject, sender, date, body, and attachments.
        """
        subject = IMAPTool.decode_email_header(email_message["subject"])
        sender = IMAPTool.decode_email_header(email_message["from"])
        date = email_message["date"]

        body_parts = []
        attachments = []
        IMAPTool.process_email_part(email_message, body_parts, attachments, agent_dir)

        body = "\n".join(body_parts)

        return {
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": body,  # Return the full body without truncation
            #'body': body[:500] + '...' if len(body) > 500 else body,
            "attachments": attachments,
        }

    @staticmethod
    def process_email_part(part, body_parts, attachments, agent_dir):
        """
        Recursively process email parts to extract body and attachments.
        """
        if part.is_multipart():
            for subpart in part.get_payload():
                IMAPTool.process_email_part(subpart, body_parts, attachments, agent_dir)
        else:
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                body_parts.append(IMAPTool.decode_email_body(part))
            elif (
                content_type == "text/html" and "attachment" not in content_disposition
            ):
                html_content = IMAPTool.decode_email_body(part)
                body_parts.append(IMAPTool.get_text_from_html(html_content))
            elif "attachment" in content_disposition or "inline" in content_disposition:
                filename = part.get_filename()
                if filename:
                    attachment_data = part.get_payload(decode=True)
                    safe_filename = IMAPTool.get_safe_filename(filename, agent_dir)
                    file_path = os.path.join(agent_dir, safe_filename)
                    with open(file_path, "wb") as f:
                        f.write(attachment_data)
                    attachments.append(
                        {
                            "filename": safe_filename,
                            "path": file_path,
                            "size": len(attachment_data),
                        }
                    )

    @staticmethod
    def decode_email_body(part):
        """
        Decode the email body, handling different character encodings.
        """
        content = part.get_payload(decode=True)
        charset = part.get_content_charset()
        if charset:
            try:
                return content.decode(charset)
            except UnicodeDecodeError:
                return content.decode("utf-8", errors="ignore")
        return content.decode("utf-8", errors="ignore")

    @staticmethod
    def decode_email_header(header):
        """
        Decode email subject or sender information.
        """
        decoded_parts = decode_header(header)
        decoded_header = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_header += part.decode(encoding or "utf-8", errors="ignore")
            else:
                decoded_header += part
        return decoded_header

    @staticmethod
    def get_safe_filename(filename, base_dir):
        """
        Ensure the filename is safe for all operating systems and doesn't overwrite existing files.
        """
        filename = os.path.basename(filename)
        safe_filename = re.sub(r"[^\w\-_\. ]", "_", filename)
        base, extension = os.path.splitext(safe_filename)
        counter = 1
        while os.path.exists(os.path.join(base_dir, safe_filename)):
            safe_filename = f"{base}_{counter}{extension}"
            counter += 1
        return safe_filename

    @staticmethod
    def get_text_from_html(html_content):
        """Convert HTML content to plain text."""
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text()

    def test_credential(self, cred, secrets: dict, run_context: RunContext) -> str:
        """Test that the given credential secrets are valid. Return None if OK, otherwise
        return an error message.
        """

        try:
            # Extract the email address and app password from the secrets
            email_address = secrets["email_address"]
            app_password = secrets["app_password"]
            # Attempt to establish a connection to the IMAP server
            imap_server = "imap.gmail.com"
            imap_port = 993
            with imaplib.IMAP4_SSL(imap_server, imap_port) as imap:
                imap.login(email_address, app_password)
                imap.select("inbox", readonly=True)
                run_context.info("IMAP gmail tested!")
            return None  # Return None if the test is successful
        except imaplib.IMAP4.error as imap_error:
            return f"IMAP login failed: {str(imap_error)}"
        except Exception as e:
            return f"An error occurred: {str(e)}"


# End of IMAPTool class
