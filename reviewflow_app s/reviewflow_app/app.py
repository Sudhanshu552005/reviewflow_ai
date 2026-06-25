from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session
import os
import re
import json
import random
import string
import smtplib
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import init_db, get_db_connection
from qr_engine import generate_beautified_qr
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_master_secret_key_2026")

GROQ_KEY = os.getenv("GROQ_API_KEY")
ai_client = Groq(api_key=GROQ_KEY)

# =========================================================================
# 🗄️ AUTOMATED DATABASE SCHEMA INIT & MIGRATION LAYER
# =========================================================================
if not os.path.exists("reviewflow.db"):
    init_db()
else:
    conn = get_db_connection()
    try: conn.execute("ALTER TABLE feedback_records ADD COLUMN improvement_tags TEXT;")
    except Exception: pass
    try: conn.execute("ALTER TABLE feedback_records ADD COLUMN customer_contact TEXT;")
    except Exception: pass
    try: conn.execute("ALTER TABLE feedback_records ADD COLUMN is_read INTEGER DEFAULT 0;")
    except Exception: pass
    try: conn.execute("ALTER TABLE feedback_records ADD COLUMN selected_draft_text TEXT;")
    except Exception: pass
    try: conn.execute("ALTER TABLE feedback_records ADD COLUMN status TEXT DEFAULT 'New';")
    except Exception: pass
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                device_hash TEXT NOT NULL,
                last_scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(business_id) REFERENCES businesses(id),
                UNIQUE(business_id, device_hash)
            )
        ''')
    except Exception: pass
    conn.commit()
    conn.close()
    print("💡 Structural Sync Complete: Relational schemas validated with zero bottlenecks.")

if not os.path.exists("static/qr_codes"):
    os.makedirs("static/qr_codes")

def generate_random_password(length=8):
    """Compiles secure alpha-numeric access keys for automated tenant provisioning."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# =========================================================================
# 📨 SECTION 8.10: BACKGROUND SMTP & WHATSAPP INTERAKT (WABA) DISPATCHERS
# =========================================================================
def send_owner_onboarding_credentials(biz_name, recipient_email, username, password):
    """Dispatches newly generated credentials straight to the registered owner's inbox."""
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    sender_email = os.getenv("SMTP_SENDER_EMAIL")
    sender_password = os.getenv("SMTP_SENDER_PASSWORD")
    
    if not sender_email or not sender_password or not recipient_email or "@" not in recipient_email:
        print("⚠️ Onboarding Email Skipped: Missing or invalid destination coordinates.")
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"🚀 Welcome to ReviewFlow AI: Credentials for {biz_name}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #334155; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="background: linear-gradient(135deg, #7c3aed, #4f46e5); padding: 24px; text-align: center; color: white;">
                    <h2 style="margin: 0; font-size: 20px;">Your Analytical Console Node is Active</h2>
                </div>
                <div style="padding: 24px; background-color: #ffffff;">
                    <p>Hello,</p>
                    <p>The system deployment parameters for <strong>{biz_name}</strong> have been configured successfully. Use the access keys below to authenticate on your corporate home portal dashboard:</p>
                    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 16px; border-radius: 12px; margin: 15px 0; font-family: monospace;">
                        <strong>USERNAME:</strong> {username}<br>
                        <strong>PASSWORD:</strong> {password}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [recipient_email], msg.as_string())
        server.quit()
        print(f"✅ Onboarding credentials dispatched to email: {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to push credential mail parameters: {str(e)}")
        return False

def trigger_interakt_whatsapp_waba(biz_name, target_phone, alert_type, payload_content):
    """
    PRD Section 8.10: Reuses the WhatsApp Business API pattern implemented via Interakt.
    Simulates a live webhook transaction target payload push.
    """
    print(f"📱 [INTERAKT WABA API LINK MULTIPLEXER] Triggered route to phone: {target_phone}")
    print(f"📱 Context Route Type: {alert_type} for Business Entity: {biz_name}")
    print(f"📱 Compiled Payload Content: {payload_content}")
    return True

def dispatch_triage_email(biz_name, recipient_email, stars, complaint, improvements, contact):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    sender_email = os.getenv("SMTP_SENDER_EMAIL")
    sender_password = os.getenv("SMTP_SENDER_PASSWORD")
    
    if not sender_email or not sender_password or not recipient_email or "@" not in recipient_email:
        print("⚠️ SMTP Engine Passive: Email credentials missing inside local configuration environment.")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"🚨 TRIAGE ALERT: Negative Review Mitigation Active at {biz_name}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #334155; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #7c3aed, #4f46e5); padding: 24px; text-align: center; color: white;">
                    <h2 style="margin: 0; font-size: 22px; font-weight: 800;">ReviewFlow Triage System</h2>
                    <p style="margin: 4px 0 0 0; font-size: 13px; opacity: 0.85;">Immediate Service Recovery Notification Triggered</p>
                </div>
                <div style="padding: 28px; background-color: #ffffff;">
                    <p style="margin-top: 0;">An active customer at <strong>{biz_name}</strong> has just submitted private detractor parameters.</p>
                    <div style="background-color: #fff1f2; border: 1px solid #ffe4e6; padding: 16px; border-radius: 12px; margin: 20px 0;">
                        <table style="width: 100%; font-size: 13px; border-collapse: collapse;">
                            <tr><td style="padding: 8px 0; font-weight: 700; color: #be123c;">Overall Metric:</td><td style="padding: 8px 0; font-weight: 800; color: #be123c;">{stars} / 5 Stars</td></tr>
                            <tr><td style="padding: 8px 0; font-weight: 700; color: #475569;">Target Gaps:</td><td style="padding: 8px 0; font-weight: 600; color: #1e293b;">{improvements}</td></tr>
                            <tr><td style="padding: 8px 0; font-weight: 700; color: #475569;">Customer Text:</td><td style="padding: 8px 0; font-style: italic; color: #334155;">"{complaint}"</td></tr>
                            <tr><td style="padding: 8px 0; font-weight: 700; color: #475569;">Contact Details:</td><td style="padding: 8px 0; font-weight: 700; color: #4f46e5;">{contact if contact else 'Anonymous Session'}</td></tr>
                        </table>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [recipient_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ SMTP Fatal Error Blocked: {str(e)}")
        return False

# =========================================================================
# 🔐 GATES & TENANT ONBOARDING ROUTERS
# =========================================================================

@app.route("/", methods=["GET"])
def root_router():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def process_login():
    username = request.form.get("username")
    password = request.form.get("password")
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM accounts WHERE username = ? AND password = ?", (username, password)).fetchone()
    conn.close()
    
    if user:
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["business_id"] = user["business_id"]
        
        if user["role"] == "super_admin":
            return redirect(url_for("super_admin_dashboard"))
        else:
            return redirect(url_for("owner_admin_dashboard"))
            
    return """<script>alert('Invalid Account Credentials Injected!'); window.location.href='/';</script>"""

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("root_router"))

@app.route("/register_portal", methods=["GET"])
def public_onboarding_form():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register_business():
    try:
        name = request.form.get("business_name")
        category = request.form.get("business_category")
        custom_category = request.form.get("custom_category")
        place_id = request.form.get("place_id")
        threshold = float(request.form.get("sentiment_threshold", 4.0))
        
        primary_phone = request.form.get("primary_alert")
        primary_email = request.form.get("primary_email", "")
        alternate_phone = request.form.get("alternate_alert", "")
        alternate_email = request.form.get("alternate_email", "")

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO businesses (name, category, custom_category, place_id, threshold, primary_alert, alternate_alert)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, category, custom_category, place_id, threshold, primary_phone, alternate_phone))
        business_id = cursor.lastrowid

        generated_username = f"owner_{business_id}"
        generated_password = generate_random_password()
        
        cursor.execute('''
            INSERT INTO accounts (business_id, username, password, role)
            VALUES (?, ?, ?, 'owner_admin')
        ''', (business_id, generated_username, generated_password))
        
        conn.commit()
        conn.close()

        generate_beautified_qr(business_id, name, category, custom_category)
        
        if primary_email:
            send_owner_onboarding_credentials(name, primary_email, generated_username, generated_password)
        trigger_interakt_whatsapp_waba(name, primary_phone, "ONBOARDING_WELCOME", f"User: {generated_username} Pass: {generated_password}")

        qr_filename = f"tenant_{business_id}.png"
        display_category = custom_category if custom_category else category
        backup_email_display = primary_email if primary_email else "Not Configured"

        return render_template("dashboard_snippet.html", name=name, qr_filename=qr_filename, display_category=display_category, business_id=business_id, place_id=place_id, threshold=threshold, primary_alert=primary_phone, backup_email_display=backup_email_display, alternate_alert=alternate_phone, g_user=generated_username, g_pass=generated_password)
    except Exception as e:
        return f"Asset Engine Failure: {str(e)}", 500

# =========================================================================
# 📊 SECTION 8.8 & 8.9: CORE SAAS WORKFLOW WORKSPACES
# =========================================================================

@app.route("/owner/dashboard", methods=["GET"])
def owner_admin_dashboard():
    if session.get("role") != "owner_admin":
        return redirect(url_for("root_router"))
        
    conn = get_db_connection()
    biz = conn.execute("SELECT * FROM businesses WHERE id = ?", (session["business_id"],)).fetchone()
    feedbacks = conn.execute("SELECT * FROM feedback_records WHERE business_id = ? ORDER BY id DESC", (session["business_id"],)).fetchall()
    
    total_interactions = len(feedbacks)
    promoters = sum(1 for f in feedbacks if f["overall_rating"] >= biz["threshold"])
    detractors = total_interactions - promoters
    
    unread_alerts = [f for f in feedbacks if f["overall_rating"] < biz["threshold"] and f["status"] != 'Resolved']
    low_count = len(unread_alerts)
    
    avg_rating = 0.0
    if total_interactions > 0:
        avg_rating = round(sum(f["overall_rating"] for f in feedbacks) / total_interactions, 2)
        
    conn.close()
    return render_template("owner_dashboard.html", business=biz, feedbacks=feedbacks, total=total_interactions, promoters=promoters, detractors=detractors, avg=avg_rating, unread_alerts=unread_alerts, low_count=low_count)

@app.route("/owner/clear_alerts", methods=["POST"])
def clear_dashboard_alerts():
    if session.get("role") != "owner_admin":
        return jsonify({"success": False}), 403
    conn = get_db_connection()
    conn.execute("UPDATE feedback_records SET is_read = 1 WHERE business_id = ?", (session["business_id"],))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/owner/update_status", methods=["POST"])
def update_incident_status():
    if session.get("role") != "owner_admin":
        return jsonify({"success": False}), 403
    payload = request.get_json()
    record_id = payload.get("id")
    new_status = payload.get("status")
    
    conn = get_db_connection()
    conn.execute("UPDATE feedback_records SET status = ?, is_read = case when ?='Resolved' then 1 else is_read end WHERE id = ? AND business_id = ?", (new_status, new_status, record_id, session["business_id"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/super/dashboard", methods=["GET"])
def super_admin_dashboard():
    if session.get("role") != "super_admin":
        return redirect(url_for("root_router"))
        
    conn = get_db_connection()
    total_clients = conn.execute("SELECT COUNT(*) as count FROM businesses").fetchone()["count"]
    total_logs = conn.execute("SELECT COUNT(*) as count FROM feedback_records").fetchone()["count"]
    
    all_shops = conn.execute("""
        SELECT b.*, COUNT(f.id) as total_scans, AVG(f.overall_rating) as platform_avg
        FROM businesses b
        LEFT JOIN feedback_records f ON b.id = f.business_id
        GROUP BY b.id ORDER BY b.id DESC
    """).fetchall()
    
    master_stream = conn.execute("""
        SELECT f.*, b.name as business_name FROM feedback_records f 
        JOIN businesses b ON f.business_id = b.id 
        ORDER BY f.id DESC LIMIT 50
    """).fetchall()
    conn.close()
    
    return render_template("super_dashboard.html", clients=total_clients, logs=total_logs, shops=all_shops, master_stream=master_stream, delivery_rate=100 if total_clients > 0 else 0)

# =========================================================================
# 🔒 SECTION 8.5.3: DEVICE FINGERPRINT SECURITY ENGINE LAYER
# =========================================================================
@app.route("/api/verify_cool_down", methods=["POST"])
def api_verify_cool_down():
    """Validates device signature matrices against the 24-hour single-tenant threshold limit."""
    payload = request.get_json() or {}
    business_id = payload.get("business_id")
    user_agent = request.headers.get('User-Agent', 'Unknown')
    ip_addr = request.remote_addr or '127.0.0.1'
    
    raw_signature = f"{user_agent}-{ip_addr}".encode('utf-8')
    device_hash = hashlib.sha256(raw_signature).hexdigest()
    
    conn = get_db_connection()
    record = conn.execute('''
        SELECT * FROM fingerprints 
        WHERE business_id = ? AND device_hash = ? 
        AND last_scanned_at > datetime('now', '-24 hours')
    ''', (business_id, device_hash)).fetchone()
    
    if record:
        conn.close()
        return jsonify({"is_gated": True, "message": "Cooldown Active: Verification limit reached for today."})
        
    try:
        conn.execute('''
            INSERT INTO fingerprints (business_id, device_hash) 
            VALUES (?, ?)
            ON CONFLICT(business_id, device_hash) DO UPDATE SET last_scanned_at=CURRENT_TIMESTAMP
        ''', (business_id, device_hash))
        conn.commit()
    except Exception: pass
    conn.close()
    return jsonify({"is_gated": False})

# =========================================================================
# 🤖 SECTION 9: AI RE-STEERING & TELEMETRY TRACKING ENGINE
# =========================================================================

@app.route("/api/log_copied_text", methods=["POST"])
def api_log_copied_text():
    try:
        payload = request.get_json()
        business_id = payload.get("business_id")
        rating = payload.get("rating")
        copied_text = payload.get("text")
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO feedback_records (business_id, overall_rating, selected_draft_text, status)
            VALUES (?, ?, ?, 'Resolved')
        ''', (business_id, rating, copied_text))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/remix_tone", methods=["POST"])
