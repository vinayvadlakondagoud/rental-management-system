
from dotenv import load_dotenv
load_dotenv()
from flask import send_from_directory
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from config import *
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import random
from datetime import datetime, timedelta
from config import BREVO_API_KEY

app = Flask(__name__)
CORS(app)


def get_db_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route("/login-page")
def login_page():
    return send_from_directory("../FRONTEND", "login.html")

@app.route("/register-page")
def register_page():
    return send_from_directory("../FRONTEND", "register.html")

@app.route("/properties-page")
def properties_page():
    return send_from_directory("../FRONTEND", "properties.html")



@app.route('/')
def home():
    return jsonify({
        "status": "Backend is running 🚀",
        "routes": [
            "/register (POST)",
            "/login (POST)",
            "/properties (GET)",
            "/book (POST)"
        ]
    })

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data['name']
    email = data['email'].lower()
    password = data['password']

    conn = get_db_connection()
    cur = conn.cursor()

    # Check already registered
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cur.fetchone():
        return jsonify({"message": "Email already registered"}), 409

    otp = str(random.randint(100000, 999999))
    expiry = datetime.now() + timedelta(minutes=5)

    cur.execute("""
        INSERT INTO user_otp_verification (name, email, password, otp, expires_at)
        VALUES (%s,%s,%s,%s,%s)
    """, (name, email, password, otp, expiry))

    conn.commit()
    cur.close()
    conn.close()

    send_otp_email(email, otp)

    return jsonify({"message": "OTP sent to email"}), 200

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data["email"]
    password = data["password"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user or user["password"] != password:
        return jsonify({"message": "Invalid credentials"}), 401

    return jsonify({
        "id": user["id"],
        "name": user["name"],
        "email": user["email"]
    })

@app.route('/properties', methods=['GET'])
def get_properties():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, category, price, unit, location,
               status, image_url
        FROM properties
        WHERE approval_status = 'APPROVED'
    """)

    data = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(data)

@app.route('/add-property', methods=['POST'])
def add_property():
    data = request.json

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO properties
        (name, category, price, unit, location, image_url, owner_id, approval_status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'PENDING')
    """, (
        data['name'],
        data['category'],
        data['price'],
        data['unit'],
        data['location'],
        data['image_url'],
        data['owner_id']
    ))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "message": "Property submitted for admin approval"
    }), 201


@app.route('/payment-success', methods=['POST'])
def payment_success():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()

    # Insert booking as PENDING_APPROVAL
    cur.execute("""
        INSERT INTO bookings
        (user_id, property_id, start_date, end_date, total_price, status)
        VALUES (%s,%s,%s,%s,%s,'PENDING_APPROVAL')
    """,(
        data['user_id'],
        data['property_id'],
        data['start'],
        data['end'],
        data['total']
    ))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message":"Payment received, awaiting admin approval"})


@app.route('/property/<int:property_id>')
def get_property(property_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, price, unit, status
        FROM properties
        WHERE id = %s
    """, (property_id,))

    data = cur.fetchone()
    cur.close()
    conn.close()

    return jsonify(data)



@app.route('/admin/pending-properties')
def pending_properties():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id, p.name, p.category, p.location, u.name AS owner
        FROM properties p
        JOIN users u ON p.owner_id = u.id
        WHERE p.approval_status = 'PENDING'
    """)

    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)


