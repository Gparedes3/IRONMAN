"""Habilidad de correo: leer/resumir la bandeja de entrada y enviar correos
vía IMAP/SMTP con una contraseña de aplicación de Gmail."""
import imaplib
import smtplib
import email
from email.header import decode_header
from email.message import EmailMessage

from ironman import config


def _decode(value) -> str:
    if value is None:
        return ""
    parts = decode_header(value)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            out.append(text.decode(enc or "utf-8", errors="ignore"))
        else:
            out.append(text)
    return "".join(out)


def fetch_recent_emails(count: int = 5) -> str:
    """Lee los correos más recientes de la bandeja y devuelve un texto
    con remitente y asunto, listo para que el modelo lo resuma."""
    try:
        imap = imaplib.IMAP4_SSL(config.IMAP_HOST)
        imap.login(config.EMAIL_ADDRESS, config.EMAIL_APP_PASSWORD)
        imap.select("INBOX")

        status, data = imap.search(None, "ALL")
        if status != "OK" or not data[0]:
            imap.logout()
            return "No hay correos en la bandeja de entrada."

        ids = data[0].split()[-count:][::-1]  # los más recientes primero
        lineas = []
        for i, msg_id in enumerate(ids, 1):
            status, msg_data = imap.fetch(msg_id, "(RFC822.HEADER)")
            if status != "OK":
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            remitente = _decode(msg.get("From"))
            asunto = _decode(msg.get("Subject"))
            lineas.append(f"{i}. De: {remitente} | Asunto: {asunto}")

        imap.logout()
        if not lineas:
            return "No se pudieron leer los correos."
        return "Correos recientes:\n" + "\n".join(lineas)
    except Exception as e:
        return f"Error al leer el correo: {e}"


def send_email(to: str, subject: str, body: str) -> str:
    """Envía un correo desde la cuenta configurada."""
    try:
        msg = EmailMessage()
        msg["From"] = config.EMAIL_ADDRESS
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.EMAIL_ADDRESS, config.EMAIL_APP_PASSWORD)
            server.send_message(msg)
        return f"Correo enviado correctamente a {to}."
    except Exception as e:
        return f"Error al enviar el correo: {e}"
