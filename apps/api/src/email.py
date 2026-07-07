import os

RESET_URL_BASE = os.environ.get("ISRA_RESET_URL_BASE", "http://localhost:3000/reset-password")
SMTP_HOST = os.environ.get("ISRA_SMTP_HOST")
SMTP_PORT = int(os.environ.get("ISRA_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("ISRA_SMTP_USER")
SMTP_PASS = os.environ.get("ISRA_SMTP_PASS")
SMTP_FROM = os.environ.get("ISRA_SMTP_FROM", "noreply@isra.dev")


def send_reset_email(email: str, token: str) -> None:
    link = f"{RESET_URL_BASE}?token={token}"
    if not SMTP_HOST:
        print(f"[DEV RESET LINK] {email} -> {link}")
        return

    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg["Subject"] = "Reset your ISRA password"
    msg["From"] = SMTP_FROM
    msg["To"] = email
    msg.set_content(
        f"Reset your ISRA password here: {link}\n\nThis link expires in 1 hour."
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USER and SMTP_PASS:
            server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