@app.route('/admin/update-property-status', methods=['POST'])
def update_property_status():
    data = request.json

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE properties
        SET approval_status = %s
        WHERE id = %s
    """, (data['status'], data['property_id']))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Property status updated"})

@app.route("/booking-page")
def booking_page():
    return send_from_directory("../FRONTEND", "booking.html")


@app.route("/dashboard/<int:user_id>")
def dashboard(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Total properties
    cur.execute("SELECT COUNT(*) AS total FROM properties")
    total_properties = cur.fetchone()["total"]

    # Active rentals (booked properties)
    cur.execute("SELECT COUNT(*) AS active FROM properties WHERE status='booked'")
    active_rentals = cur.fetchone()["active"]

    # User bookings
    cur.execute("""
        SELECT COUNT(*) AS total_bookings
        FROM bookings
        WHERE user_id = %s
    """, (user_id,))
    total_bookings = cur.fetchone()["total_bookings"]

    # Pending payments (example logic)
    cur.execute("""
        SELECT IFNULL(SUM(total_price),0) AS pending
        FROM bookings
        WHERE user_id=%s AND status='CONFIRMED'
    """, (user_id,))
    pending_payments = cur.fetchone()["pending"]

    # Recent bookings
    cur.execute("""
        SELECT b.id, p.name, b.start_date, b.end_date,
               b.total_price, b.status
        FROM bookings b
        JOIN properties p ON b.property_id = p.id
        WHERE b.user_id = %s
        ORDER BY b.id DESC
        LIMIT 5
    """, (user_id,))

    recent = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        "stats": {
            "total_properties": total_properties,
            "active_rentals": active_rentals,
            "total_bookings": total_bookings,
            "pending_payments": pending_payments
        },
        "recent_bookings": recent
    })


@app.route("/profile/<int:user_id>")
def get_profile(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # User info
    cur.execute("""
        SELECT id, name, email
        FROM users
        WHERE id = %s
    """, (user_id,))
    user = cur.fetchone()

    # Total bookings
    cur.execute("""
        SELECT COUNT(*) AS total_bookings
        FROM bookings
        WHERE user_id = %s
    """, (user_id,))
    total_bookings = cur.fetchone()["total_bookings"]

    # Active rentals
    cur.execute("""
        SELECT COUNT(*) AS active_rentals
        FROM bookings
        WHERE user_id = %s AND status='CONFIRMED'
    """, (user_id,))
    active_rentals = cur.fetchone()["active_rentals"]

    # Total spent
    cur.execute("""
        SELECT IFNULL(SUM(total_price),0) AS total_spent
        FROM bookings
        WHERE user_id = %s
    """, (user_id,))
    total_spent = cur.fetchone()["total_spent"]

    # Booking history
    cur.execute("""
        SELECT p.name, b.start_date, b.end_date,
               b.total_price, b.status
        FROM bookings b
        JOIN properties p ON b.property_id = p.id
        WHERE b.user_id = %s
        ORDER BY b.id DESC
    """, (user_id,))
    history = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        "user": user,
        "stats": {
            "total_bookings": total_bookings,
            "active_rentals": active_rentals,
            "total_spent": total_spent
        },
        "history": history
    })

@app.route("/change-password", methods=["POST"])
def change_password():
    data = request.json
    user_id = data["user_id"]
    current = data["current"]
    new = data["new"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT password FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()

    if not user or user["password"] != current:
        return jsonify({"message": "Current password incorrect"}), 400

    cur.execute(
        "UPDATE users SET password=%s WHERE id=%s",
        (new, user_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Password updated successfully"})


@app.route("/settings/<int:user_id>", methods=["GET","POST"])
def settings(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "GET":
        cur.execute("""
            SELECT email_alerts, booking_updates, payment_reminders,
                   language, currency, date_format
            FROM users WHERE id=%s
        """,(user_id,))
        data = cur.fetchone()
        return jsonify(data)

    data = request.json
    cur.execute("""
        UPDATE users SET
        email_alerts=%s,
        booking_updates=%s,
        payment_reminders=%s,
        language=%s,
        currency=%s,
        date_format=%s
        WHERE id=%s
    """,(
        data["email_alerts"],
        data["booking_updates"],
        data["payment_reminders"],
        data["language"],
        data["currency"],
        data["date_format"],
        user_id
    ))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message":"Settings saved"})

@app.route("/delete-account/<int:user_id>", methods=["DELETE"])
def delete_account(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM bookings WHERE user_id=%s", (user_id,))
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Account deleted successfully"})

@app.route("/admin/kpis")
def admin_kpis():
    conn = get_db_connection()
    cur = conn.cursor()

    # Total users
    cur.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cur.fetchone()["total_users"]

    # Total properties
    cur.execute("SELECT COUNT(*) AS total_properties FROM properties")
    total_properties = cur.fetchone()["total_properties"]

    # Pending approvals
    cur.execute("""
        SELECT COUNT(*) AS pending
        FROM properties
        WHERE approval_status = 'PENDING'
    """)
    pending = cur.fetchone()["pending"]

    # Approved listings
    cur.execute("""
        SELECT COUNT(*) AS approved
        FROM properties
        WHERE approval_status = 'APPROVED'
    """)
    approved = cur.fetchone()["approved"]

    cur.close()
    conn.close()

    return jsonify({
        "total_users": total_users,
        "total_properties": total_properties,
        "pending": pending,
        "approved": approved
    })

@app.route("/admin/users")
def admin_users():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, email, created_at
        FROM users
        ORDER BY id DESC
    """)

    users = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(users)

