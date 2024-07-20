import email
import email.message
import imaplib
import logging
import os
import time
from datetime import datetime
from email.header import decode_header
from typing import Any, Dict, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

IMAP_URL = 'imap.gmail.com'
USERNAME = os.getenv('GMAIL_USERNAME')
PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

def decode_header_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    decoded_value, encoding = decode_header(value)[0]
    if isinstance(decoded_value, bytes):
        decoded_value = decoded_value.decode(encoding if encoding else "utf-8")
    return decoded_value

def decode_payload(part: email.message.EmailMessage) -> str:
    payload = part.get_payload(decode=True)
    try:
        return payload.decode(errors='replace')
    except AttributeError:
        return ""

def connect_to_gmail(username: str, password: str, retries: int = 3, delay: int = 2) -> imaplib.IMAP4_SSL:
    attempt = 0
    while attempt < retries:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_URL)
            mail.login(username, password)
            mail.select('inbox')
            return mail
        except Exception as e:
            logging.error(f"An Error Occurred: {e}")
        attempt += 1
        logging.info(f"Retrying... ({attempt}/{retries})")
        time.sleep(delay)
    raise ConnectionError("Failed to connect to Gmail.")

def process_email_body(msg: email.message.EmailMessage) -> Tuple[str, bool]:
    email_body = ""
    has_attachment = False

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" in content_disposition:
                has_attachment = True
            elif content_type == "text/plain":
                email_body += decode_payload(part)
    else:
        email_body += decode_payload(msg)

    return email_body, has_attachment

def extract_email_details(msg: email.message.EmailMessage) -> Dict[str, Any]:
    subject = decode_header_value(msg.get("Subject"))

    from_ = decode_header_value(msg.get("From"))
    if '<' in from_:
        parts = from_.split('<')
        name = parts[0]
        email_ = parts[1][:-1]
    else:
        name = from_
        email_ = None

    email_date = email.utils.parsedate_tz(msg["Date"])
    if email_date:
        date_ = datetime.fromtimestamp(email.utils.mktime_tz(email_date))
        received_date = date_.strftime("%Y-%m-%d %H:%M:%S")
    else:
        received_date = None

    if subject.strip().startswith('Re:'):
        is_reply = True 
    else:
        is_reply = False
    email_body, has_attachment = process_email_body(msg)

    return {
        "subject": subject,
        "sender_name": name.strip() if name else '',
        "sender_email": email_,
        "received_date": received_date,
        "body": email_body.strip(),
        "has_attachment": has_attachment,
        "is_reply": is_reply
    }


def get_emails(mail: imaplib.IMAP4_SSL) -> pd.DataFrame:
    data = []
    status, messages = mail.search(None, "ALL")

    if status != 'OK':
        logging.error("Failed to retrieve emails.")
        return pd.DataFrame()

    email_ids = messages[0].split()
    logging.info("Processing ...")
    for email_id in email_ids:
        try:
            status, email_body = mail.fetch(email_id, "(RFC822)")

            if status != 'OK':
                logging.error(f"Failed to fetch email ID {email_id}")
                continue

            for response_part in email_body:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    email_data = extract_email_details(msg)
                    data.append(email_data)
        except Exception as e:
            logging.error(f"Error fetching email ID {email_id}: {e}")

    return pd.DataFrame(data)

def main(username: str, password: str) -> pd.DataFrame:
    try:
        logging.info("Connecting to Gmail")
        mail = connect_to_gmail(username, password)
        logging.info("Fetching inbox")
        emails_df = get_emails(mail)
        return emails_df
    except Exception as e:
        logging.error(f"Failed to retrieve emails: {e}")
        return pd.DataFrame()
    finally:
        try:
            mail.logout()
        except:
            pass


if __name__=='__main__':
    emails_df = main(USERNAME, PASSWORD)
    emails_df.to_csv('data.csv',index=False)