import smtplib
from email.message import EmailMessage

from app.config import settings
from app.i18n import translator


def send_report_email(visit_dict: dict, pdf_bytes: bytes, lang: str | None = None) -> None:
    """Send the measurement PDF report. Raises on failure so the caller can
    record the error and let the user retry.
    """
    t = translator(lang)
    msg = EmailMessage()
    msg["Subject"] = t("email_subject", customer=visit_dict["customer_name"], date=visit_dict["visit_date"])
    msg["From"] = settings.email_from
    msg["To"] = settings.email_to
    msg.set_content(
        t(
            "email_body",
            customer=visit_dict["customer_name"],
            address=visit_dict["address"],
            city=visit_dict["city"],
        )
    )
    filename = f"measurement-{visit_dict['id']}.pdf"
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)
