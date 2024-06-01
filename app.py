from flask import Flask, request, render_template_string
import pyotp
from twilio.rest import Client
import re

app = Flask(__name__)

# Replace these placeholders with your actual Twilio credentials
TWILIO_ACCOUNT_SID = 'your_actual_account_sid'
TWILIO_AUTH_TOKEN = 'your_actual_auth_token'
TWILIO_PHONE_NUMBER = '+1234567890'  # Replace with your actual Twilio phone number

# Initialize the Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# In-memory storage for demonstration (in a real application, store this securely per user)
user_data = {
    'phone_number': '',
    'secret': pyotp.random_base32()
}

def is_valid_phone_number(phone_number):
    # Simple regex to check if the phone number is in E.164 format
    pattern = re.compile(r'^\+\d{1,15}$')
    return pattern.match(phone_number)

@app.route('/')
def index():
    return render_template_string('''
        <h1>2FA with OTP</h1>
        <p>Enter your phone number to receive an OTP. Use international format (e.g., +1234567890).</p>
        <form method="post" action="{{ url_for('send_otp') }}">
            <p><input type="text" name="phone_number" placeholder="Phone Number"/></p>
            <p><input type="submit" value="Send OTP"/></p>
        </form>
    ''')

@app.route('/send_otp', methods=['POST'])
def send_otp():
    phone_number = request.form['phone_number']
    if not is_valid_phone_number(phone_number):
        return "Invalid phone number format. Please use international format (e.g., +1234567890).", 400

    user_data['phone_number'] = phone_number
    totp = pyotp.TOTP(user_data['secret'])
    otp = totp.now()
    
    try:
        # Send OTP via Twilio
        message = client.messages.create(
            body=f'Your OTP is {otp}',
            from_=TWILIO_PHONE_NUMBER,
            to=user_data['phone_number']
        )
        return render_template_string('''
            <h1>OTP Sent</h1>
            <p>OTP has been sent to your phone number. Enter the OTP below to verify.</p>
            <form method="post" action="{{ url_for('verify_otp') }}">
                <p><input type="text" name="otp" placeholder="Enter OTP"/></p>
                <p><input type="submit" value="Verify OTP"/></p>
            </form>
        ''')
    except Exception as e:
        return f"Failed to send OTP: {e}", 500

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    otp = request.form['otp']
    totp = pyotp.TOTP(user_data['secret'])
    
    if totp.verify(otp):
        return "OTP is valid!"
    else:
        return "Invalid OTP!", 400

if __name__ == '__main__':
    app.run(debug=True)
