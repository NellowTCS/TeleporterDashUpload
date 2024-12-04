import os
import imaplib
import email
from email.header import decode_header
import zipfile
import shutil

# Load environment variables
EMAIL_SERVER = os.getenv("EMAIL_SERVER")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def clean(text):
    """Clean text for creating filenames."""
    return "".join(c if c.isalnum() else "_" for c in text)

def process_zip_attachment(zip_path, repo_root):
    """Process the zip file by extracting required files."""
    extract_path = os.path.join(repo_root, "temp_extracted")
    os.makedirs(extract_path, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    # Paths for specific files
    soundtracks_folder = os.path.join(repo_root, "Soundtracks")
    os.makedirs(soundtracks_folder, exist_ok=True)

    level_soundtrack_path = os.path.join(extract_path, "Sound", "Level Soundtracks")
    level_file_path = os.path.join(extract_path, "Levels")

    # Move .mp3 files to Soundtracks
    for file_name in os.listdir(level_soundtrack_path):
        if file_name.endswith(".mp3"):
            shutil.move(os.path.join(level_soundtrack_path, file_name), soundtracks_folder)

    # Move .js level file to repo root
    for file_name in os.listdir(level_file_path):
        if file_name.endswith(".js"):
            shutil.move(os.path.join(level_file_path, file_name), repo_root)

    # Remove README.txt if present
    readme_path = os.path.join(extract_path, "README.txt")
    if os.path.exists(readme_path):
        os.remove(readme_path)

    # Clean up temp extraction folder
    shutil.rmtree(extract_path)

def save_attachment(part, save_path, repo_root):
    filename = part.get_filename()
    if filename and filename.endswith(".zip"):
        filepath = os.path.join(save_path, clean(filename))
        with open(filepath, "wb") as f:
            f.write(part.get_payload(decode=True))
        process_zip_attachment(filepath, repo_root)
        os.remove(filepath)  # Delete the zip file after processing

# Connect to the server
mail = imaplib.IMAP4_SSL(EMAIL_SERVER)
mail.login(EMAIL_USER, EMAIL_PASSWORD)

# Select the mailbox you want to use
mail.select("inbox")

# Search for all emails
status, messages = mail.search(None, "ALL")
messages = messages[0].split()

repo_root = os.getcwd()

for msg_num in messages:
    res, msg = mail.fetch(msg_num, "(RFC822)")
    for response in msg:
        if isinstance(response, tuple):
            # Parse the raw email
            msg = email.message_from_bytes(response[1])
            for part in msg.walk():
                # Save attachment if it is a zip file
                if part.get_content_disposition() == "attachment":
                    save_attachment(part, repo_root, repo_root)

# Close the connection
mail.logout()
