import logging
import os
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
from utils.logger import logger
from config import settings # For email credentials
from datetime import datetime # Added for datetime

logger = logging.getLogger(__name__)

class ReportService:
    """
    데이터 분석 결과를 PDF 보고서로 생성하고 이메일로 발송하는 서비스입니다.
    """
    def __init__(self):
        logger.info("ReportService initialized.")
        self.reports_dir = "generated_reports"
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_pdf_report(self, chart_image_path: str, report_data: Dict[str, Any]) -> str:
        """
        차트 이미지를 포함한 PDF 보고서를 생성합니다.
        """
        pdf_filename = os.path.join(self.reports_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        c = canvas.Canvas(pdf_filename, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 24)
        c.drawString(inch, height - inch, "데이터 분석 보고서")

        # Report Data
        c.setFont("Helvetica", 12)
        textobject = c.beginText(inch, height - inch - 0.5 * inch)
        textobject.textLine(f"파일: {report_data.get('file_name', 'N/A')}")
        textobject.textLine(f"분석 시간: {report_data.get('analysis_time', 'N/A')}")
        textobject.textLine(f"모델 유형: {report_data.get('model_type', 'N/A')}")
        textobject.textLine(f"설명: {report_data.get('description', 'N/A')}")
        c.drawText(textobject)

        # Chart Image
        if os.path.exists(chart_image_path):
            c.drawImage(chart_image_path, inch, height - inch - 4 * inch, width=400, height=300)
            logger.info(f"Chart image {chart_image_path} included in PDF.")
        else:
            logger.warning(f"Chart image not found at {chart_image_path}. PDF generated without image.")

        c.save()
        logger.info(f"PDF report generated: {pdf_filename}")
        return pdf_filename

    def send_email_with_attachment(self, recipient_email: str, subject: str, body: str, attachment_path: Optional[str] = None):
        """
        지정된 이메일 주소로 첨부 파일을 포함한 이메일을 발송합니다.
        """
        sender_email = settings.EMAIL_SENDER_EMAIL
        sender_password = settings.EMAIL_SENDER_PASSWORD
        smtp_server = settings.EMAIL_SMTP_SERVER
        smtp_port = settings.EMAIL_SMTP_PORT

        if not all([sender_email, sender_password, smtp_server, smtp_port]):
            logger.error("Email sending credentials are not fully configured.")
            raise ValueError("이메일 발송을 위한 환경 변수가 설정되지 않았습니다.")

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {os.path.basename(attachment_path)}",
                )
                msg.attach(part)
                logger.info(f"Attachment {attachment_path} added to email.")
            except Exception as e:
                logger.error(f"Failed to attach file {attachment_path}: {e}", exc_info=True)
                raise

        try:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
            logger.info(f"Email sent successfully to {recipient_email}.")
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}", exc_info=True)
            raise
