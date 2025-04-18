from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import requests
import uuid
import sqlite3

app = Flask(__name__)


app.secret_key = '094f4cacd1e7b665821c40c8a005f1abe9d7e25fe0897c4459d3132a1e55f180'  

# Payment Gateway Configuration
API_URL = "https://pay.imb.org.in/api/create-order"  
API_KEY = "5e491c82fc0f1aedddc986828462fc84"  

@app.route('/', methods=['GET', 'POST'])
def home():
    """Home route with form to initiate payment"""
    if request.method == 'POST':
        amount = request.form.get('amount')
        mobile = request.form.get('mobile')
        email = request.form.get('email')

        if amount and amount.isdigit() and mobile:
            # Save data to session
            session['amount'] = amount
            session['mobile'] = mobile
            session['email'] = email
            return redirect(url_for('pay'))

    return render_template('home.html')

@app.route('/pay')
def pay():
    """Initiate the payment process"""

    amount = session.get('amount')
    mobile = session.get('mobile')
    email = session.get('email')

    if not amount or not mobile or not email:
        return "Invalid payment data!", 400

    # Generate a unique transaction ID
    order_id = str(uuid.uuid4().hex[:12])
    session['order_id'] = order_id

    payload = {
        "customer_mobile": mobile,
        "user_token": API_KEY,
        "amount": amount,
        "order_id": order_id,
        "redirect_url": "https://9652-103-166-12-205.ngrok-free.app/payment-status",
        "remark1": email,
        "remark2": "Test transaction"
    }

    headers = {
         "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        # Send POST request to payment gateway
        response = requests.post(API_URL, data=payload, headers=headers)
        # print("status code", response.status_code)
        # print("response", response.text)

        if response.status_code == 200:
            response_data = response.json()
            print("Response Data:", response_data)
            payment_url = response_data.get('result', {}).get('payment_url')
            

            # # Log the entire response
            # print("Response Data:", response_data)

            # # Extract the payment URL
            # payment_url = response_data.get('result', {}).get('payment_url')

            if payment_url:
                # Redirect the user to the payment gateway
                return redirect(payment_url)
  
            else:
                return "Payment URL not found!", 400

        else:
            return f"Failed to create order. Status code: {response.status_code}"

    except Exception as e:
        print("Error:", e)
        return "An error occurred during payment processing.", 500



@app.route('/payment-status', methods=['POST'])
def payment_status():
    """Handle payment status verification"""
    
    # 🔥 Debug incoming request
    print("Headers:", request.headers)
    print("Form Data:", request.form)
    print("JSON Data:", request.get_json())

    # Get order details
    order_id = request.form.get('order_id')
    utr = request.form.get('utr')

    if not order_id or not utr:
        return "Invalid payment data", 400

    # Verification API
    verification_url = "https://pay.imb.org.in/api/verify-payment"
    
    payload = {
        "order_id": order_id,
        "utr": utr
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        # ✅ Use POST instead of GET
        response = requests.post(verification_url, json=payload, headers=headers)

        if response.status_code == 200:
            payment_data = response.json().get('result', {})
            
            # Extract payment details
            status = payment_data.get('status', 'failed')
            amount = payment_data.get('amount', '0')
            mobile = payment_data.get('customer_mobile', 'N/A')
            email = payment_data.get('remark1', 'N/A')
            message = payment_data.get('message', 'No message')

            # Store in SQLite DB
            conn = sqlite3.connect('payments.db')
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO transactions (status, amount, mobile, email, order_id, utr, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (status, amount, mobile, email, order_id, utr, message))

            conn.commit()
            conn.close()

            # ✅ Redirect to history if payment is successful
            if status == "success":
                return redirect(url_for('history'))

            # ✅ Render status page with payment details
            return render_template(
                'status.html',
                status=status,
                amount=amount,
                mobile=mobile,
                email=email,
                order_id=order_id,
                utr=utr,
                message=message
            )

        else:
            return f"Payment verification failed. Status code: {response.status_code}"

    except Exception as e:
        print("Error:", e)
        return "An error occurred during payment verification.", 500



@app.route('/process-payment', methods=['POST'])
def process_payment():
    """Process payment and redirect to payment gateway"""
    
    try:
        # Extract and validate form data
        amount = request.form.get('amount')
        mobile = request.form.get('mobile')
        email = request.form.get('email')

        if not amount or not mobile or not email:
            return "Invalid payment data!", 400

        # ✅ Data validation
        if not amount.isdigit() or int(amount) <= 0:
            return "Invalid amount!", 400

        if not mobile.isdigit() or len(mobile) != 10:
            return "Invalid mobile number!", 400

        if '@' not in email or '.' not in email:
            return "Invalid email!", 400

        # Store data in session
        print("Storing in session:", amount, mobile, email)
        session['amount'] = amount
        session['mobile'] = mobile
        session['email'] = email

        # Redirect to payment page
        return redirect(url_for('pay'))

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred during payment processing.", 500

@app.route('/history')
def history():
    try:
        conn = sqlite3.connect('payments.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM transactions ORDER BY timestamp DESC')
        transactions = cursor.fetchall()

        conn.close()

        return render_template('history.html', transactions=transactions)

    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run(debug=True)
