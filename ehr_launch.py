from flask import Flask, request, session, redirect
from urllib.parse import urlencode
import requests
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "test_secret"


CLIENT_ID     = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
app.secret_key = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.secret_key = "test_secret"




@app.route("/")
def home():
    return "<h2>✅ EHR Launch Server Running!</h2>"
@app.route("/epic/launch")
def epic_launch():
    iss    = request.args.get("iss")
    launch = request.args.get("launch")
    
    session['iss']    = iss
    session['launch'] = launch
    
    params = {
        "response_type": "code",
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "scope":         "launch openid fhirUser patient/Patient.read",
        "launch":        launch,
        "aud":           iss,
    }
    
    # Dynamic — jo bhi launcher bheje us ka auth URL use karo
    # SMART Launcher ke liye
    if "smarthealthit" in iss:
        auth_url = "https://launch.smarthealthit.org/v/r4/auth/authorize"
    else:
        auth_url = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize"
    
    return redirect(auth_url + "?" + urlencode(params))    

@app.route("/callback")
def callback():
    code = request.args.get("code")
    iss  = session.get('iss')
    
    # Token URL fix
    if "smarthealthit" in iss:
        token_url = "https://launch.smarthealthit.org/v/r4/auth/token"
    else:
        token_url = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
    
    r = requests.post(token_url, data={
        "grant_type":   "authorization_code",
        "code":         code,
        "redirect_uri": REDIRECT_URI,
        "client_id":    CLIENT_ID
    })
    
    data = r.json()
    
    if "access_token" in data:
        return f"""
        <h2>✅ EHR Launch Success!</h2>
        <p><b>Patient ID:</b> {data.get('patient')}</p>
        <p><b>Token:</b> {data.get('access_token')[:50]}...</p>
        """
    return f"<h2>❌ Failed</h2><pre>{data}</pre>"




if __name__ == "__main__":
    app.run(port=5001, debug=True)



# import code
# import re

# from flask import Flask, request, session, redirect, url_for
# from urllib.parse import urlencode
# import requests

# app = Flask(__name__)
# app.secret_key = "test_secret"

# CLIENT_ID    = "e7bda512-bad4-4794-8692-5956a8bd5a90"
# REDIRECT_URI = "http://localhost:5001/callback"
# FHIR_URL     = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
# CLIENT_SECRET = "S+f7loevTQHq4OCiYE8+WuK8dyLMmqziFMzLLuoqATyLac3UP7TaMQnJ9mqxASIaDO0yuHtjsb8yqE5oOxGTBg=="
# # --- HOME ---
# @app.route("/")
# def home():
#     return "<h2>✅ EHR Launch Server Running!</h2>"

# # --- STEP 1: EPIC LAUNCH ---
# @app.route("/epic/launch")
# def epic_launch():
#     iss    = request.args.get("iss")
#     launch = request.args.get("launch")
    
#     print(f"ISS: {iss}")
#     print(f"LAUNCH: {launch}")
#     print(f"CLIENT_ID being used: {CLIENT_ID}")

#     session['iss']    = iss
#     session['launch'] = launch

#     params = {
#         "response_type": "code",
#         "client_id":     CLIENT_ID,
#         "redirect_uri":  REDIRECT_URI,
#         "scope":         "launch openid fhirUser patient/Patient.read patient/Observation.read patient/Condition.read patient/MedicationRequest.read patient/DocumentReference.write",
#         "launch":        launch,
#         "aud":           iss,
#     }

#     # Dynamic auth URL
#     if "smarthealthit" in str(iss):
#         auth_url = "https://launch.smarthealthit.org/v/r4/auth/authorize"
#     else:
#         auth_url = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize"

#     return redirect(auth_url + "?" + urlencode(params))


# # --- STEP 2: CALLBACK ---
# @app.route("/callback")
# def callback():
#     code = request.args.get("code")
#     iss  = session.get('iss')

#     # Token URL
#     if "smarthealthit" in str(iss):
#         token_url = "https://launch.smarthealthit.org/v/r4/auth/token"
#     else:
#         token_url = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"

#     r = requests.post(token_url, data={
#         "grant_type":   "authorization_code",
#         "code":         code,
#         "redirect_uri": REDIRECT_URI,
#         "client_id":    CLIENT_ID,
#         "client_secret": CLIENT_SECRET
#     })

#     data = r.json()

#     if "access_token" in data:
#         session['token']      = data['access_token']
#         session['patient_id'] = data.get('patient')
#         return redirect(url_for('dashboard'))

#     return f"<h2>❌ Login Failed</h2><pre>{data}</pre>"

# # --- STEP 3: DASHBOARD ---
# @app.route("/dashboard")
# def dashboard():
#     token      = session.get('token')
#     patient_id = session.get('patient_id')

#     if not token:
#         return redirect(url_for('home'))

#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Accept":        "application/fhir+json"
#     }

#     # Patient Basic Info
#     try:
#         p = requests.get(
#             f"{FHIR_URL}/Patient/{patient_id}",
#             headers=headers
#         ).json()

#         name      = p.get('name', [{}])[0]
#         full_name = f"{name.get('given', [''])[0]} {name.get('family', '')}"
#         dob       = p.get('birthDate', 'N/A')
#         gender    = p.get('gender', 'N/A').capitalize()
#     except:
#         full_name = "Unknown"
#         dob = gender = "N/A"

