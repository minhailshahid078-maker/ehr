



# # added nobese dashboard

# from flask import Flask, request, session, redirect, url_for, jsonify
# from urllib.parse import urlencode
# import requests
# from dotenv import load_dotenv
# import os
# import base64
# from datetime import datetime, timezone
# import logging

# load_dotenv()

# # Logging setup
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = Flask(__name__)
# app.secret_key = os.getenv("SECRET_KEY", "fallback_secret")

# CLIENT_ID    = os.getenv("CLIENT_ID")
# CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# REDIRECT_URI = os.getenv("REDIRECT_URI")
# FHIR_URL     = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"


# # --- ERROR HANDLERS ---
# @app.errorhandler(404)
# def not_found(e):
#     return "<h2>❌ 404 — Page not found</h2><a href='/'>Home</a>", 404

# @app.errorhandler(500)
# def server_error(e):
#     logger.error(f"Server error: {e}")
#     return "<h2>❌ Server Error — Check logs</h2><a href='/'>Home</a>", 500


# # --- HOME ---
# @app.route("/")
# def home():
#     return "<h2>✅ EHR Launch Server Running!</h2>"


# # --- STEP 1: EPIC LAUNCH ---
# @app.route("/epic/launch")
# def epic_launch():
#     try:
#         iss    = request.args.get("iss")
#         launch = request.args.get("launch")

#         if not iss or not launch:
#             logger.error(f"Missing iss or launch: iss={iss}, launch={launch}")
#             return "<h2>❌ Missing iss or launch parameter</h2>", 400

#         session['iss']    = iss
#         session['launch'] = launch

#         params = {
#             "response_type": "code",
#             "client_id":     CLIENT_ID,
#             "redirect_uri":  REDIRECT_URI,
#             "scope":         "launch openid fhirUser patient/Patient.read patient/Observation.read patient/Condition.read patient/MedicationRequest.read patient/DocumentReference.write",
#             "launch":        launch,
#             "aud":           iss,
#         }

#         if "smarthealthit" in str(iss):
#             auth_url = "https://launch.smarthealthit.org/v/r4/auth/authorize"
#         else:
#             auth_url = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize"

#         logger.info(f"Launching with iss={iss}")
#         return redirect(auth_url + "?" + urlencode(params))

#     except Exception as e:
#         logger.error(f"Launch error: {e}")
#         return f"<h2>❌ Launch Error: {str(e)}</h2>", 500


# # --- STEP 2: CALLBACK ---
# @app.route("/callback")
# def callback():
#     try:
#         code = request.args.get("code")
#         iss  = session.get('iss')

#         if not code:
#             return "<h2>❌ No code received from Epic</h2>", 400

#         if not iss:
#             return "<h2>❌ Session expired — please relaunch</h2>", 400

#         if "smarthealthit" in str(iss):
#             token_url = "https://launch.smarthealthit.org/v/r4/auth/token"
#             fhir_base = iss
#         else:
#             token_url = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
#             fhir_base = FHIR_URL

#         r = requests.post(token_url, data={
#             "grant_type":   "authorization_code",
#             "code":         code,
#             "redirect_uri": REDIRECT_URI,
#             "client_id":    CLIENT_ID
#         }, timeout=10)

#         data = r.json()

#         if "access_token" in data:
#             session['token']      = data['access_token']
#             session['patient_id'] = data.get('patient')
#             session['fhir_base']  = fhir_base
#             logger.info(f"Token received for patient: {data.get('patient')}")
#             return redirect(url_for('dashboard'))

#         logger.error(f"Token error: {data}")
#         return f"<h2>❌ Login Failed</h2><pre>{data}</pre>", 401

#     except requests.exceptions.Timeout:
#         return "<h2>❌ Epic server timeout — try again</h2>", 504
#     except Exception as e:
#         logger.error(f"Callback error: {e}")
#         return f"<h2>❌ Callback Error: {str(e)}</h2>", 500


# # --- STEP 3: DASHBOARD ---
# @app.route("/dashboard")
# def dashboard():
#     try:
#         token      = session.get('token')
#         patient_id = session.get('patient_id')
#         fhir_base  = session.get('fhir_base', FHIR_URL)

#         if not token:
#             return redirect(url_for('home'))

#         if not patient_id:
#             return "<h2>❌ No patient ID in session</h2>", 400

#         headers = {
#             "Authorization": f"Bearer {token}",
#             "Accept":        "application/fhir+json"
#         }

