WHATSAPP GREETING CARD UPDATE

Extract this ZIP. Upload the contents to your existing GitHub repository root:
- main.py (replace existing)
- greeting_card.py (new)
- requirements.txt (replace existing)
- fonts/ folder (all files, including LICENSE.txt)
Do not upload the ZIP itself to the repository.

No new environment variables or SQL changes are required.
Keep existing Meta, Gemini, Supabase and Resend environment variables.
Render start command stays: uvicorn main:app --host 0.0.0.0 --port $PORT

Wait for Render to show Live. Generate a NEW greeting, then send /img.
The previous deployment's temporary session does not survive redeployment.
The card is a 1080 x 1350 JPEG with a teal, cream and gold design.
Each of the five experiences uses its own card heading.
Decorative emoji are omitted on the card; the WhatsApp text stays unchanged.
Bundled fonts suit English messages and common Latin-script names.

/img works from any conversation stage without advancing the active question.
It uses the latest successful greeting for that number in the current session.
Main Menu preserves the greeting. Stop clears it.
Inactivity expiry (30 minutes) and server restarts clear temporary greetings.
Without a saved greeting, the bot asks the customer to create one first.
Rendering/upload errors preserve the greeting so /img can be retried.

This update retains the existing seven-question enquiry flow and email alerts.
It does not implement the separately discussed shorter enquiry flow,
persistent sessions or hosting upgrade.
No additional image-generation API key is needed. Hosting and WhatsApp usage
terms still apply. Media is uploaded to Meta for WhatsApp delivery.

Local checks: command routing, missing greeting, state preservation, media
upload payload, upload failure, word wrapping, long-text fitting and JPEG size.
Existing save, alert, enquiry and webhook functions were checked unchanged.
Live image delivery must be tested after deployment.
