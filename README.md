# miniFaxServer (WIP V2 Branch)

<img align="right" width="400" height="400" src="https://i.imgur.com/pCU81k6.png">

A tiny, ready to deploy, simple fax and SMS recieve server running on the Telynx Programmable Fax and SMS APIs. 

This is built around my use case and homelab but is versatile to be deployed as-is for yours or be used in something more complex. This has not been tested at scale and outside of my personal at-home use, while it relies on Telnyx to do most of the work, as with all FOSS, no guarantees are made.

*   **Fax Inbound and Outbound w/ Confirmations**
*   **IP Whitelist With Telnyx IP Ranges by Default**
*   [**Docker Image**](https://github.com/msmhome/miniFaxServer/pkgs/container/minifaxserver/252967649?tag=main) **with Cloudflare Tunnel (cloudflared)**
*   **Lightweight, 50-60MB RAM Usage; Simple, No Web UI**
*   **HTTPS Support**
*   **PDF Faxes, TXT SMS Files**
*   **Built Asynchronously**

# Usage

It's useful to deploy this in a container on a NAS and use a network file share, or run on docker desktop with host path directories mounted.

miniFaxServer revolves around the /Faxes directory. Faxes and SMS messages recieved are dumped there in encoded .pdf or .txt files respectively. 

Add your own IP ranges in the .env whitelist, the default entries are for Telnyx's servers and should not be changed. Try host 0.0.0.0 if you encounter problems with whitelist.

#### Fax In

Faxes recieved will be saved as a PDF in the Faxes directory with the name `from_+12015550000_telnyx-delivery-webhook-id.pdf`.

It is recommended to enable the feature to email faxes in the telnyx web gui (it's free).

#### Fax Out

Put any PDF files to be sent out in the Faxes/outbound directory named as the destination phone number excluding the country code. ie `8885550000.pdf`. This will begin an automatic process to fax that PDF, once delivered, the PDF will be moved to Faxes/outbound\_confirmations as `+18885550000_telnyx-delivery-webhook-id_confirmed.pdf`.

(note for my use I hard coded the US +1 country code, modify or remove this in the script as necessary)

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

Also set the `TUNNEL_TOKEN` environment variable for the container with your Cloudflare Tunnel token.  

### Cloudflare Tunnel (cloudflared)

Cloudflared is built in and recommended instead of an open port. Enable `Disable Chunked Encoding`. 

It's also recommended to get an origin server certificate, save the certificate and private key to `Faxes/certs/certificate.pem` and `Faxes/certs/key.pem` respectively. Make sure to set your cloudflare tunnel configuration as HTTPS and set the origin server name.  

## Resources

#### Need to test your fax set up?

Try the [Canon](https://community.usa.canon.com/t5/Desktop-Inkjet-Printers/G7020-FAX/m-p/295192/highlight/true#M17767) Test Fax Service at +1 855-392-2666. This has better uptime than HP's fax test service, and replies faster.

#### [Telnyx Fax Docs](https://developers.telnyx.com/docs/programmable-fax/get-started)