#         # Patient Info
#         full_name = dob = gender = "N/A"
#         try:
#             p         = requests.get(
#                 f"{fhir_base}/Patient/{patient_id}",
#                 headers=headers, timeout=10
#             ).json()
#             name      = p.get('name', [{}])[0]
#             full_name = f"{name.get('given', [''])[0]} {name.get('family', '')}"
#             dob       = p.get('birthDate', 'N/A')
#             gender    = p.get('gender', 'N/A').capitalize()
#         except Exception as e:
#             logger.error(f"Patient fetch error: {e}")

#         # Weight & BMI
#         weight = bmi = "N/A"
#         try:
#             obs = requests.get(
#                 f"{fhir_base}/Observation?patient={patient_id}&category=vital-signs",
#                 headers=headers, timeout=10
#             ).json()
#             for entry in obs.get('entry', []):
#                 res  = entry.get('resource', {})
#                 code = res.get('code', {}).get('coding', [{}])[0].get('code', '')
#                 val  = res.get('valueQuantity', {})
#                 if code == '29463-7':
#                     weight = f"{val.get('value', 'N/A')} {val.get('unit', '')}"
#                 if code == '39156-5':
#                     bmi = f"{val.get('value', 'N/A')}"
#         except Exception as e:
#             logger.error(f"Observation fetch error: {e}")

#         # Conditions
#         conditions = []
#         try:
#             cond = requests.get(
#                 f"{fhir_base}/Condition?patient={patient_id}",
#                 headers=headers, timeout=10
#             ).json()
#             for entry in cond.get('entry', []):
#                 conditions.append(
#                     entry.get('resource', {}).get('code', {}).get('text', 'Unknown')
#                 )
#         except Exception as e:
#             logger.error(f"Condition fetch error: {e}")

#         # Medications
#         medications = []
#         try:
#             meds = requests.get(
#                 f"{fhir_base}/MedicationRequest?patient={patient_id}",
#                 headers=headers, timeout=10
#             ).json()
#             for entry in meds.get('entry', []):
#                 medications.append(
#                     entry.get('resource', {}).get('medicationCodeableConcept', {}).get('text', 'Unknown')
#                 )
#         except Exception as e:
#             logger.error(f"Medication fetch error: {e}")

#         cond_list = "".join([f"<li>{c}</li>" for c in conditions]) or "<li>None found</li>"
#         med_list  = "".join([f"<li>{m}</li>" for m in medications]) or "<li>None found</li>"

#         return f"""
#         <div style="max-width:900px; margin:auto; font-family:sans-serif; padding:20px;">
#             <h2 style="color:#007bff; border-bottom:3px solid #007bff; padding-bottom:10px;">
#                 🏥 Nobese Patient Dashboard
#             </h2>
#             <div style="background:#f1f8ff; padding:20px; border-radius:10px; margin-bottom:20px;">
#                 <h3 style="margin:0; color:#0056b3;">{full_name}</h3>
#                 <p><b>DOB:</b> {dob} | <b>Gender:</b> {gender}</p>
#                 <p><b>Patient ID:</b> {patient_id}</p>
#             </div>
#             <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:20px;">
#                 <div style="background:#fff3cd; padding:15px; border-radius:10px;">
#                     <h4>⚖️ Weight</h4>
#                     <p style="font-size:24px; font-weight:bold;">{weight}</p>
#                 </div>
#                 <div style="background:#d4edda; padding:15px; border-radius:10px;">
#                     <h4>📊 BMI</h4>
#                     <p style="font-size:24px; font-weight:bold;">{bmi}</p>
#                 </div>
#             </div>
#             <div style="background:#fff; border:1px solid #dee2e6; padding:20px; border-radius:10px; margin-bottom:20px;">
#                 <h4>🩺 Conditions</h4>
#                 <ul>{cond_list}</ul>
#             </div>
#             <div style="background:#fff; border:1px solid #dee2e6; padding:20px; border-radius:10px; margin-bottom:20px;">
#                 <h4>💊 Medications</h4>
#                 <ul>{med_list}</ul>
#             </div>
#             <div style="background:#d4edda; padding:20px; border-radius:10px;">
#                 <h4>📝 Write Note to Epic</h4>
#                 <form action="/push_note" method="POST">
#                     <input type="hidden" name="p_id" value="{patient_id}">
#                     <textarea name="note_text" style="width:98%; height:80px; margin-bottom:10px;">Clinical Note - Nobese Visit</textarea>
#                     <button type="submit" style="width:100%; padding:15px; background:#28a745; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">
#                         PUSH NOTE TO EPIC ✅
#                     </button>
#                 </form>
#             </div>
#         </div>
#         """

