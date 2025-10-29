
# storage.py
import os
from pathlib import Path
from datetime import datetime
import zipfile
import io

# Root folder where all uploaded docs are stored, grouped by user_id
UPLOAD_ROOT = "uploads"

# Allowed extensions for upload
ALLOWED_EXTENSIONS = [
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".csv", ".txt", ".png", ".jpg", ".jpeg"
]

def ensure_user_folder(user_id: int):
    """
    Make sure the folder uploads/<user_id>/ exists.
    Return that folder path as a Path object.
    """
    folder = Path(UPLOAD_ROOT) / str(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def save_uploaded_file(user_id: int, uploaded_file, safe_filename: str = None):
    """
    Saves a Streamlit UploadedFile object into the user's personal folder.
    We add a timestamp prefix to avoid collisions.
    Returns:
        stored_path (str): actual path on disk where file was saved
        size_kb (int): file size in KB (rounded)
        ext (str): file extension in lower case (e.g. ".pdf", ".docx")
    """
    user_folder = ensure_user_folder(user_id)

    original_name = uploaded_file.name
    filename_to_store = safe_filename or original_name

    # add timestamp to help uniqueness
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    final_name = f"{ts}_{filename_to_store}"

    file_path = user_folder / final_name

    # write file bytes
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    size_kb = round(file_path.stat().st_size / 1024)
    ext = file_path.suffix.lower()

    return str(file_path), size_kb, ext

def build_user_zip(user_id: int):
    """
    Build an in-memory .zip file containing ALL documents
    in uploads/<user_id>/, and return the raw bytes.

    We do NOT write the zip to disk. We just return it so the
    Streamlit page can offer it as a download_button.
    """
    user_folder = ensure_user_folder(user_id)

    # Create an in-memory bytes buffer
    mem_zip = io.BytesIO()

    # Add every file in uploads/<user_id> recursively
    with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(user_folder):
            for file in files:
                abs_path = os.path.join(root, file)
                # path inside zip should NOT include full drive path,
                # only relative to the user's folder
                rel_path = os.path.relpath(abs_path, user_folder)
                zf.write(abs_path, rel_path)

    # Go back to the start of the BytesIO buffer
    mem_zip.seek(0)
    return mem_zip.getvalue()