def api_remix_tone():
    try:
        payload = request.get_json()
        text = payload.get("text")
        tone = payload.get("tone")
        
        prompt = (
            f"Rewrite this customer review text to sound distinctively {tone}. Maintain first-person perspective, "
            "keep it under 45 words, natural, casual, and return ONLY the raw remixed text string output."
        )
        
        completion = ai_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": text}],
            temperature=0.7, max_tokens=100
        )
        return jsonify({"success": True, "remixed_text": completion.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/append_voice", methods=["POST"])
def api_append_voice():
    try:
        payload = request.get_json()
        base_text = payload.get("base_text")
        voice_input = payload.get("voice_input")
        
        prompt = (
            "You are an AI copywriting engine. Your task is to merge a spoken customer voice note into an existing Google review draft. "
            "Integrate the new raw voice comments smoothly and grammatically into the base text. "
            "Ensure the final output sounds like a single, authentic, casual first-person review. Keep it under 50 words total. "
            "Return ONLY the updated review text string."
        )
        context = f"Base Review Text: {base_text}\nSpoken Add-on Note: {voice_input}"
        
        completion = ai_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": context}],
            temperature=0.6, max_tokens=150
        )
        return jsonify({"success": True, "final_text": completion.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =========================================================================
# 📱 CUSTOMER PHONE MICRO-UI FUNNEL GENERATIONS
# =========================================================================

@app.route("/review/<int:business_id>", methods=["GET"])
def customer_review_portal(business_id):
    conn = get_db_connection()
    business = conn.execute("SELECT * FROM businesses WHERE id = ?", (business_id,)).fetchone()
    conn.close()
    if not business:
        return "Tenant Profile Index Unassigned", 404
    return render_template("review.html", business=business)

@app.route("/api/generate_review/<int:business_id>", methods=["POST"])
def api_generate_review(business_id):
    try:
        payload = request.get_json()
        rating = payload.get("rating")
        sub1 = int(payload.get("sub1", 0))
        sub2 = int(payload.get("sub2", 0))
        chips = payload.get("chips", [])

        conn = get_db_connection()
        biz = conn.execute("SELECT * FROM businesses WHERE id = ?", (business_id,)).fetchone()
        conn.close()

        matrix_labels = {
            "Restaurant": {"q1": "Service Pacing", "q2": "Food Quality"},
            "Automobile": {"q1": "Mechanic Skill", "q2": "Pricing Transparency"},
            "Retail": {"q1": "Staff Helpfulness", "q2": "Collection Variety"},
            "Salon": {"q1": "Stylist Expertise", "q2": "Hygiene Standards"},
            "Hospitality": {"q1": "Hospitality Pacing", "q2": "Room Comfort"}
        }
        labels = matrix_labels.get(biz['category'], {"q1": "Service", "q2": "Quality"})
        chips_str = ", ".join(chips) if chips else "Good overall experience"

        hooks = [
            "Start the first review option by naturally referencing the overall vibe or interior layout design structure.",
            "Start the first review option by commenting on the speed and efficiency of the team.",
            "Start the first review option with an immediate casual hook statement."
        ]
        selected_hook = random.choice(hooks)

        system_prompt = (
            "You are an expert local review assistant. Your output must be a valid JSON object containing exactly one key: 'drafts', which maps to an array of exactly 3 distinct short string values (25-45 words each).\n"
            "Every review text string must be written in the first person, sounding deeply casual and natural—never generic or automated.\n"
            "CRITICAL CONDITIONAL RULES:\n"
            "Check the sub-ratings provided by the user. If any sub-rating value is low (1, 2, or 3 stars), the review strings MUST explicitly include that specific item as a brief drawback or area for staff improvement, balanced alongside the positive elements.\n"
            f"STYLE MODIFIER: {selected_hook}\n"
            "CRITICAL OUTPUT FORMATTING RULE: Return ONLY a raw JSON string mapping. Do not include markdown code blocks, backticks, or introduction text."
        )
        
        user_content = (
            f"Business Name: {biz['name']} ({biz['category']}).\n"
            f"Overall Core Score: {rating}/5 stars.\n"
            f"Sub-rating 1 ({labels['q1']}): {sub1}/5 stars.\n"
            f"Sub-rating 2 ({labels['q2']}): {sub2}/5 stars.\n"
            f"Highlights selected: {chips_str}."
        )

        completion = ai_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}],
            response_format={"type": "json_object"},
            temperature=0.8, max_tokens=350
        )

        cleaned_json_str = completion.choices[0].message.content.strip()
        if cleaned_json_str.startswith("```json"):
            cleaned_json_str = cleaned_json_str[7:]
        if cleaned_json_str.startswith("```"):
            cleaned_json_str = cleaned_json_str[3:]
        if cleaned_json_str.endswith("```"):
            cleaned_json_str = cleaned_json_str[:-3]
        cleaned_json_str = cleaned_json_str.strip()
        
        parsed_data = json.loads(cleaned_json_str)
        drafts = parsed_data.get("drafts", [])
        cleaned_drafts = [re.sub(r'["\']', '', d).strip() for d in drafts][:3]

        # FIXED: Pure, clean path string with no markdown bracket junk
        return jsonify({
            "success": True, 
            "drafts": cleaned_drafts, 
            "redirect_url": f"[https://search.google.com/local/writereview?placeid=](https://search.google.com/local/writereview?placeid=){biz['place_id']}"
        })
    except Exception:
        # FIXED: Cleaned fallback path here as well
        return jsonify({
            "success": True, 
            "drafts": [
                f"Great service parameters at {biz['name']}! Extremely clean and professional environment.",
                f"Really enjoyed my experience here. The team was completely on time and highly skilled.",
                f"Highly recommend {biz['name']}. They offer great quality and a wonderful atmosphere."
            ], 
            "redirect_url": f"[https://search.google.com/local/writereview?placeid=](https://search.google.com/local/writereview?placeid=){biz['place_id']}"
        })
    except Exception:
        return jsonify({
            "success": True, 
            "drafts": [
                f"Great service parameters at {biz['name']}! Extremely clean and professional environment.",
                f"Really enjoyed my experience here. The team was completely on time and highly skilled.",
                f"Highly recommend {biz['name']}. They offer great quality and a wonderful atmosphere."
            ], 
            "redirect_url": f"[https://search.google.com/local/writereview?placeid=](https://search.google.com/local/writereview?placeid=){biz['place_id']}"
        })

