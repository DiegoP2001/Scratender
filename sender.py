import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage
from typing import Optional
from config.config import SenderConfig
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List
from datetime import datetime, timedelta

import os
import base64
import re

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv()


class Sender:
    SERVICE_ACCOUNT_FILE = os.path.join(basedir, 'credentials.json')
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.settings.basic"
    ]


    def __init__(self, port: Optional[int] = 465, smtp_server: Optional[str] = "smtp.gmail.com", email: Optional[str] = None, password: Optional[str] = None ) -> None:
        self.port = port
        self.email = email or SenderConfig.EMAIL_SENDER
        self.password = password or SenderConfig.PASSWORD_SENDER
        self.smtp_server = smtp_server
        self.context = ssl.create_default_context()

    
    def get_gmail_service(self, user_email):
        """Crea un cliente autenticado para Gmail en nombre de un usuario específico."""
        credentials = service_account.Credentials.from_service_account_file(
            self.SERVICE_ACCOUNT_FILE,
            scopes=self.SCOPES,
            subject=user_email  
        )

        # Construir el servicio de Gmail con las credenciales del usuario
        service = build("gmail", "v1", credentials=credentials)
        return service
    
    def get_gmail_signature(self, service, user_email="me"):
        try:
            signature_data = service.users().settings().sendAs().get(userId=user_email, sendAsEmail=user_email).execute()
            return signature_data.get("signature", "")
        except Exception as e:
            print(f"No se pudo obtener la firma: {e}")
            return ""

    def send_email_v2_gmail_api(self, user_email, recipients_email: List[dict], subject, html_content: str):
        """
        Envía correos personalizados a una lista de destinatarios.

        :param user_email: Correo del remitente.
        :param recipients: Lista de diccionarios con {'email': str, 'name': str}.
        :param subject: Asunto del correo.
        :param message_body_template: Plantilla de texto con {name}.
        :param html_template: Plantilla HTML opcional con {name}.
        """
        service = self.get_gmail_service(user_email)
        # Obtener la firma del usuario
        signature_html = self.get_gmail_signature(service, user_email)

        for recipient in recipients_email:
            try:
                message = EmailMessage()
                html_message = f"""
                    <!DOCTYPE html>
                        <html lang="es">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>Listado de Licitaciones</title>
                            <style>
                                body {{
                                    line-height: 1.6;
                                    color: #333;
                                    max-width: 800px;
                                    margin: 0 auto;
                                    padding: 20px;
                                }}
                                .header {{
                                    background-color: #003366;
                                    color: white;
                                    padding: 20px;
                                    text-align: center;
                                }}
                                .content {{
                                    background-color: #f9f9f9;
                                    border: 1px solid #ddd;
                                    padding: 20px;
                                    margin-top: 20px;
                                }}
                                .footer {{
                                    margin-top: 20px;
                                    text-align: center;
                                    font-size: 0.9em;
                                    color: #666;
                                }}
                                h1, h2 {{
                                    color: #003366;
                                }}
                                .licitacion {{
                                    background-color: white;
                                    border: 1px solid #ddd;
                                    padding: 15px;
                                    margin-bottom: 20px;
                                    border-radius: 5px;
                                }}
                                .licitacion h3 {{
                                    color: #003366;
                                    margin-top: 0;
                                }}
                                .button {{
                                    display: inline-block;
                                    background-color: #4CFF50;
                                    color: white;
                                    padding: 8px 15px;
                                    text-decoration: none;
                                    border-radius: 3px;
                                    font-size: 0.9em;
                                    margin-right: 10px;
                                }}
                                table {{
                                    width: 100%;
                                    border-collapse: collapse;
                                    margin-bottom: 10px;
                                }}
                                th, td {{
                                    text-align: left;
                                    padding: 8px;
                                    border-bottom: 1px solid #ddd;
                                }}
                                th {{
                                    background-color: #f2f2f2;
                                    width: 40%;
                                }}
                                td {{
                                    width: 60%; /* Ancho fijo para los datos */
                                }}
                                .actions {{
                                    margin-top: 15px;
                                }}
                                .documents {{
                                    margin-top: 10px;
                                }}
                                .documents a {{
                                    display: inline-block;
                                    margin-right: 10px;
                                    margin-bottom: 5px;
                                    color: #4CAF50;
                                    text-decoration: none;
                                }}
                                .documents a:hover {{
                                    text-decoration: underline;
                                }}
                            </style>
                        </head>
                        <body style="font-family: 'Trebuchet MS', 'Lucida Sans Unicode', 'Lucida Grande', 'Lucida Sans', Arial, sans-serif;">
                            <div class="header">
                                <h1 style="color: white">Listado de {subject}</h1>
                            </div>
                            <div class="content">
                                <p>Hola,</p>
                                <p>Licitaciones recolectadas el día de ayer</p>
                                    { html_content }
                                <p>Para obtener más información sobre cualquiera de estas licitaciones, por favor haga clic en "Ver Detalles". Para acceder a los documentos completos de la licitación, utilice el botón "Ver Documentos".</p>
                                <p>Si necesita asistencia adicional o tiene alguna pregunta, no dude en contactar con Diego.</p>
                                <p>Atentamente,</p>
                                <p>El bot Dibu</p>
                            </div>
                            <div class="footer">
                                <p>Este correo electrónico es confidencial y está destinado únicamente a los destinatarios autorizados.</p>
                            </div>
                        </body>
                        </html>
                        { signature_html }
                """
                message.add_alternative(html_message , subtype="html")

                message["To"] = recipient
                message["From"] = user_email
                message["Subject"] = subject

                # Codificar el mensaje en Base64
                encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                create_message = {"raw": encoded_message}

                # Enviar el correo
                send_message = (
                    service.users()
                    .messages()
                    .send(userId="me", body=create_message)
                    .execute()
                )
                print(f"Correo enviado a {recipient}")

            except HttpError as e:
                print(f"Error al enviar correo a {recipient}: {e}")

    def get_latest_linkedin_email(self, user_email):
        """Busca el correo más reciente de LinkedIn y extrae el primer enlace encontrado."""
        service = self.get_gmail_service(user_email)

        try:
            # Buscar los últimos correos de LinkedIn en la bandeja de entrada
            response = service.users().messages().list(userId="me", q="from:linkedin.com", maxResults=5).execute()
            messages = response.get("messages", [])

            if not messages:
                print("No se encontraron correos de LinkedIn.")
                return None

            for msg in messages:
                message = service.users().messages().get(userId="me", id=msg["id"]).execute()
                payload = message["payload"]
                
                # Extraer el cuerpo del correo
                email_data = None
                if "parts" in payload:
                    for part in payload["parts"]:
                        if part["mimeType"] == "text/html":
                            email_data = part["body"]["data"]
                            break
                        elif part["mimeType"] == "text/plain":
                            email_data = part["body"]["data"]
                
                if email_data:
                    decoded_email = base64.urlsafe_b64decode(email_data).decode("utf-8")

                    # Buscar el primer enlace en el contenido del correo
                    links = re.findall(r"https?://[^\s<>\"']+", decoded_email)
                    linkedin_links = [link for link in links if "linkedin.com" in link]

                    if linkedin_links:
                        print(f"Enlace encontrado: {linkedin_links[0]}")
                        return linkedin_links[0]

            print("No se encontraron enlaces en los correos de LinkedIn.")
            return None

        except Exception as e:
            print(f"Error al obtener correos: {e}")
            return None
