import imaplib
import email
from email.header import decode_header
import re

# Precise search queries to target job application confirmations specifically
JOB_SEARCH_QUERIES = [
    'SUBJECT "thank you for applying"',
    'SUBJECT "application received"',
    'SUBJECT "application submitted"',
    'SUBJECT "thanks for applying"',
    'SUBJECT "application update"',
    'SUBJECT "interview"'
]

# Exclude emails containing these marketing/newsletter keywords in the subject
EXCLUDED_KEYWORDS = ["newsletter", "webinar", "course", "promotional", "digest", "alert", "weekly", "subscription"]

def parse_sender_name(from_header):
    """Extracts a clean company name from email header."""
    match = re.search(r'(?:"?([^"<]+)"?\s*)?<', from_header)
    if match and match.group(1):
        clean_name = match.group(1).strip()
        # Clean fluff like "Careers at X" or "Talent Acquisition"
        clean_name = re.sub(r'(?i)\b(careers|recruiting|talent|team|jobs|no-reply|notifications|hiring|hr)\b', '', clean_name).strip()
        if len(clean_name) > 2:
            return clean_name
            
    if "@" in from_header:
        domain = from_header.split("@")[-1].split(".")[0].lower()
        if domain not in ["gmail", "outlook", "yahoo", "hotmail"]:
            return domain.capitalize()
            
    return "Direct Mail / HR"

def fetch_job_emails(gmail_user, app_password, max_results=30):
    """Scans Inbox and Sent folders specifically for valid application emails."""
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    
    try:
        mail.login(gmail_user, app_password)
    except Exception as e:
        print(f"Login failed: {e}")
        return []

    extracted_jobs = []
    folders = ["inbox", '"[Gmail]/Sent Mail"']

    for folder in folders:
        try:
            status, _ = mail.select(folder)
            if status != "OK":
                continue

            for search_query in JOB_SEARCH_QUERIES:
                status, messages = mail.search(None, search_query)
                if status != "OK" or not messages[0]:
                    continue

                email_ids = messages[0].split()
                # Grab up to max_results per query
                for e_id in email_ids[-max_results:]:
                    res, msg_data = mail.fetch(e_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            # Extract Subject
                            subject_header = msg.get("Subject", "")
                            subject, encoding = decode_header(subject_header)[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")

                            # Skip newsletters or marketing emails
                            if any(neg in subject.lower() for neg in EXCLUDED_KEYWORDS):
                                continue

                            # Extract From address
                            from_addr = msg.get("From", "")
                            company_name = parse_sender_name(from_addr)
                            
                            extracted_jobs.append({
                                "company": company_name,
                                "subject": subject[:60] + "..." if len(subject) > 60 else subject,
                                "sender": from_addr,
                                "status": "Applied"
                            })
        except Exception as err:
            print(f"Error scanning folder {folder}: {err}")

    mail.logout()
    
    # De-duplicate by company name
    unique_jobs = {j["company"]: j for j in extracted_jobs}.values()
    return list(unique_jobs)