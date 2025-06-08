# BittyNews/utils/email_utils.py
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

def send_email_via_brevo(recipient_email: str, subject: str, html_content: str) -> bool:
    """
    Sends an email using the Brevo (Sendinblue) API.

    Args:
        recipient_email (str): The email address of the recipient.
        subject (str): The subject of the email.
        html_content (str): The HTML content of the email.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("NEWSLETTER_SENDER_EMAIL") # Email verified in Brevo

    if not api_key:
        print("ERROR email_utils: BREVO_API_KEY not found in environment.")
        return False
    if not sender_email:
        print("ERROR email_utils: NEWSLETTER_SENDER_EMAIL not found in environment.")
        return False
    if not recipient_email:
        print("ERROR email_utils: Recipient email not provided.")
        return False

    # Configure API key authorization: api-key
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    # Create an instance of the API class
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    sender_name = os.getenv("NEWSLETTER_SENDER_NAME", "BittyNews Digest") # Optional sender name

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": recipient_email}], # Must be a list of recipient objects
        sender={"email": sender_email, "name": sender_name},
        subject=subject,
        html_content=html_content
        # You can also add 'textContent' for a plain text version
        # text_content="This is the plain text version for BittyNews." 
    )

    try:
        print(f"DEBUG email_utils: Attempting to send email to {recipient_email} with subject '{subject}' via Brevo...")
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"DEBUG email_utils: Brevo API response: {api_response}")
        print(f"✅ Email sent successfully to {recipient_email} via Brevo!")
        return True
    except ApiException as e:
        print(f"❌ ERROR email_utils: Brevo API Exception when calling SMTPApi->send_transac_email: {e}")
        # Brevo API errors often have a 'body' attribute with more details if it's a JSON response
        try:
            error_body = json.loads(e.body)
            print(f"   Error details: {error_body}")
        except:
            pass # e.body might not be JSON
        return False
    except Exception as e_gen:
        print(f"❌ ERROR email_utils: Unexpected error sending email via Brevo: {e_gen}")
        return False

if __name__ == '__main__':
    print("--- Testing email_utils.py (Brevo Sender) ---")
    # Ensure .env is loaded for this direct test if you haven't loaded it globally
    from dotenv import load_dotenv
    dotenv_path_test = os.path.join(os.path.dirname(__file__), '..', '.env')
    if load_dotenv(dotenv_path_test):
        print(f"DEBUG email_utils_test: .env loaded from {dotenv_path_test}")
    else:
        print(f"DEBUG email_utils_test: .env not found at {dotenv_path_test}, ensure environment variables are set.")


    recipient = os.getenv("NEWSLETTER_RECIPIENT_EMAIL")
    sender = os.getenv("NEWSLETTER_SENDER_EMAIL")

    if not recipient or not sender or not os.getenv("BREVO_API_KEY"):
        print("\nERROR: Missing BREVO_API_KEY, NEWSLETTER_SENDER_EMAIL, or NEWSLETTER_RECIPIENT_EMAIL in .env for testing.")
        print("--- Test Aborted ---")
    else:
        print(f"Attempting to send a test email from {sender} to {recipient}...")
        test_subject = "BittyNews - Brevo Test Email"
        test_html_body = """
        <h1>Hello from BittyNews!</h1>
        <p>This is a test email sent via Brevo using the Python SDK.</p>
        <p>If you received this, the setup is working!</p>
        <p>Cheers,<br>BittyNews Bot</p>
        """
        if send_email_via_brevo(recipient, test_subject, test_html_body):
            print("Test email function reported success. Please check your inbox (and spam folder).")
        else:
            print("Test email function reported failure. Check error messages above.")
    print("--- Test Complete ---")
