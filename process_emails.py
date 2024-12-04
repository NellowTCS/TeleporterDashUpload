import os
import imaplib
import email
from email.header import decode_header
import base64

# Load environment variables
EMAIL_SERVER = os.getenv("EMAIL_SERVER")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def clean(text):
    """Clean text for creating filenames."""
    return "".join(c if c.isalnum() else "_" for c in text)

def save_attachment(part, save_path):
    filename = part.get_filename()
    if filename and filename.endswith(".js"):
        filepath = os.path.join(save_path, clean(filename))
        with open(filepath, "wb") as f:
            f.write(part.get_payload(decode=True))

# Connect to the server
mail = imaplib.IMAP4_SSL(EMAIL_SERVER)
mail.login(EMAIL_USER, EMAIL_PASSWORD)

# Select the mailbox you want to use
mail.select("inbox")

# Search for all emails
status, messages = mail.search(None, "ALL")
messages = messages[0].split()

save_path = os.getcwd()

for msg_num in messages:
    res, msg = mail.fetch(msg_num, "(RFC822)")
    for response in msg:
        if isinstance(response, tuple):
            # Parse the raw email
            msg = email.message_from_bytes(response[1])
            for part in msg.walk():
                # Save attachment if it is a .js file
                if part.get_content_disposition() == "attachment":
                    save_attachment(part, save_path)

# Close the connection
mail.logout()
