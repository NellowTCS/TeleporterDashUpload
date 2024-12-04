import os
import imaplib
import email
from email.header import decode_header
import zipfile
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean(text):
    """
    Clean text for creating safe filenames.
    
    Args:
        text (str): Input text to be cleaned
    
    Returns:
        str: Sanitized filename with only alphanumeric characters and underscores
    """
    return "".join(c if c.isalnum() else "_" for c in text)

def process_zip_attachment(zip_path, repo_root):
    """
    Process the zip file by extracting and organizing required files.
    
    Args:
        zip_path (str): Full path to the zip file
        repo_root (str): Root directory of the repository
    """
    try:
        # Create temporary extraction directory
        extract_path = os.path.join(repo_root, "temp_extracted")
        os.makedirs(extract_path, exist_ok=True)
        
        # Extract zip contents
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Paths for specific directories
        soundtracks_folder = os.path.join(repo_root, "Soundtracks")
        os.makedirs(soundtracks_folder, exist_ok=True)
        
        level_soundtrack_path = os.path.join(extract_path, "Sound", "Level Soundtracks")
        level_file_path = os.path.join(extract_path, "Levels")
        
        # Move .mp3 files to Soundtracks folder
        if os.path.exists(level_soundtrack_path):
            for file_name in os.listdir(level_soundtrack_path):
                if file_name.endswith(".mp3"):
                    source = os.path.join(level_soundtrack_path, file_name)
                    dest = os.path.join(soundtracks_folder, file_name)
                    shutil.move(source, dest)
                    logger.info(f"Moved soundtrack: {file_name}")
        
        # Move .js level files to repo root
        if os.path.exists(level_file_path):
            for file_name in os.listdir(level_file_path):
                if file_name.endswith(".js"):
                    source = os.path.join(level_file_path, file_name)
                    dest = os.path.join(repo_root, file_name)
                    shutil.move(source, dest)
                    logger.info(f"Moved level file: {file_name}")
        
        # Remove README.txt if present
        readme_path = os.path.join(extract_path, "README.txt")
        if os.path.exists(readme_path):
            os.remove(readme_path)
            logger.info("Removed README.txt")
        
    except Exception as e:
        logger.error(f"Error processing zip attachment: {e}")
    
    finally:
        # Clean up temporary extraction folder
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
            logger.info("Cleaned up temporary extraction folder")

def save_attachment(part, save_path, repo_root):
    """
    Save and process email attachments.
    
    Args:
        part (email.message.Message): Email message part
        save_path (str): Path to save attachments
        repo_root (str): Root directory of the repository
    """
    try:
        filename = part.get_filename()
        if filename and filename.endswith(".zip"):
            # Sanitize filename
            clean_filename = clean(filename)
            filepath = os.path.join(save_path, clean_filename)
            
            # Save zip file
            with open(filepath, "wb") as f:
                f.write(part.get_payload(decode=True))
            
            logger.info(f"Saved attachment: {filename}")
            
            # Process the zip file
            process_zip_attachment(filepath, repo_root)
            
            # Remove the zip file after processing
            os.remove(filepath)
            logger.info(f"Deleted zip file: {filename}")
    
    except Exception as e:
        logger.error(f"Error saving attachment: {e}")

def process_emails(email_server, email_user, email_password, repo_root=None):
    """
    Process emails and extract attachments.
    
    Args:
        email_server (str): IMAP email server address
        email_user (str): Email username
        email_password (str): Email password
        repo_root (str, optional): Root directory for file processing. Defaults to current working directory.
    """
    # Use current working directory if no repo_root specified
    if repo_root is None:
        repo_root = os.getcwd()
    
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(email_server)
        mail.login(email_user, email_password)
        
        # Select the mailbox
        mail.select("inbox")
        
        # Search for all emails
        status, messages = mail.search(None, "ALL")
        messages = messages[0].split()
        
        logger.info(f"Found {len(messages)} emails to process")
        
        # Process each email
        for msg_num in messages:
            try:
                res, msg = mail.fetch(msg_num, "(RFC822)")
                for response in msg:
                    if isinstance(response, tuple):
                        # Parse the raw email
                        email_msg = email.message_from_bytes(response[1])
                        
                        # Walk through email parts
                        for part in email_msg.walk():
                            # Save attachment if it is a zip file
                            if part.get_content_disposition() == "attachment":
                                save_attachment(part, repo_root, repo_root)
            
            except Exception as e:
                logger.error(f"Error processing email {msg_num}: {e}")
        
        logger.info("Email processing complete")
    
    except Exception as e:
        logger.error(f"Error connecting to email server: {e}")
    
    finally:
        # Ensure mail connection is closed
        try:
            mail.logout()
        except:
            pass

def main():
    """
    Main function to run email processing.
    Reads email credentials from environment variables.
    """
    # Load environment variables
    EMAIL_SERVER = os.getenv("EMAIL_SERVER")
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    
    if not all([EMAIL_SERVER, EMAIL_USER, EMAIL_PASSWORD]):
        logger.error("Missing email configuration. Please set EMAIL_SERVER, EMAIL_USER, and EMAIL_PASSWORD environment variables.")
        return
    
    process_emails(EMAIL_SERVER, EMAIL_USER, EMAIL_PASSWORD)

if __name__ == "__main__":
    main()
