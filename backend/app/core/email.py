import asyncio
import base64
import logging
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    ContentId,
    Disposition,
    FileContent,
    FileName,
    FileType,
    Mail,
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


async def send_email(
    to_emails: List[str],
    subject: str,
    html_content: str,
    from_email: Optional[str] = None,
    attachments: Optional[List[Dict[str, str]]] = None,
) -> bool:
    """
    Send an email using SendGrid.

    Args:
        to_emails: List of recipient email addresses
        subject: Email subject
        html_content: HTML content of the email
        from_email: Sender email address (defaults to FROM_EMAIL from .env)
        attachments: Optional list of attachments with 'filename' and 'content' keys

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        logger.info(f"[EMAIL] Preparing to send email. To: {to_emails}, Subject: {subject}")

        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        if not sendgrid_api_key:
            error_msg = "SENDGRID_API_KEY not found in environment variables"
            logger.error(f"[EMAIL] {error_msg}")
            return False

        from_email = from_email or os.getenv("FROM_EMAIL")
        if not from_email:
            error_msg = "FROM_EMAIL not found in environment variables"
            logger.error(f"[EMAIL] {error_msg}")
            return False

        logger.info(f"[EMAIL] Sending from: {from_email} to: {to_emails}")

        # Create email message
        message = Mail(
            from_email=from_email,
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
        )

        # Add attachments if provided
        if attachments:
            logger.info(f"[EMAIL] Processing {len(attachments)} attachments")
            for i, attachment in enumerate(attachments, 1):
                try:
                    with open(attachment["filename"], "rb") as f:
                        data = f.read()
                        encoded = base64.b64encode(data).decode()

                        attached_file = Attachment()
                        attached_file.file_content = FileContent(encoded)
                        attached_file.file_type = FileType("application/octet-stream")
                        attached_file.file_name = FileName(os.path.basename(attachment["filename"]))
                        attached_file.disposition = Disposition("attachment")
                        if "content_id" in attachment:
                            attached_file.content_id = ContentId(attachment["content_id"])

                        message.attachment = attached_file
                        logger.debug(f"[EMAIL] Added attachment {i}: {attachment['filename']}")
                except Exception as e:
                    logger.error(
                        f"[EMAIL] Error processing attachment {attachment.get('filename')}: {str(e)}",
                        exc_info=True,
                    )

        # Initialize SendGrid client and send email
        logger.info("[EMAIL] Initializing SendGrid client...")

        try:
            sg = SendGridAPIClient(sendgrid_api_key)

            logger.info("[EMAIL] Sending email via SendGrid...")
            # Make sure to await the async call
            response = await asyncio.get_event_loop().run_in_executor(None, lambda: sg.send(message))

            # Log response details
            logger.info(f"[EMAIL] Email sent successfully to {', '.join(to_emails)}")
            logger.info(f"[EMAIL] Status code: {response.status_code}")
            logger.debug(f"[EMAIL] Response headers: {response.headers}")

            # Check if the email was successfully sent (2xx status code)
            if 200 <= response.status_code < 300:
                logger.info("[EMAIL] Email sent successfully")
                return True
            else:
                logger.error(f"[EMAIL] Failed to send email. Status code: {response.status_code}")
                logger.error(f"[EMAIL] Response body: {response.body}")
                return False

        except Exception as e:
            logger.error(f"[EMAIL] Error sending email via SendGrid: {str(e)}", exc_info=True)
            return False

    except Exception as e:
        error_msg = f"[EMAIL] Error sending email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False


def send_lead_confirmation(lead_data: Dict) -> bool:
    """
    Send a confirmation email to the lead.

    Args:
        lead_data: Dictionary containing lead information

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    first_name = lead_data.get("first_name", "there")
    email = lead_data.get("email")

    if not email:
        logger.error("No email provided in lead data")
        return False

    subject = "Thank You for Contacting Us!"

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
            <h2 style="color: #4a6baf;">Thank You, {first_name}!</h2>
            <p>We've received your information and our team will get back to you shortly.</p>

            <div style="margin: 20px 0; padding: 15px; background-color: #e9f0f9; border-radius: 5px;">
                <h3 style="margin-top: 0; color: #4a6baf;">Your Submission Details:</h3>
                <p><strong>Name:</strong> {first_name} {lead_data.get("last_name", "")}</p>
                <p><strong>Email:</strong> <a href="mailto:{email}" style="color: #4a6baf; text-decoration: none;">{email}</a></p>
                <p><strong>Phone:</strong> {lead_data.get("phone", "Not provided")}</p>
                <p><strong>Message:</strong> {lead_data.get("notes", "No additional notes")}</p>
            </div>

            <p>If you have any questions, feel free to reply to this email.</p>

            <p>Best regards,<br>The Alma Team</p>

            <div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #ddd; font-size: 12px; color: #777;">
                <p>This is an automated message. Please do not reply directly to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """.format(email=email, first_name=first_name)

    return send_email(to_emails=[email], subject=subject, html_content=html_content)


async def send_lead_notification(lead_data: Dict, admin_emails: List[str]) -> bool:
    """
    Send email notifications to the lead and admin when a new lead is created.

    Args:
        lead_data: Dictionary containing lead information
        admin_emails: List of admin email addresses to notify

    Returns:
        bool: True if all emails were sent successfully, False otherwise
    """
    logger.info(f"[LEAD NOTIFICATION] Starting notification for lead: {lead_data.get('id')}")

    try:
        # Validate lead data
        if not lead_data or not isinstance(lead_data, dict):
            logger.error("[LEAD NOTIFICATION] Invalid lead_data provided")
            return False

        lead_email = lead_data.get("email")
        first_name = lead_data.get("first_name", "there")

        if not lead_email:
            logger.error("[LEAD NOTIFICATION] No email address provided in lead data")
            return False

        # Get from_email from environment
        from_email = os.getenv("FROM_EMAIL")
        if not from_email:
            logger.error("[EMAIL] FROM_EMAIL not set in environment variables")
            return False

        logger.info(f"[LEAD NOTIFICATION] Sending confirmation to lead: {lead_email}")

        # Prepare lead confirmation email
        lead_subject = "Thank You for Contacting Us!"
        lead_html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #4a6baf;">Thank You, {first_name}!</h2>
                <p>We've received your information and our team will get back to you shortly.</p>

                <div style="margin: 20px 0; padding: 15px; background-color: #e9f0f9; border-radius: 5px;">
                    <h3 style="margin-top: 0; color: #4a6baf;">Your Submission Details:</h3>
                    <p><strong>Name:</strong> {lead_data.get("first_name", "")} {lead_data.get("last_name", "")}</p>
                    <p><strong>Email:</strong> <a href="mailto:{lead_email}" style="color: #4a6baf; text-decoration: none;">{lead_email}</a></p>
                    <p><strong>Phone:</strong> {lead_data.get("phone", "Not provided")}</p>
                    <p><strong>Message:</strong> {lead_data.get("notes", "No additional notes")}</p>
                    <p><strong>Submission Date:</strong> {lead_data.get("created_at", "Unknown")}</p>
                </div>

                <p>If you have any questions, feel free to reply to this email.</p>

                <p>Best regards,<br>The Alma Team</p>

                <div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #ddd; font-size: 12px; color: #777;">
                    <p>This is an automated message. Please do not reply directly to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Send email to the lead
        logger.info("[EMAIL] Sending confirmation email to lead...")
        lead_email_sent = await send_email(
            to_emails=[lead_email],
            subject=lead_subject,
            html_content=lead_html_content,
            from_email=from_email,
        )

        if not lead_email_sent:
            logger.error("[EMAIL] Failed to send confirmation email to lead")
        else:
            logger.info("[EMAIL] Successfully sent confirmation email to lead")

        # Prepare admin notification email
        admin_subject = f"New Lead: {first_name} {lead_data.get('last_name', '')}"
        admin_html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #4a6baf; margin-top: 0;">New Lead Submission</h2>

                <div style="margin: 20px 0; padding: 15px; background-color: #e9f0f9; border-radius: 5px;">
                    <h3 style="margin-top: 0; color: #4a6baf;">Lead Details:</h3>
                    <p><strong>Name:</strong> {lead_data.get("first_name", "")} {lead_data.get("last_name", "")}</p>
                    <p><strong>Email:</strong> <a href="mailto:{lead_email}">{lead_email}</a></p>
                    <p><strong>Phone:</strong> {lead_data.get("phone", "Not provided")}</p>
                    <p><strong>Message:</strong> {lead_data.get("notes", "No additional notes")}</p>
                    <p><strong>Submission Date:</strong> {lead_data.get("created_at", "Unknown")}</p>
                    <p><strong>Lead ID:</strong> {lead_data.get("id", "N/A")}</p>
                </div>

                <p>This lead was submitted through the website contact form.</p>

                <div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #ddd; font-size: 12px; color: #777;">
                    <p>This is an automated notification. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Send notification to admin(s)
        admin_email_sent = True
        if admin_emails:
            logger.info(f"[EMAIL] Sending notification to admin(s): {', '.join(admin_emails)}")
            admin_email_sent = await send_email(
                to_emails=admin_emails,
                subject=admin_subject,
                html_content=admin_html_content,
                from_email=from_email,
            )

            if not admin_email_sent:
                logger.error("[EMAIL] Failed to send notification email to admin(s)")
            else:
                logger.info("[EMAIL] Successfully sent notification email to admin(s)")
        else:
            logger.warning("[EMAIL] No admin emails provided, skipping admin notification")

        result = lead_email_sent and admin_email_sent
        logger.info(f"[LEAD NOTIFICATION] Notification process completed {'successfully' if result else 'with errors'}")
        return result

    except Exception as e:
        error_msg = f"[LEAD NOTIFICATION] Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False
