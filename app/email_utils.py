import smtplib
from email.message import EmailMessage

from app.config import settings


def send_report_email(visit_dict: dict, pdf_bytes: bytes) -> None:
    """Send the measurement PDF report. Raises on failure so the caller can
    record the error and let the user retry.
    """
    msg = EmailMessage()
    msg["Subject"] = f"Measurement report - {visit_dict['customer_name']} - {visit_dict['visit_date']}"
    msg["From"] = settings.email_from
    msg["To"] = settings.email_to
    msg.set_content(
        f"New measurement report for {visit_dict['customer_name']} "
        f"({visit_dict['address']}, {visit_dict['city']}) attached."
    )
    filename = f"measurement-{visit_dict['id']}.pdf"
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)
