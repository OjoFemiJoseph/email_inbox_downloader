# Gmail Inbox Downloader

This Python script downloads email details from your Gmail inbox using the IMAP protocol. It retrieves the subject, sender, received date, body, checks for attachments, and determines if the email is a reply to a previously sent message. The result is saved in a CSV file.

## Prerequisites
1. Python
2. Gmail App Password

## Generating a Gmail App Password

1. This is a straight link to the app password page: [Google Account App Password](https://myaccount.google.com/apppasswords).
2. Specify a name
5. Click "Create". Google will display a new password. Copy this password, as you'll need it for the script.

Note: you will need to enable 2 step verification to use app password

## Installation

Clone the repository:
```
git clone https://github.com/OjoFemiJoseph/email_inbox_downloader.git
cd email_inbox_downloader
```

Install the required libraries:
```
pip install -r requirements.txt
```

Create a .env file with your Gmail credentials

GMAIL_APP_PASSWORD=

GMAIL_USERNAME=

run ```python main.py```