#     # Weight & BMI
#     weight = bmi = "N/A"
#     try:
#         obs = requests.get(
#             f"{FHIR_URL}/Observation?patient={patient_id}&category=vital-signs",
#             headers=headers
#         ).json()

#         for entry in obs.get('entry', []):
#             r = entry.get('resource', {})
#             code = r.get('code', {}).get('coding', [{}])[0].get('code', '')
#             val  = r.get('valueQuantity', {})

#             if code == '29463-7':  # Weight
#                 weight = f"{val.get('value', 'N/A')} {val.get('unit', '')}"
#             if code == '39156-5':  # BMI
#                 bmi = f"{val.get('value', 'N/A')}"
#     except:
#         pass

#     # Conditions
#     conditions = []
#     try:
#         cond = requests.get(
#             f"{FHIR_URL}/Condition?patient={patient_id}",
#             headers=headers
#         ).json()

#         for entry in cond.get('entry', []):
#             r    = entry.get('resource', {})
#             name_c = r.get('code', {}).get('text', 'Unknown')
#             conditions.append(name_c)
#     except:
#         pass

#     # Medications
#     medications = []
#     try:
#         meds = requests.get(
#             f"{FHIR_URL}/MedicationRequest?patient={patient_id}",
#             headers=headers
#         ).json()

#         for entry in meds.get('entry', []):
#             r    = entry.get('resource', {})
#             med  = r.get('medicationCodeableConcept', {}).get('text', 'Unknown')
#             medications.append(med)
#     except:
#         pass

#     # HTML Dashboard
#     cond_list = "".join([f"<li>{c}</li>" for c in conditions]) or "<li>None found</li>"
#     med_list  = "".join([f"<li>{m}</li>" for m in medications]) or "<li>None found</li>"

#     return f"""
#     <div style="max-width:900px; margin:auto; font-family:sans-serif; padding:20px;">
        
#         <h2 style="color:#007bff; border-bottom:3px solid #007bff; padding-bottom:10px;">
#             🏥 Nobese Patient Dashboard
#         </h2>

#         <div style="background:#f1f8ff; padding:20px; border-radius:10px; margin-bottom:20px;">
#             <h3 style="margin:0; color:#0056b3;">{full_name}</h3>
#             <p><b>DOB:</b> {dob} | <b>Gender:</b> {gender}</p>
#             <p><b>Patient ID:</b> {patient_id}</p>
#         </div>

#         <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:20px;">
#             <div style="background:#fff3cd; padding:15px; border-radius:10px;">
#                 <h4>⚖️ Weight</h4>
#                 <p style="font-size:24px; font-weight:bold;">{weight}</p>
#             </div>
#             <div style="background:#d4edda; padding:15px; border-radius:10px;">
#                 <h4>📊 BMI</h4>
#                 <p style="font-size:24px; font-weight:bold;">{bmi}</p>
#             </div>
#         </div>

#         <div style="background:#fff; border:1px solid #dee2e6; padding:20px; border-radius:10px; margin-bottom:20px;">
#             <h4>🩺 Conditions</h4>
#             <ul>{cond_list}</ul>
#         </div>

#         <div style="background:#fff; border:1px solid #dee2e6; padding:20px; border-radius:10px; margin-bottom:20px;">
#             <h4>💊 Medications</h4>
#             <ul>{med_list}</ul>
#         </div>

#         <div style="background:#d4edda; padding:20px; border-radius:10px;">
#             <h4>📝 Write Note to Epic</h4>
#             <form action="/push_note" method="POST">
#                 <input type="hidden" name="p_id" value="{patient_id}">
#                 <textarea name="note_text" style="width:98%; height:80px; margin-bottom:10px;">Clinical Note - Nobese Visit</textarea>
#                 <button type="submit" style="width:100%; padding:15px; background:#28a745; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">
#                     PUSH NOTE TO EPIC ✅
#                 </button>
#             </form>
#         </div>

#     </div>
#     """


# # --- STEP 4: PUSH NOTE ---
# @app.route("/push_note", methods=['POST'])
# def push_note():
#     import base64
#     from datetime import datetime, timezone

#     token     = session.get('token')
#     p_id      = request.form.get('p_id')
#     note_text = request.form.get('note_text')
#     now       = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

#     headers = {
#         "Authorization":  f"Bearer {token}",
#         "Content-Type":   "application/fhir+json"
#     }

#     payload = {
#         "resourceType": "DocumentReference",
#         "status":       "current",
#         "docStatus":    "final",
#         "type": {
#             "coding": [{"system": "http://loinc.org", "code": "11488-4"}]
#         },
#         "subject":  {"reference": f"Patient/{p_id}"},
#         "date":     now,
#         "content": [{
#             "attachment": {
#                 "contentType": "text/plain",
#                 "data": base64.b64encode(note_text.encode()).decode()
#             }
#         }]
#     }

#     res = requests.post(
#         f"{FHIR_URL}/DocumentReference",
#         json=payload,
#         headers=headers
#     )

#     if res.status_code == 201:
#         return f"""
#         <div style='text-align:center; padding:50px;'>
#             <h1>✅ Note Successfully Pushed to Epic!</h1>
#             <a href='/dashboard'>← Back to Dashboard</a>
#         </div>
#         """

#     return f"<h2>❌ Error {res.status_code}</h2><pre>{res.text}</pre>"


# if __name__ == "__main__":
#     app.run(port=5001, debug=True)