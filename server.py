import os
import requests
from urllib.parse import urlparse, urlsplit, urlunsplit
from werkzeug.utils import secure_filename
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from fastapi import FastAPI, HTTPException, Request, Depends
from starlette.responses import Response
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field
import telnyx
from dotenv import load_dotenv
import uvicorn
import bleach
import json
import logging
import shutil
import ipaddress

#TODO: Append phone number and timestamp to inbound and outbound final fax PDF files. similar to SMS

# Initialize FastAPI with rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.mount("/static/outbound", StaticFiles(directory="Faxes/outbound"), name="static") # mount outbound faxes directory to webserver

# Configure logging
#TODO: Add debug logging level, make it put all HTTP requests in/out raw
#TODO: Standardize logging messages, include timestamp, type, direction, phone numbers, and file. 
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

# Read and process whitelisted IP ranges from environment variable
WHITELISTED_IP_RANGES_STR = os.getenv('WHITELISTED_IP_RANGES')
if WHITELISTED_IP_RANGES_STR is None:
    raise ValueError("WHITELISTED_IP_RANGES environment variable is not set")
try:
    # Ensure the string is correctly formatted for JSON
    WHITELISTED_IP_RANGES_STR = WHITELISTED_IP_RANGES_STR.strip().replace("'", '"')
    ip_ranges = json.loads(WHITELISTED_IP_RANGES_STR)
    WHITELISTED_IP_RANGES = []
    for ip in ip_ranges:
        try:
            WHITELISTED_IP_RANGES.append(ipaddress.ip_network(ip))
        except ValueError as e:
            print(f"[ERROR]:Invalid IP range '{ip}' skipped: {e}")
    print(f"Parsed Whitelisted IP ranges: {WHITELISTED_IP_RANGES}")
    logging.debug(f"Parsed WHITELISTED_IP_RANGES: {WHITELISTED_IP_RANGES}")

except ipaddress.AddressValueError as e:
    logging.debug(f"Unable to properly read whitelisted IP ranges. Are they set in environment and in proper JSON? {e}")
    raise ValueError(f"Error decoding WHITELISTED_IP_RANGES: {e}")

except json.JSONDecodeError as e:
    logging.debug(f"Unable to properly read whitelisted IP ranges. Are they set in environment and in proper JSON? {e}")
    raise ValueError(f"Error decoding WHITELISTED_IP_RANGES: {e}")

def is_whitelisted(ip):
    ip_address = ipaddress.ip_address(ip)
    return any(ip_address in network for network in WHITELISTED_IP_RANGES)

@app.middleware("http")
async def whitelist_middleware(request: Request, call_next):
    client_ip = request.client.host
    if not is_whitelisted(client_ip):
        return Response(status_code=403, content="Forbidden")
    response = await call_next(request)
    return response

# Formatting for Fax In
class FaxData(BaseModel):
    event_type: str
    direction: str
    fax_id: str
    to: str
    from_: str = Field(alias="from")
    media_url: str