#     except Exception as e:
#         logger.error(f"Dashboard error: {e}")
#         return f"<h2>❌ Dashboard Error: {str(e)}</h2>", 500


# # --- STEP 4: PUSH NOTE ---
# @app.route("/push_note", methods=['POST'])
# def push_note():
#     try:
#         token     = session.get('token')
#         fhir_base = session.get('fhir_base', FHIR_URL)
#         p_id      = request.form.get('p_id')
#         note_text = request.form.get('note_text')

#         if not token:
#             return "<h2>❌ Session expired</h2>", 401
#         if not p_id or not note_text:
#             return "<h2>❌ Missing patient ID or note</h2>", 400

#         now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

#         headers = {
#             "Authorization": f"Bearer {token}",
#             "Content-Type":  "application/fhir+json"
#         }

#         payload = {
#             "resourceType": "DocumentReference",
#             "status":       "current",
#             "docStatus":    "final",
#             "type": {"coding": [{"system": "http://loinc.org", "code": "11488-4"}]},
#             "subject":  {"reference": f"Patient/{p_id}"},
#             "date":     now,
#             "content": [{"attachment": {
#                 "contentType": "text/plain",
#                 "data": base64.b64encode(note_text.encode()).decode()
#             }}]
#         }

#         res = requests.post(
#             f"{fhir_base}/DocumentReference",
#             json=payload,
#             headers=headers,
#             timeout=10
#         )

#         if res.status_code == 201:
#             logger.info(f"Note pushed for patient {p_id}")
#             return f"""
#             <div style='text-align:center; padding:50px;'>
#                 <h1>✅ Note Successfully Pushed to Epic!</h1>
#                 <a href='/dashboard'>← Back to Dashboard</a>
#             </div>
#             """

#         logger.error(f"Note push failed: {res.status_code} {res.text}")
#         return f"<h2>❌ Error {res.status_code}</h2><pre>{res.text}</pre>", res.status_code

#     except requests.exceptions.Timeout:
#         return "<h2>❌ Epic server timeout</h2>", 504
#     except Exception as e:
#         logger.error(f"Push note error: {e}")
#         return f"<h2>❌ Note Error: {str(e)}</h2>", 500


# if __name__ == "__main__":
#     app.run(port=5001, debug=True)




from flask import Flask, request, session, redirect, url_for, jsonify
from urllib.parse import urlencode
import requests
from dotenv import load_dotenv
import os
import base64
from datetime import datetime, timezone
import logging

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret")

CLIENT_ID    = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
FHIR_URL     = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"


# --- ERROR HANDLERS ---
@app.errorhandler(404)
def not_found(e):
    return "<h2>❌ 404 — Page not found</h2><a href='/'>Home</a>", 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return "<h2>❌ Server Error — Check logs</h2><a href='/'>Home</a>", 500


# --- HOME ---
@app.route("/")
def home():
    return "<h2>✅ EHR Launch Server Running!</h2>"


# --- STEP 1: EPIC LAUNCH ---
@app.route("/epic/launch")
def epic_launch():
    try:
        iss    = request.args.get("iss")
        launch = request.args.get("launch")

        if not iss or not launch:
            logger.error(f"Missing iss or launch: iss={iss}, launch={launch}")
            return "<h2>❌ Missing iss or launch parameter</h2>", 400

        session['iss']    = iss
        session['launch'] = launch

        params = {
            "response_type": "code",
            "client_id":     CLIENT_ID,
            "redirect_uri":  REDIRECT_URI,
            "scope":         "launch openid fhirUser patient/Patient.read patient/Observation.read patient/Condition.read patient/MedicationRequest.read patient/DocumentReference.write",
            "launch":        launch,
            "aud":           iss,
        }

        if "smarthealthit" in str(iss):
            auth_url = "https://launch.smarthealthit.org/v/r4/auth/authorize"
        else:
            auth_url = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize"

        logger.info(f"Launching with iss={iss}")
        return redirect(auth_url + "?" + urlencode(params))

    except Exception as e:
        logger.error(f"Launch error: {e}")
        return f"<h2>❌ Launch Error: {str(e)}</h2>", 500


