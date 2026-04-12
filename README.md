# miniFaxServer
![GitHub branch check runs](https://img.shields.io/github/check-runs/msmhome/miniFaxServer/main?label=build)
[![Ceasefire Now](https://badge.techforpalestine.org/default)](https://techforpalestine.org/learn-more)

<img align="right" width="500" height="500" src="https://i.imgur.com/pCU81k6.png">
A tiny, ready to deploy, simple fax server with SMS receive running on the Telnyx Programmable Fax and SMS APIs. 

This is built around my use case and homelab but is versatile to be deployed as-is for yours or be used in something more complex.

### Features
*   **Fax Inbound and Outbound w/ Confirmations**
*   **IP Whitelist with Telnyx IP Ranges by Default**
*   [**Docker Image**](https://github.com/msmhome/miniFaxServer/pkgs/container/minifaxserver) **with Cloudflare Tunnels Built In**
*   **Relies on Filesystem, Simple, No Web UI**
*   **HTTPS Support**
*   **PDF Faxes in/out, Inbound SMS TXT Files**
*   **Built Asynchronously**

### Architecture Overview

- Incoming webhooks from Telnyx → saved to filesystem  
- Outbound faxes → file watcher → API call to Telnyx  
- Cloudflare Tunnel → exposes service securely  
- No database; filesystem acts as queue + storage  

This has not been tested at scale and outside of my at-home use, and while it relies on Telnyx to do most of the work, as with all FOSS, no guarantees are made.

# Usage

It's useful to deploy this in a container on a NAS and use a network file share or run locally on Docker with host path directories mounted.

miniFaxServer revolves around the /Faxes directory. Faxes and SMS messages received are dumped there in encoded .pdf or .txt files, respectively. 

The default entries are for Telnyx's servers and should not be changed. 

Endpoints exposed:
*   `/telnyx-webhook` The webhook Telnyx will primarily send fax-related messages to.
*   `/sms` The webhook Telnyx will use for SMS messages.
*   `/status` Will post a `{"status":"ONLINE"}` for uptime monitoring.
***
#### Fax In
The faxes received will be saved as a PDF in the Faxes directory under the name `Fax_<first_5_chars_faxid>_from__12015551234_at_<timestamp>.pdf`.

It's recommended to enable the feature to also email faxes in the Telnyx web GUI (it's free).

#### Fax Out
Put any PDF files to be sent out in the Faxes/outbound directory named as the destination phone number, excluding the country code. ie `8885550000.pdf`. This will begin an automatic process to fax that PDF. Once delivered, the PDF will be moved to Faxes/outbound\_confirmations as `Fax_<first_5_chars_faxid>_to_+18005001234_at_<timestamp>_confirmed.pdf`.

(Note: for my use I hardcoded the US +1 country code, modify this in the script as necessary)

#### SMS In
SMS must be configured in the Telnyx portal and the webhook must point /sms. Your inbound texts will be saved in the Faxes directory as `SMS_from_+12015550000_at_timestamp.txt`.

## Installation
### Docker Container

Save [.env.example](https://raw.githubusercontent.com/msmhome/miniFaxServer/refs/heads/main/.env.example) as .env and edit values.

Create `Faxes/`, `Faxes/outbound`, `Faxes/outbound_confirmations` and `certs/` if using origin certificates

```bash
docker run -d \
  -v /your/path/Faxes:/app/Faxes \
  -v /your/path/certs/key.pem:/app/certs/key.pem:ro \
  -v /your/path/certs/cert.pem:/app/certs/cert.pem:ro \
  -v /your/path/.env:/app/.env:ro \
  -p 8080:8080 \
  ghcr.io/msmhome/minifaxserver:latest
```

Pull the prebuilt container image, or just specify `ghcr.io/msmhome/minifaxserver:latest` if using a managed GUI like TrueNAS SCALE or Unraid.
***

### Standard Python Install

```bash
git clone https://github.com/msmhome/miniFaxServer.git
cd miniFaxServer

cp .env.example .env
# Edit .env with your values

python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate.bat  # Windows

pip install -r requirements.txt
```

Run with
```bash
python server.py
```

#### [Please submit issues here.](https://github.com/msmhome/miniFaxServer/issues)

## Configuration

Copy `.env.example` to `.env` or load these environment values another way, then fill in the values.

| Variable                 | Required     | Note                                                                 |
| ------------------------ | ------------ | -------------------------------------------------------------------- |
| TELNYX_PUBLIC_KEY        | Yes          |                                                                      |
| TELNYX_API_KEY           | Yes          |                                                                      |
| TELNYX_FAX_CONNECTION_ID | Yes          | Fax API App ID (from Telnyx portal)                                  |
| TELNYX_FAX_FROM_NUMBER   | Yes          | Your Telnyx outbound fax number (format: +12015551234)               |
| MEDIA_BASE_URL           | Yes          | Base URL for serving outbound PDFs (e.g. https://example.com/static) |
| HOST                     | Yes          | Host to bind the server to (e.g. 127.0.0.1)                          |
| PORT                     | Yes          | Port to bind the server to                                           |
| MESSAGE_PROFILE_ID       | if using SMS | Telnyx Messaging Profile ID for inbound SMS                          |
| WHITELISTED_IP_RANGES    | No           | JSON array of allowed CIDR ranges; defaulted to [Telnyx's IP ranges](https://support.telnyx.com/en/articles/1130687-whitelisting-telnyx-ip-addresses)|
| TUNNEL_TOKEN             | Yes          | Cloudflared Tunnel Token                                             |
| LOG_LEVEL                | No           | `INFO` set by default, `ERROR` & `DEBUG` available                   |

***
#### Directories that must be mounted as volumes:

*   `/app/.env (read only)`
*   `/app/certs/ (read only)`
*   `/app/Faxes/`
*   `/app/Faxes/outbound/`
*   `/app/Faxes/outbound_confirmations/`

***
### TELNYX_FAX_CONNECTION_ID

This is the Application ID for your Telnyx Fax API Application.

**Steps to configure:**

1. Log in to the [Telnyx Portal](https://portal.telnyx.com).
2. Navigate to **Programmable Voice → Fax API Applications**.
3. Click **Create New Application** and complete the setup form.
4. Copy the **Application ID** (a numeric value) from the application details page and set it as `TELNYX_FAX_CONNECTION_ID` in your `.env` file.

**Set an Outbound Voice Profile for the application:**

1. In the Telnyx Portal, go to **Real-Time Communication → Voice → Settings → Outbound Voice Profile**.
2. Click **Create** and configure a new outbound voice profile.
3. Return to **Programmable Voice → Fax API Applications**, open your application, and assign the outbound voice profile you just created.

**Configure the webhook:**

Set the Fax API Application's webhook URL to:
```
https://[HOST]/telnyx-webhook
```
***

### MESSAGE_PROFILE_ID

This is the Profile ID for your Telnyx Programmable Messaging profile.

**Steps to configure:**

1. Log in to the [Telnyx Portal](https://portal.telnyx.com).
2. Navigate to **Real-Time Communication → Messaging → Programmable Messaging**.
3. Click **Add New Profile**.
4. In the profile settings, set the **Webhook URL** to:
   ```
   https://[HOST]/sms
   ```
5. Save the profile, then copy the **Profile ID** and set it as `MESSAGE_PROFILE_ID` in your `.env` file.
***

### Cloudflare Tunnels (cloudflared)

Set the `TUNNEL_TOKEN` environment variable for the container with your Cloudflare Tunnel token.  

Cloudflared is built in and recommended instead of an open port. Set `Disable Chunked Encoding` to on. 

It's also recommended to get an origin server certificate and save the certificate and private key to `certs/certificate.pem` and `certs/key.pem`, respectively. Make sure to set your cloudflare tunnel configuration as HTTPS and set the origin server name.  


# Resources

### Need to test your fax setup?
Try the [Canon](https://community.usa.canon.com/t5/Desktop-Inkjet-Printers/G7020-FAX/m-p/295192/highlight/true#M17767) Test Fax Service at +1 855-392-2666. This has better uptime than HP's fax test service, and replies faster.

### [Telnyx Fax Docs](https://developers.telnyx.com/docs/programmable-fax/get-started)