#Formatting for SMS In
def sanitize_and_store(message: str, from_number: str, directory="Faxes"):
    sanitized_message = bleach.clean(message, strip=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')  # Using microseconds for uniqueness
    file_name = f"SMS_from_{from_number}_at_{timestamp}.txt"
    os.makedirs(directory, exist_ok=True)  # Ensure the directory exists

    file_path = os.path.join(directory, file_name)
    with open(file_path, "w") as file:
        file.write(sanitized_message)

    return sanitized_message

class SmsData(BaseModel):
    data: dict

#Sanitize and format Fax In File
def download_file(url, save_directory='Faxes'):
    # Checking if the url is valid
    try:
        split_url = list(urlsplit(url))
        split_url[1] = secure_filename(split_url[1])
        url = urlunsplit(split_url)
        url = url.replace("%2B", "+")
        r = requests.get(url, allow_redirects=True, timeout=30)
        file_name = secure_filename(os.path.basename(urlparse(url).path)) # secure the filename
        os.makedirs(save_directory, exist_ok=True)
        file_path = os.path.join(save_directory, file_name)
        open(file_path, "wb").write(r.content)
        return file_path
    except Exception as e:
        print(f"An error occurred while downloading the file: {e}")
        return None


@app.get("/", include_in_schema=False)
# Block all root connections
async def root():
    return Response(status_code=404)

# For uptime monitoring
@app.get("/status")
async def status():
    return {"status": "ONLINE"}

@app.post("/sms")
async def handle_sms(data: SmsData):
    try:
        message = data.data.get('payload').get('text')
        from_number = data.data.get('payload').get('from').get('phone_number')
        sanitized_message = sanitize_and_store(message, from_number)
        print(f"Received an SMS from {from_number}: {sanitized_message}")
        logging.debug(f"Received an SMS from {from_number}: {'message.payload'}")
        return Response(status_code=200)
    except KeyError:
        print("Incorrect data format received.")
        return Response(status_code=400)
    except Exception as e:
        print(f"An error occurred: {e}")
        return Response(status_code=500)

@app.post("/telnyx-webhook")
@limiter.limit("100/minute")
async def inbound_message(request: Request):
    try:
        body = await request.json()
        # fax_id = body["payload"]["fax_id"]
        fax_id = body["data"]["payload"]["fax_id"]
        # event_type = body.get("event_type")
        event_type = body["data"]["event_type"]
        direction = body["data"]["payload"]["direction"]

        if event_type == "fax.delivered":
            faxed_to = body["data"]["payload"]["to"]
            print(f"Received delivery confirmation for fax ID: {fax_id}")
            # Call on_confirmed with the fax_id received from the webhook
            event_handler.on_confirmed(faxed_to, fax_id)
        elif event_type == "fax.failed":
            failure_reason = body["payload"].get("failure_reason")
            print(f"Fax failed with reason: {failure_reason}")
            # Handle the failure case as needed
        else:
            print(f"Unhandled event type: {event_type}")

        if event_type != "fax.received" or direction != "inbound":
            failure_reason = body["data"]["payload"].get("failure_reason")
            if failure_reason:
                print(f"Fax failed due to: {failure_reason}")
            print(f"Received fax event_type: {event_type} to {direction} fax_id: {fax_id}")
            return Response(status_code=200)
        to_number = body["data"]["payload"]["to"]
        from_number = body["data"]["payload"]["from"]
        media_url = body["data"]["payload"]["media_url"]
        attachment = download_file(media_url)
        if attachment is None:
            print(f"Failed to download fax with id: {fax_id} from {from_number} to {to_number}")
            return Response(status_code=500)
        print(f"Downloaded fax with id: {fax_id} from {from_number} to {to_number}")
        return Response(status_code=200)
    except KeyError:
        print("Incorrect data format received.")
        return Response(status_code=400)
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return Response(status_code=500)
    

class FaxEventHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.fax_id_to_file = {}

    def on_created(self, event):
        print(f"Event detected: {event}")
        if event.is_directory:
            return
        if event.event_type == 'created' and event.src_path.endswith('.pdf'):
            self.process_fax(event.src_path)

    def process_fax(self, file_path):
        print(f"Processing fax for file: {file_path}")
        file_name = os.path.basename(file_path)
        fax_number = os.path.splitext(file_name)[0]  # Extract fax number from file name
        self.send_fax(file_path, fax_number)

    def send_fax(self, file_path, fax_number, on_success_callback=None):
        print(f"Sending fax to {fax_number} for file: {file_path}")
        file_name = os.path.basename(file_path)
        media_url = f"{os.getenv('MEDIA_BASE_URL')}/outbound/{file_name}"
        payload = {
            "connection_id": os.getenv("TELNYX_FAX_CONNECTION_ID"),
            "from": os.getenv("TELNYX_FAX_FROM_NUMBER"),
            "media_url": media_url,
            "monochrome": False,
            "t38_enabled": True,
            "to": "+1" + fax_number
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('TELNYX_API_KEY')}"
        }

        url = "https://api.telnyx.com/v2/faxes"
        response = requests.post(url, json=payload, headers=headers, timeout=900) # change timeout value if you have larger faxes def. 15 minutes

        print(f"Fax send response: {response.status_code}, {response.content}")
        if response.status_code in [200, 202]:
            data = response.json()
            confirmation_number = data['data']['id']
            new_file_path = os.path.join('Faxes', 'outbound_confirmations', f"{confirmation_number}.pdf")
            os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
            # Store the mapping of fax_id to file_name
            self.fax_id_to_file[confirmation_number] = file_name
            # Execute the callback with the confirmation number
            if on_success_callback:
                on_success_callback(confirmation_number)
            # Don't move the file yet, wait for confirmation
            print(f"Fax sent successfully: {data}")
        else:
            print(f"Failed to send fax: {response.content}")

    def on_confirmed(self, faxed_to, confirmation_number):
        print(f"On confirmed called for confirmation number: {confirmation_number}")
        # Retrieve the original file name using the fax_id
        original_file_name = self.fax_id_to_file.get(confirmation_number)
        if not original_file_name:
            print(f"No mapping found for confirmation number: {confirmation_number}")
            return
        file_path = os.path.join('Faxes/outbound', original_file_name)
        new_file_name = f"{faxed_to}_{confirmation_number}_confirmed.pdf"
        new_file_path = os.path.join('Faxes', 'outbound_confirmations', new_file_name)
        try:
            shutil.move(file_path, new_file_path)
            print(f"Moved confirmed fax to {new_file_path}")
        except Exception as e:
            print(f"Failed to move file for fax {confirmation_number}: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    telnyx.api_key = os.getenv("TELNYX_API_KEY")
    telnyx.public_key = os.getenv("TELNYX_PUBLIC_KEY")

    # Set up the observer for the FaxEventHandler
    path = "Faxes/outbound"
    global event_handler
    event_handler = FaxEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    # Start the FastAPI app
    uvicorn.run(app, host=str(os.getenv("HOST")), port=int(os.getenv("PORT")), log_level='info', ssl_keyfile='certs/key.pem', ssl_certfile='certs/cert.pem')