DIGITAL CATALYST — FINALISED WHATSAPP FLOW

WHAT CHANGED
This package replaces the earlier short-flow main.py. It now starts with experience
selection, then asks for recipient name, recipient phone and message tone. It sends
text first; /img creates the illustrated card, followed by a separate completion
message. HI always begins a fresh session. No Talk to Team, enquiry form, emails,
proactive sends or template requests are in this application.

STEP 1 — KEEP A BACKUP
Download your current GitHub repository ZIP before replacing files.
This is a new release package, not an edit of your live repository by the assistant.

STEP 2 — CREATE THE NEW SUPABASE TABLE
Open Supabase -> project -> SQL Editor -> New query.
Name it: Create Greeting Sessions.
Paste the entire included setup.sql and click Run.
Open Table Editor and confirm greeting_sessions exists.
Do not delete enquiries or greeting_contacts; they hold previous-version records.
Keep RLS enabled. No public access policies are needed.

DATABASE CONTENTS
id: unique greeting session ID. New HI -> new record on experience selection.
sender_whatsapp_number: person speaking to the bot, taken from the incoming webhook.
experience: 1 Wish, 2 Roast, 3 Prediction, 4 Emotional, 5 Future You.
recipient_name: name the human enters for their friend/family member.
recipient_phone: recipient number they enter, with country code; digits only.
tone: 1 Heartfelt, 2 Funny, 3 Inspirational.
status: name -> number -> tone -> generating -> text_ready -> complete.
permission_notice_acknowledged / consent_version: selecting an experience acknowledges
our notice about saving supplied data; this is NOT proof of the recipient's own
consent to marketing. No marketing permission is inferred.
created_at / updated_at: timestamps.

Each answer is saved before the next question is sent. A save failure shows Retry
and does not discard that answer. Repeating a save uses the same session ID and
updates the same row. New sessions are separate rows, even for the same recipient.
The database does not store full generated greetings or image bytes.
'complete' tracks the prepared workflow result; it is not a delivery/read/share receipt.

STEP 3 — UPLOAD THE CODE
Extract this ZIP locally. In GitHub -> your existing repository -> Add file -> Upload files:
- main.py (replace)
- greeting_card.py (replace)
- requirements.txt (replace)
- assets/ folder and everything inside it
- fonts/ folder and everything inside it, including LICENSE.txt
Keep these at the REPOSITORY ROOT. Do not create an extra parent folder.
Do not upload this ZIP itself as your deployment source.
README.txt, FLOW_EXAMPLE.txt and setup.sql are safe to include; they contain no secrets.
Commit changes. No need to put real keys in GitHub.

STEP 4 — RENDER CONFIGURATION
Keep existing environment values:
VERIFY_TOKEN, WHATSAPP_TOKEN, PHONE_NUMBER_ID, META_APP_SECRET, GRAPH_API_VERSION,
GEMINI_API_KEY, GEMINI_MODEL (if already set), SUPABASE_URL, SUPABASE_SECRET_KEY,
BOT_WHATSAPP_NUMBER.
No new key is required.
BOT_WHATSAPP_NUMBER is the actual connected WhatsApp number with country code,
digits only; it controls the invite link. It is NOT the Meta Phone Number ID.
Old RESEND_API_KEY, ALERT_FROM_EMAIL and TEAM_ALERT_EMAIL are unused; you may remove
them after confirming the old email feature is no longer needed.
Build: pip install -r requirements.txt
Start: uvicorn main:app --host 0.0.0.0 --port $PORT
Use one process/instance with this in-memory session implementation.
Wait for deployment to show Live. If automatic deployment is off, deploy latest commit.
Callback URL and verify token remain unchanged; do not reconfigure Meta webhooks.

STEP 5 — META SETTINGS
No template change is required for this user-first flow. Templates do not trigger
themselves. This code allows only text, interactive choices and image messages;
it explicitly blocks a template content type.
Do NOT click Meta's test-panel Send message button to start this flow. That button
sends the selected Meta sample, such as Order Confirmation, separately from your bot.
Custom templates may be archived if your Manager exposes that action, but it is
not necessary. This package does not archive or delete account assets.
Leave the messages webhook subscription enabled.

STEP 6 — LIVE TEST
1. Send HI from your approved personal test number.
2. Choose an experience.
3. Enter a sample recipient name, e.g. Rahul.
4. Enter a number you have permission to use, with country code.
5. Choose Heartfelt / Funny / Inspirational.
6. Expect a short greeting ending: Reply /img to turn this into a greeting card.
7. Send /img. Expect the card first, then the session-complete text.
8. On the card, press and hold -> Forward -> select the friend's chat -> Send.
   On desktop use the image message menu -> Forward.
9. Reply HI. Expect a new experience menu, with previous answers cleared in chat state.
10. In Supabase -> greeting_sessions, check the saved fields and new row per session.

Also test an invalid number: the bot must ask again instead of advancing.
Check a database failure: Retry must preserve the current answer.
Check old question buttons: they must not be saved as names/phone numbers.

SHARING AND PHONE LIMITS
The entered recipient number is for storage only. The bot does not send to it.
Neither a typed number nor generating a card gives permission for future marketing.
There is no custom native Forward button or contact-picker API. The bot asks users
to use WhatsApp's own Forward action; it cannot enforce or detect a private forward.
Completion means card creation finished, not that sharing or recipient delivery was verified.
The actual forwarding target is chosen manually by the human and may differ from
the supplied number. The bot cannot verify the match.
Forwarded-card recipients are not automatically added to the database.
Phone checks validate international digit format, not ownership or WhatsApp registration.
Current Meta test-number recipient restrictions still apply until live-number setup.

TECHNICAL LIMITS
Active conversation state, outbound retry queue and message deduplication are kept
in memory for this single process. Supabase checkpoints survive restarts, but this
version does NOT automatically resume an unfinished chat after a restart. Send HI.
Idle sessions expire after 30 minutes. STOP clears chat state, not previously saved DB rows.
Pending responses retry when the same number sends another message or Meta retries
that message. There is no scheduled retry worker or guaranteed delivery queue.
Card completion is sent only after Meta accepts the image-send request, not after
an image delivery receipt. Duplicate/partial response handling lasts until restart.
No always-on hosting upgrade, rate limits or public launch were performed here.
English text and common Latin-script names are the supported card-font target.

VALIDATION COMPLETED LOCALLY
Simulated 15 experience/tone journeys; database save/retry; name and phone validation;
AI and image-upload failures; image-before-completion order; duplicate message replay;
sender-only outbound delivery; database fields; webhook verification/signature checks.
The live Meta/Gemini/Supabase integration must be checked after your deployment.
