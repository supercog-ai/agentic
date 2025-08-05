import os
import mimetypes
import pandas as pd
import html2text
import textract
from pathlib import Path
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from PyPDF2 import PdfReader
import requests
import magic
import tempfile
import mimetypes

def read_file(file_path: str, mime_type: str|None = None) -> tuple[str, str]:
    """
    Universal file reader that handles multiple file types.
    Returns tuple of (content, mime_type)
    """
    if file_path.startswith(("http://", "https://")):
        return _read_url(file_path, mime_type)
    
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File {file_path} not found")

    mime_type = mime_type or mimetypes.guess_type(file_path)[0]
    
    mime_type = mime_type or magic.from_file(file_path, mime=True)

    print("For file: ", file_path, " Mime type: ", mime_type)
    
    if mime_type == 'inode/x-empty':
        return "", "text/plain"

    if file_path_obj.suffix.lower() == '.md' and not mime_type:
        mime_type = 'text/markdown'
    
    if not mime_type:
        mime_type = 'text/plain'
    
    if mime_type.startswith("image/"):
        raise ValueError("Image processing requires specialized tools")
    
    try:
        if mime_type == "text/csv":
            return pd.read_csv(file_path).to_csv(), mime_type
        elif mime_type in ["text/plain", "application/json", "application/xml", "text/markdown"]:
            return file_path_obj.read_text(encoding='utf-8'), mime_type
        elif 'html' in mime_type:
            return html2text.html2text(file_path_obj.read_text()), mime_type
        elif mime_type == "application/pdf":
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                text = "\n".join(page.extract_text() for page in reader.pages)
                return text, mime_type
        elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return pd.read_excel(file_path).to_csv(), mime_type
        elif mime_type == "text/x-python":
            with open(file_path,"r") as f:
                return f.read(), mime_type
        else:
            return textract.process(file_path).decode('utf-8'), mime_type
    except Exception as e:
        raise ValueError(f"Error reading {file_path}: {str(e)}") from e

def _read_url(url: str, mime_type: str = None) -> tuple[str, str]:
    """Helper to handle URL content"""
    temp_file = None
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        file_name = get_last_path_component(url)
        temp_file = tempfile.NamedTemporaryFile(
            suffix=Path(file_name).suffix,
            delete=False
        )
        
        with open(temp_file.name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        mime_type = mime_type or response.headers.get('Content-Type', '').split(';')[0]
        content, mime_type = read_file(temp_file.name, mime_type)
        return content, mime_type
        
    except Exception as e:
        raise ValueError(f"Error downloading {url}: {str(e)}") from e
    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

def get_last_path_component(url: str) -> str:
    """Extract the last component of a URL path.
    
    Args:
        url: The URL to parse
        
    Returns:
        str: The last component of the URL path. If the path is empty or ends in a slash,
             returns a fallback name constructed from the path segments or hostname.
    """

    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    path = parsed_url.path
    last_component = path.split('/')[-1]
    
    if not last_component.strip():
        last_component = "_".join(path.strip('/').split('/'))
        if not last_component:
            last_component = parsed_url.hostname or "download"
    
    return last_component 