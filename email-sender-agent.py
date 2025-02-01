# import boto3
from crewai import Agent, Task, Crew
from crewai.utilities.paths import db_storage_path
from crewai.tools import tool
from download_invoice import S3Downloader
import os
import boto3

bedrock_client = boto3.client('bedrock', region_name='us-east-1')

bucket_name = os.environ['BUCKET_NAME']
APP_PASSWORD = os.environ['EMAIL_APP_PASSWORD']
sender_email = os.environ['SENDER_EMAIL_ADDRESS']
BEDROCK_MODEL_NAME = os.environ['BEDROCK_MODEL_NAME']
RECIPIENT_EMAIL_ADDRESS = os.environ['RECIPIENT_EMAIL_ADDRESS']

@tool("send_email")
def send_email(to: str, subject: str, body: str) -> str:
    
    """
    Sends an email with the given subject, body, and an optional attachment.
    
    Args:
        to (str): Recipient email address.
        subject (str): Email subject line.
        body (str): Main content of the email.
        attachment (str, optional): Path to the attachment file. Defaults to None.

    Returns:
        str: Confirmation message of email sent.
    """
    
    import smtplib ## smtplib is inbuit to Python... we don't need to install it. 
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from datetime import datetime
    from email import encoders
    import os
    
    # Email Configuration
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    EMAIL = sender_email
    PASSWORD = APP_PASSWORD
    
    # # Recipient Details
    TO_EMAIL = to

    current_month = datetime.now().strftime("%B")
    subject = f"{current_month} {subject}"
    
    body = body
    
    # Set up the email
    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    print("Calling Function To Download Invoice from S3 Bucket")
    filepath = f'/tmp/{current_month}-rent.pdf'
    key_name = f'{current_month}-rent.pdf'
    print("filepath:", filepath)
    print("key_name:", key_name)
    
    path = "/tmp"
    dir_list = os.listdir(path)
    print("Files and directories in '", path, "' :")
    # prints all files
    print(dir_list)
    
    
    # Example usage:
    downloader = S3Downloader()
    downloader.download_object(bucket_name, key_name, filepath)
    
    pdfname = filepath

    # open the file in bynary
    binary_pdf = open(pdfname, 'rb')
    
    payload = MIMEBase('application', 'octate-stream', Name=key_name)
    payload.set_payload((binary_pdf).read())
    
    # enconding the binary into base64
    encoders.encode_base64(payload)
    
    # add header with pdf name
    payload.add_header('Content-Decomposition', 'attachment', filename=pdfname)
    msg.attach(payload)
   
    # Connect and send email
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
        server.quit()
        return "Email sent successfully!"
    except Exception as e:
        return f"Error sending email: {e}"


def handler(event, context):
    ##Defining Agent Role
    # Create an agent with all available parameters
    
    email_writer = Agent(
        role="Email Writer",
        goal="You will Draft an email to Santhosh from Payables with Invoice to claim monthly rent",
        backstory="A professional communicator with profound knowledge and expertise in drafting clear, precise and concise emails with out any gramatical errors.",
        llm=BEDROCK_MODEL_NAME,
        verbose=True
    )

    # Define the task
    email_task = Task(
        description=(
            "Draft an email to santhosh regarding monthly invoice rent."
            f"The email should be sent to the following to address: {RECIPIENT_EMAIL_ADDRESS}\n"
            "The Subject should be : Month Rent Invoice - Action Required:\n"
            "The Body Should meet the following criteria: \n"
            "- A polite and formal message to forward the Invoice to finance team.\n"
            "- Include a message that will let him know that he can come back to for changes anytime .\n"
            "- A thank-you note for the hard work.\n"
            "- Thanks, Best Regards from Pavan Kumar.P"
        ),
        agent=email_writer,
        tools=[send_email], # Link the email-sending function to the task,
        expected_output="An email with Clear and concise details",
        verbose=True
    )

    # Form a crew (even though it's just one agent)
    crew = Crew(
        agents=[email_writer],
        tasks=[email_task],
        verbose=True
    )
    
    try: 
        # Run the crew
        crew.kickoff()
        return {
            "statusCode": 200,
            "message": "Crew Co-oridated successfully to send an email"
        }
    except Exception as e:
        return {
            "statusCode": 1,
            "message": f"Crew Failed to co-ordinate to send an email, The error is as follows : {e}"
        }