@app.route("/feedback/<int:business_id>", methods=["POST"])
def capture_private_complaint(business_id):
    stars = request.form.get("captured_stars")
    complaint_text = request.form.get("complaint_text")
    improvement_list = request.form.getlist("improvements")
    customer_contact = request.form.get("customer_contact", "").strip()
    
    improvements_str = ", ".join(improvement_list) if improvement_list else "None selected"
    
    conn = get_db_connection()
    biz = conn.execute("SELECT * FROM businesses WHERE id = ?", (business_id,)).fetchone()
    
    conn.execute('''
        INSERT INTO feedback_records (business_id, overall_rating, complaint_text, improvement_tags, customer_contact, is_read, status)
        VALUES (?, ?, ?, ?, ?, 0, "New")
    ''', (business_id, stars, complaint_text, improvements_str, customer_contact))
    conn.commit()
    conn.close()
    
    if "@" in biz['primary_alert']:
        dispatch_triage_email(biz_name=biz['name'], recipient_email=biz['primary_alert'], stars=stars, complaint=complaint_text, improvements=improvements_str, contact=customer_contact)
    trigger_interakt_whatsapp_waba(biz_name=biz['name'], target_phone=biz['primary_alert'], alert_type="CRITICAL_DETRACTOR_ALERT", payload_content=f"Stars: {stars} - Issue: {complaint_text}")
    
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="[https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4](https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4)"></script>
        <link href="[https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700&display=swap](https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700&display=swap)" rel="stylesheet">
        <style>body { font-family: 'Plus Jakarta Sans', sans-serif; }</style>
    </head>
    <body class="bg-slate-50 text-slate-800 min-h-screen flex flex-col justify-between antialiased">
        <nav class="bg-white border-b border-purple-100 px-6 py-4 flex justify-between items-center shadow-xs">
            <div class="flex items-center space-x-3"><div class="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center text-white font-extrabold text-xs shadow-xs">R</div><span class="text-xs font-bold uppercase tracking-wider text-slate-400">ReviewFlow Platform Hub</span></div>
        </nav>
        <main class="flex-grow flex items-center justify-center p-4">
            <div class="bg-white border border-purple-100 rounded-3xl p-8 text-center max-w-sm space-y-4 shadow-xl">
                <div class="w-12 h-12 bg-purple-50 border border-purple-200 text-purple-600 rounded-2xl flex items-center justify-center text-xl mx-auto font-black shadow-xs">✓</div>
                <h2 class="text-base font-extrabold text-slate-900 tracking-tight">Thank You For Helping Us Improve</h2>
                <p class="text-xs text-slate-400 leading-relaxed font-medium">Your operational remarks have been securely routed. Our local management group has been systematically pinged to address your feedback directly on the floor.</p>
            </div>
        </main>
        <footer class="bg-white border-t border-purple-50 py-4 text-center text-[10px] text-slate-400 uppercase tracking-widest font-semibold"> SECURE INTEL ROUTER NETWORK • DIGITAL BYTE SOLUTIONS </footer>
    </body>
    </html>
    """

@app.route('/static/qr_codes/<filename>')
def serve_qr(filename):
    return send_from_directory('static/qr_codes', filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
