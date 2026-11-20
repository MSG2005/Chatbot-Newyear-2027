SHORT WHATSAPP CARD JOURNEY

1. In Supabase SQL Editor, run the included setup.sql ONCE.
   It creates greeting_contacts with only whatsapp_number and name.
   Phone number is the primary key, so returning users update one contact row.
   Existing enquiries and follow-up data are not changed or deleted.

2. Extract this ZIP. Upload its contents to your existing GitHub repository root:
   main.py, greeting_card.py, requirements.txt, assets/ and fonts/.
   Replace existing versions. Do not upload the ZIP itself.
   README.txt and setup.sql may also be kept in the repository; neither has secrets.

3. Keep existing Meta, Gemini and Supabase environment values in Render.
   BOT_WHATSAPP_NUMBER is the actual WhatsApp number with country code, digits
   only, not the Phone Number ID. It controls the invite link in the caption.
   Resend/TEAM_ALERT variables are no longer used. They can be removed later.
   Start command stays: uvicorn main:app --host 0.0.0.0 --port $PORT
   Keep one process/instance while sessions are in memory.

4. Wait for Render Live. Send HI, enter a first name, choose an experience.
   Choosing explicitly confirms the storage notice shown on that menu.
   Name is used in Gemini generation; phone number is not sent to Gemini.
   Supabase receives only the two contact fields. Greeting stays in memory;
   card media goes to Meta to deliver the image.

5. The result is the illustrated image with a short caption, not a long text
   greeting plus image. Card text now targets 30-45 words.
   All five experiences and two illustrated layouts per theme remain.
   No business/email/city/site/questions, Talk to Team or email alert calls.

SHARING
The caption tells users to tap the forward arrow beside the IMAGE, or select
it and choose Forward. This forwards the real card to chosen WhatsApp chats.
The bot cannot open WhatsApp's native image-forwarding picker with a custom
reply button. /share shows brief instructions and the invite link.
The invite link opens this bot; it does not attach the card automatically.
People receiving forwarded cards are NOT added to the database. They must
message the bot and complete the short consent flow themselves.
The Meta test number is still limited to approved testers; switch
BOT_WHATSAPP_NUMBER and other Meta credentials when connecting a live number.

COMMANDS
HI / MENU / RESTART: begin a new card and ask for name.
/img: alternate layout for the saved greeting; no new AI call if still cached.
/share: forwarding instructions and invite link.
STOP: clear the temporary session; stored contact rows are not deleted.
After inactivity expiry (30 minutes), redeployment or restart, start again.
A customer may generate a card for themselves and forward it to friends.
Database saving happens BEFORE generation. If generation fails afterward,
the contact remains saved and Retry resumes the card journey.

No new API keys. No live WhatsApp number has been connected by this update.
This is a short-flow implementation, not a claim of full production readiness.
Session state and deduplication are in memory. Background tasks are not a
durable queue. Usage limits and privacy/deletion support remain launch work.
Font and illustrated artwork files from the existing card package are included.
Artwork was generated for this project; no image-generation API runs per card.

CHECKED LOCALLY
Five end-to-end simulated flows, consent before save, two-field database payload,
layout cycling, missing-save/generation/upload recovery, forwarding guidance,
webhook verification/signature checks and Python syntax.
After deployment verify actual card delivery and the greeting_contacts table.
