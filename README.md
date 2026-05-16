
# 🏠 Rental Management System

A full-stack **Rental Management System** built using **HTML, CSS, Python Flask, and MySQL**, designed to streamline property listing, booking, and management with secure authentication and admin-controlled workflows.

---

## 🚀 Features

### 👤 User Module

* User registration with **OTP email verification**
* Secure login system
* Browse available rental properties
* Book properties with date selection
* View booking history and purchases
* User dashboard & profile management

---

### 🏢 Property Management

* Add new property listings
* Multiple categories:

  * Real Estate
  * Vehicles
  * Equipment
* Property details:

  * Price
  * Location
  * Billing unit (per day/month)
* **Admin approval required before listing**

---

### 📅 Booking System

* Select rental duration
* Automatic price calculation
* Booking confirmation workflow
* Booking status tracking:

  * Pending
  * Confirmed

---

### 🛡️ Admin Panel

* Approve/reject property listings
* Manage users and properties
* Monitor bookings and transactions
* Maintain system integrity

---

## 🏗️ Tech Stack

| Layer          | Technology             |
| -------------- | ---------------------- |
| Frontend       | HTML, CSS, Bootstrap   |
| Backend        | Python Flask           |
| Database       | MySQL (Workbench)      |
| API Type       | REST APIs              |
| Authentication | OTP Email Verification |

---


## ⚙️ Installation & Setup

### 🔹 1. Clone the Repository

```bash
git clone https://github.com/your-username/rental-management-system.git
cd rental-management-system
```

---

### 🔹 2. Backend Setup

```bash
cd BACKEND
pip install -r requirements.txt
```

Create `.env` file:

```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=rental_db
BREVO_API_KEY=your_api_key
```

Run server:

```bash
python app.py
```

---

### 🔹 3. Frontend Setup

Simply open:

```bash
FRONTEND/index.html
```

---

## 🔄 System Workflow

1. User registers → OTP verification
2. User logs in
3. User browses properties
4. Owner adds property → goes for admin approval
5. Admin approves property
6. User books property
7. Booking stored in database
8. Admin approves booking

---

## 🔐 Security Features

* OTP-based email verification
* Admin approval system
* Session-based authentication (frontend storage)

---

## 📊 Database Design

Tables used:

* `users`
* `properties`
* `bookings`
* `user_otp_verification`

---

## ✅ Advantages

* Centralized rental management
* Secure authentication system
* Admin-controlled ecosystem
* Scalable architecture
* Multi-category rental support

---

## ⚠️ Limitations

* No real payment gateway integration
* Passwords not encrypted (can be improved)
* Limited filtering/search functionality

---

## 🔮 Future Enhancements

* 💳 Payment Gateway Integration (Razorpay/Stripe)
* 📍 Google Maps Integration
* 💬 Real-time chat system
* 📱 Mobile app version
* 🤖 AI-based recommendations


## 🤝 Contributing

Contributions are welcome!
Feel free to fork this repo and submit a pull request.

---

## 📄 License

This project is open-source and available under the **MIT License**.

---

## 👨‍💻 Author

**Vinay Vadlakonda**

* GitHub: [https://github.com/vinayvadlakondagoud](https://github.com/vinayvadlakondagoud)
* LinkedIn: [https://www.linkedin.com/in/vinay-vadlakonda/](https://www.linkedin.com/in/vinay-vadlakonda/)

---

## ⭐ Show Your Support

If you like this project, please ⭐ the repository!