@app.route("/admin/delete-user/<int:user_id>", methods=["DELETE"])
def admin_delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM bookings WHERE user_id=%s", (user_id,))
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "User deleted"})

@app.route("/payment-page")
def payment_page():
    return send_from_directory("../FRONTEND", "payment.html")

@app.route('/admin/pending-bookings')
def pending_bookings():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            b.id AS booking_id,
            u.name AS user_name,
            p.name AS property_name,
            b.start_date,
            b.end_date,
            b.total_price,
            b.status,
            b.property_id
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN properties p ON b.property_id = p.id
        WHERE b.status = 'PENDING_APPROVAL'
        ORDER BY b.id DESC
    """)

    data = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(data)


@app.route('/admin/update-booking-status', methods=['POST'])
def update_booking_status():
    data = request.json
    booking_id = data['booking_id']
    action = data['action']  # APPROVE or REJECT

    conn = get_db_connection()
    cur = conn.cursor()

    # Get property linked to booking
    cur.execute(
        "SELECT property_id FROM bookings WHERE id=%s",
        (booking_id,)
    )
    booking = cur.fetchone()

    if not booking:
        return jsonify({"message": "Booking not found"}), 404

    property_id = booking['property_id']

    if action == "APPROVE":
        # Confirm booking
        cur.execute(
            "UPDATE bookings SET status='CONFIRMED' WHERE id=%s",
            (booking_id,)
        )

        # Lock property
        cur.execute(
            "UPDATE properties SET status='booked' WHERE id=%s",
            (property_id,)
        )

    elif action == "REJECT":
        # Remove booking completely
        cur.execute(
            "DELETE FROM bookings WHERE id=%s",
            (booking_id,)
        )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": f"Booking {action.lower()}ed successfully"})

def send_otp_email(email, otp):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    email_data = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": email}],
        sender={"email": "rms.portal.in@gmail.com", "name": "Rental Management System"},
        subject="Your OTP Verification Code",
        html_content=f"""
        <h2>Verify Your Account</h2>
        <p>Your OTP is:</p>
        <h1>{otp}</h1>
        <p>This OTP is valid for 5 minutes.</p>
        """
    )

    api_instance.send_transac_email(email_data)

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data['email']
    otp = data['otp']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM user_otp_verification
        WHERE email=%s AND otp=%s AND expires_at > NOW()
    """, (email, otp))

    record = cur.fetchone()

    if not record:
        return jsonify({"message": "Invalid or expired OTP"}), 400

    # Insert real user
    cur.execute("""
        INSERT INTO users (name, email, password)
        VALUES (%s,%s,%s)
    """, (record['name'], record['email'], record['password']))

    # Cleanup
    cur.execute("DELETE FROM user_otp_verification WHERE email=%s", (email,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Account verified successfully"}), 201

@app.route("/sales/<int:user_id>")
def user_sales(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            b.id AS booking_id,
            p.name,
            p.category,
            p.location,
            p.image_url,
            p.price,
            p.unit,
            b.start_date,
            b.end_date,
            b.total_price,
            b.status
        FROM bookings b
        JOIN properties p ON b.property_id = p.id
        WHERE b.user_id = %s
          AND b.status = 'CONFIRMED'
        ORDER BY b.id DESC
    """, (user_id,))

    data = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(data)

@app.route("/admin/sales")
def admin_sales():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            b.id AS booking_id,
            u.name AS user_name,
            u.email AS user_email,
            p.name AS property_name,
            p.category,
            p.location,
            p.image_url,
            b.start_date,
            b.end_date,
            b.total_price,
            b.status
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN properties p ON b.property_id = p.id
        WHERE b.status = 'CONFIRMED'
        ORDER BY b.id DESC
    """)

    data = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
    