# --- STEP 2: CALLBACK ---
@app.route("/callback")
def callback():
    try:
        code = request.args.get("code")
        iss  = session.get('iss')

        if not code:
            return "<h2>❌ No code received from Epic</h2>", 400

        if not iss:
            return "<h2>❌ Session expired — please relaunch</h2>", 400

        if "smarthealthit" in str(iss):
            token_url = "https://launch.smarthealthit.org/v/r4/auth/token"
            fhir_base = iss
        else:
            token_url = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
            fhir_base = FHIR_URL

        r = requests.post(token_url, data={
            "grant_type":   "authorization_code",
            "code":         code,
            "redirect_uri": REDIRECT_URI,
            "client_id":    CLIENT_ID
        }, timeout=10)

        data = r.json()

        if "access_token" in data:
            session['token']      = data['access_token']
            session['patient_id'] = data.get('patient')
            session['fhir_base']  = fhir_base
            logger.info(f"Token received for patient: {data.get('patient')}")
            return redirect(url_for('dashboard'))

        logger.error(f"Token error: {data}")
        return f"<h2>❌ Login Failed</h2><pre>{data}</pre>", 401

    except requests.exceptions.Timeout:
        return "<h2>❌ Epic server timeout — try again</h2>", 504
    except Exception as e:
        logger.error(f"Callback error: {e}")
        return f"<h2>❌ Callback Error: {str(e)}</h2>", 500


# --- STEP 3: DASHBOARD ---
@app.route("/dashboard")
def dashboard():
    try:
        token      = session.get('token')
        patient_id = session.get('patient_id')
        fhir_base  = session.get('fhir_base', FHIR_URL)

        if not token:
            return redirect(url_for('home'))

        if not patient_id:
            return "<h2>❌ No patient ID in session</h2>", 400

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept":        "application/fhir+json"
        }

        # Patient Info
        full_name = dob = gender = "N/A"
        try:
            p         = requests.get(
                f"{fhir_base}/Patient/{patient_id}",
                headers=headers, timeout=10
            ).json()
            name      = p.get('name', [{}])[0]
            full_name = f"{name.get('given', [''])[0]} {name.get('family', '')}"
            dob       = p.get('birthDate', 'N/A')
            gender    = p.get('gender', 'N/A').capitalize()
        except Exception as e:
            logger.error(f"Patient fetch error: {e}")

        # Weight & BMI
        weight = bmi = "N/A"
        try:
            obs = requests.get(
                f"{fhir_base}/Observation?patient={patient_id}&category=vital-signs",
                headers=headers, timeout=10
            ).json()
            for entry in obs.get('entry', []):
                res  = entry.get('resource', {})
                code = res.get('code', {}).get('coding', [{}])[0].get('code', '')
                val  = res.get('valueQuantity', {})
                if code == '29463-7':
                    weight = f"{val.get('value', 'N/A')} {val.get('unit', '')}"
                if code == '39156-5':
                    bmi = f"{val.get('value', 'N/A')}"
        except Exception as e:
            logger.error(f"Observation fetch error: {e}")

        # Conditions
        conditions = []
        try:
            cond = requests.get(
                f"{fhir_base}/Condition?patient={patient_id}",
                headers=headers, timeout=10
            ).json()
            for entry in cond.get('entry', []):
                conditions.append(
                    entry.get('resource', {}).get('code', {}).get('text', 'Unknown')
                )
        except Exception as e:
            logger.error(f"Condition fetch error: {e}")

        # Medications
        medications = []
        try:
            meds = requests.get(
                f"{fhir_base}/MedicationRequest?patient={patient_id}",
                headers=headers, timeout=10
            ).json()
            for entry in meds.get('entry', []):
                medications.append(
                    entry.get('resource', {}).get('medicationCodeableConcept', {}).get('text', 'Unknown')
                )
        except Exception as e:
            logger.error(f"Medication fetch error: {e}")

        cond_list = "".join([f"<li>{c}</li>" for c in conditions]) or "<li>None found</li>"
        med_list  = "".join([f"<li>{m}</li>" for m in medications]) or "<li>None found</li>"

        return f"""
        <div style="max-width:900px; margin:auto; font-family:sans-serif; padding:20px;">
            <h2 style="color:#007bff; border-bottom:3px solid #007bff; padding-bottom:10px;">
                🏥 Nobese Patient Dashboard
            </h2>
            <div style="background:#f1f8ff; padding:20px; border-radius:10px; margin-bottom:20px;">
                <h3 style="margin:0; color:#0056b3;">{full_name}</h3>
                <p><b>DOB:</b> {dob} | <b>Gender:</b> {gender}</p>
                <p><b>Patient ID:</b> {patient_id}</p>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:20px;">
                <div style="background:#fff3cd; padding:15px; border-radius:10px;">
                    <h4>⚖️ Weight</h4>
                    <p style="font-size:24px; font-weight:bold;">{weight}</p>
                </div>
                <div style="background:#d4edda; padding:15px; border-radius:10px;">
                    <h4>📊 BMI</h4>
                    <p style="font-size:24px; font-weight:bold;">{bmi}</p>
                </div>
            </div>
            <div style="background:#fff; border:1px solid #dee2e6; padding:20px; border-radius:10px; margin-bottom:20px;">
                <h4>🩺 Conditions</h4>
                <ul>{cond_list}</ul>
            </div>
            <div style="background:#fff; border:1px solid #dee2e6; padding:20px; border-radius:10px; margin-bottom:20px;">
                <h4>💊 Medications</h4>
                <ul>{med_list}</ul>
            </div>
            <div style="background:#d4edda; padding:20px; border-radius:10px;">
                <h4>📝 Write Note to Epic</h4>
                <form action="/push_note" method="POST">
                    <input type="hidden" name="p_id" value="{patient_id}">
                    <textarea name="note_text" style="width:98%; height:80px; margin-bottom:10px;">Clinical Note - Nobese Visit</textarea>
                    <button type="submit" style="width:100%; padding:15px; background:#28a745; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">
                        PUSH NOTE TO EPIC ✅
                    </button>
                </form>
            </div>
        </div>
        """

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return f"<h2>❌ Dashboard Error: {str(e)}</h2>", 500


