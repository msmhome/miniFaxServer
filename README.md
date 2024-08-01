# miniFaxServer

VERSION 2 WIP BRANCH

A tiny, ready to deploy, simple Python fax send/recieve and SMS receive server running using Telynx Programmable Fax API.

# Usuage 
miniFaxServer revolves around the /Faxes directory. Faxes and SMS messages recieved are dumped there in encoded .pdf or .txt files respectively. It's useful to deploy this on a NAS and use a network file share, or run on docker desktop with a host path directory mounted.  

Recommended to be deployed through a cloudflare tunnel. 

Add your own IP ranges in the .env whitelist, the default entries are for Telnyx's servers and should not be changed. 

## Fax In
Faxes recieved will be saved as a PDF in the Faxes directory with the name 'from_+12015550000_telnyx-delivery-webhook-id.pdf`

It is recommended to enable the feature to email faxes in the telnyx web gui (it is free).

## Fax Out
Put any PDF files to be sent out in the Faxes/outbound directory named as the destination phone number excluding the country code. ie 8885550000.pdf. This will begin an automatic process to fax that PDF, once delivered, the PDF will be moved to Faxes/outbound_confirmations as '+18885550000_telnyx-delivery-webhook-id_confirmed.pdf'.    

(note for my use I hard coded the US +1 country code, modify or remove this in the code as necessary)

## SMS In
SMS must be configured in the Telnyx webui and the webhook must point /sms. Your inbound texts will be saved in the Faxes directory as SMS_from_+12015550000_at_timestamp.txt



Need to test your fax set up? 
Try the Canon Test Fax Service at +18553922666 (https://community.usa.canon.com/t5/Desktop-Inkjet-Printers/G7020-FAX/m-p/295192/highlight/true#M17767). This has better uptime than HP's fax test service, and replies faster. 

Telnyx Fax Docs https://developers.telnyx.com/docs/programmable-fax/get-started

