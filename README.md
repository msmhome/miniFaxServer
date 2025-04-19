# miniFaxServer

<img align="right" width="400" height="400" src="https://i.imgur.com/pCU81k6.png">

[![Ceasefire Now](https://badge.techforpalestine.org/default)](https://techforpalestine.org/learn-more)

A tiny, ready to deploy, simple fax server with SMS recieve running on the Telynx Programmable Fax and SMS APIs. 

This is built around my use case and homelab but is versatile to be deployed as-is for yours or be used in something more complex.
*   **Fax Inbound and Outbound w/ Confirmations**
*   **IP Whitelist with Telnyx IP Ranges by Default**
*   [**Docker Image**](https://github.com/msmhome/miniFaxServer/pkgs/container/minifaxserver/253626966?tag=main) **with Cloudflare Tunnels Built In**
*   **Lightweight, Simple, No Web UI**
*   **HTTPS Support**
*   **PDF Faxes, TXT SMS Files**
*   **Built Asynchronously**

This has not been tested at scale and outside of my at-home use, while it relies on Telnyx to do most of the work, as with all FOSS, no guarantees are made.

# Usage

It's useful to deploy this in a container on a NAS and use a network file share or run locally on Docker with host path directories mounted.

miniFaxServer revolves around the /Faxes directory. Faxes and SMS messages received are dumped there in encoded .pdf or .txt files, respectively. 

Add your own IP ranges to the .env whitelist. The default entries are for Telnyx's servers and should not be changed. Try host 0.0.0.0 if you encounter problems with whitelist due to cloudflared showing internal IPs. 

Endpoints exposed:
*   `/telnyx-webhook` The webhook Telnyx will primarily send fax-related messages to.
*   `/sms` The webhook Telnyx will use for SMS messages.
*   `/status` Will post a `{"status":"ONLINE"}` for uptime monitoring.

#### Fax In
The faxes received will be saved as a PDF in the Faxes directory under the name `Fax_<first_5_chars_telnyx_fax_id>_from_+12015551234_at_<timestamp>.pdf`.

It's recommended to enable the feature to also email faxes in the Telnyx web GUI (it's free).

#### Fax Out
Put any PDF files to be sent out in the Faxes/outbound directory named as the destination phone number, excluding the country code. ie `8885550000.pdf`. This will begin an automatic process to fax that PDF. Once delivered, the PDF will be moved to Faxes/outbound\_confirmations as `Fax_<first_5_chars_telnyx_fax_id>_to_+18005001234_at_<timestamp>_confirmed.pdf`.

(Note: for my use I hardcoded the US +1 country code, modify or remove this in the script as necessary)

#### SMS In
SMS must be configured in the Telnyx webui and the webhook must point /sms. Your inbound texts will be saved in the Faxes directory as `SMS_from_+12015550000_at_timestamp.txt`.

#### [Please submit issues here.](https://github.com/msmhome/miniFaxServer/issues)

## Docker Container

`docker pull ghcr.io/msmhome/minifaxserver:latest`

Pull the prebuilt container image, or just specify `ghcr.io/msmhome/minifaxserver:latest` if using a managed GUI like TrueNAS SCALE or Unraid.

#### Overview of the directories that must be mounted as volumes:

*   `/app/.env (read only)`
*   `/app/certs/ (read only)`
*   `/app/Faxes/`
*   `/app/Faxes/outbound/`
*   `/app/Faxes/outbound_confirmations/`

Also, set the `TUNNEL_TOKEN` environment variable for the container with your Cloudflare Tunnel token.  

### Cloudflare Tunnels (cloudflared)

Cloudflared is built in and recommended instead of an open port. Set `Disable Chunked Encoding` to on. 

It's also recommended to get an origin server certificate and save the certificate and private key to `Faxes/certs/certificate.pem` and `Faxes/certs/key.pem`, respectively. Make sure to set your cloudflare tunnel configuration as HTTPS and set the origin server name.  

## Resources

#### Need to test your fax setup?

Try the [Canon](https://community.usa.canon.com/t5/Desktop-Inkjet-Printers/G7020-FAX/m-p/295192/highlight/true#M17767) Test Fax Service at +1 855-392-2666. This has better uptime than HP's fax test service, and replies faster.

#### [Telnyx Fax Docs](https://developers.telnyx.com/docs/programmable-fax/get-started)