# --- STEP 4: PUSH NOTE ---
@app.route("/push_note", methods=['POST'])
def push_note():
    try:
        token     = session.get('token')
        fhir_base = session.get('fhir_base', FHIR_URL)
        p_id      = request.form.get('p_id')
        note_text = request.form.get('note_text')

        if not token:
            return "<h2>❌ Session expired</h2>", 401
        if not p_id or not note_text:
            return "<h2>❌ Missing data</h2>", 400

        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/fhir+json"
        }

        # Step 1 — Encounter fetch karo
        enc_id = None
        try:
            enc_res = requests.get(
                f"{fhir_base}/Encounter?patient={p_id}&_count=1",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/fhir+json"},
                timeout=10
            ).json()
            entries = enc_res.get('entry', [])
            if entries:
                enc_id = entries[0].get('resource', {}).get('id')
                logger.info(f"Encounter found: {enc_id}")
        except Exception as e:
            logger.error(f"Encounter fetch error: {e}")

        # Step 2 — Payload banao
        payload = {
            "resourceType": "DocumentReference",
            "status":       "current",
            "docStatus":    "final",
            "type": {"coding": [{"system": "http://loinc.org", "code": "11488-4"}]},
            "subject":  {"reference": f"Patient/{p_id}"},
            "date":     now,
            "content": [{"attachment": {
                "contentType": "text/plain",
                "data": base64.b64encode(note_text.encode()).decode()
            }}]
        }

        # Step 3 — Encounter attach karo
        if enc_id:
            payload["context"] = {
                "encounter": [{"reference": f"Encounter/{enc_id}"}],
                "period": {"start": now}
            }

        # Step 4 — Epic mein push karo
        res = requests.post(
            f"{fhir_base}/DocumentReference",
            json=payload,
            headers=headers,
            timeout=10
        )

        logger.info(f"Note push status: {res.status_code}")
        logger.info(f"Note push response: {res.text}")

        if res.status_code == 201:
            return f"""
            <div style='text-align:center; padding:50px;'>
                <h1>✅ Note Successfully Pushed to Epic!</h1>
                <p>Encounter ID: {enc_id}</p>
                <a href='/dashboard'>← Back to Dashboard</a>
            </div>
            """

        return f"<h2>❌ Error {res.status_code}</h2><pre>{res.text}</pre>", res.status_code

    except requests.exceptions.Timeout:
        return "<h2>❌ Epic server timeout</h2>", 504
    except Exception as e:
        logger.error(f"Push note error: {e}")
        return f"<h2>❌ Note Error: {str(e)}</h2>", 500

if __name__ == "__main__":
    app.run(port=5001, debug=True)

