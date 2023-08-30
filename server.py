import os
import telnyx
from fastapi import FastAPI, HTTPException, Request, Depends
from starlette.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field
from urllib.parse import urlparse, urlsplit, urlunsplit
from werkzeug.utils import secure_filename
import json
import requests
from dotenv import load_dotenv
import uvicorn

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class FaxData(BaseModel):
    event_type: str
    direction: str
    fax_id: str
    to: str
    from_: str = Field(alias="from")
    media_url: str

@app.get("/", include_in_schema=False)
async def root():
    return Response(status_code=404)

@app.get("/status")
async def status():
    return {"status": "ONLINE"}

@app.post("/faxes")
@limiter.limit("10/minute")  
async def inbound_message(request: Request):
    try:
        body = await request.json()
        fax_id = body["data"]["payload"]["fax_id"]
        event_type = body["data"]["event_type"]
        direction = body["data"]["payload"]["direction"]
        if event_type != "fax.received" or direction != "inbound":
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
        print(f"An error occurred: {e}")
        return Response(status_code=500)

def download_file(url, save_directory='Faxes'):
    # Checking if the url is valid
    try:
        split_url = list(urlsplit(url))
        split_url[1] = secure_filename(split_url[1])
        url = urlunsplit(split_url)
        r = requests.get(url, allow_redirects=True)
        file_name = secure_filename(os.path.basename(urlparse(url).path)) # secure the filename
        os.makedirs(save_directory, exist_ok=True)
        file_path = os.path.join(save_directory, file_name)
        open(file_path, "wb").write(r.content)
        return file_path
    except Exception as e:
        print(f"An error occurred while downloading the file: {e}")
        return None

if __name__ == "__main__":
    load_dotenv()
    telnyx.api_key = os.getenv("TELNYX_API_KEY")
    telnyx.public_key = os.getenv("TELNYX_PUBLIC_KEY")
    uvicorn.run(app, host='192.168.1.196', port=58000, log_level='info', ssl_keyfile='certs/key.pem', ssl_certfile='certs/cert.pem')
