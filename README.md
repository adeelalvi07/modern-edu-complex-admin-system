# Modern Educational Complex - School Management System (SMS)

An enterprise-grade, offline-first School Management System desktop application engineered in **Python** using **CustomTkinter** with multi-user **Local LAN Relational Database** support (PostgreSQL/MySQL/SQLite).

Designed to handle 400 to 1,000+ students across 13 classes (**Playgroup, Nursery, Prep, and Class 1 through Class 10**) with concurrent multi-computer LAN access and automated data security.

---

## 🌟 Key Features & Modules

1. **Authentication & RBAC**:
   - Secure login with bcrypt password hashing.
   - Role-Based Access Control (`Admin`, `Teacher`, `Staff`).
   - Audit logging of critical system operations.

2. **Student Management Module**:
   - Comprehensive registration capturing student demographics, parent details, and class/section enrollment.
   - Live search directory with responsive data tables.
   - End-of-year batch promotion engine (auto-graduates Class 10).

3. **Teacher & Staff Management**:
   - Profiles tracking designations, departments, qualifications, and salaries.
   - Monthly payroll generator with payment status tracking.

4. **Fast-Entry Attendance System**:
   - Rapid batch student and staff attendance tracking.
   - One-click *"Mark All Present"* acceleration.
   - Automatic calculation of attendance percentages.
   - Chronic absentees detection flagging students with `< 75%` attendance.

5. **Fee & Finance Module**:
   - Configure fee structures per class (Tuition, Sports, Lab, Exam fees).
   - Batch monthly fee voucher/challan generation.
   - Counter payment POS with receipt numbers.
   - Printable **3-part official PDF Fee Challan** (Student Copy, School Copy, Bank Copy).
   - Defaulters register with one-click **Excel (.xlsx) export**.

6. **Academic & Examination Module**:
   - Marks entry sheet with automatic letter grading (`A+`, `A`, `B`, `C`, `D`, `F`).
   - **Statistical Insights Dashboard**: Calculates Mean, Sample Variance ($s^2$), Standard Deviation ($\sigma$), and Gaussian Normal Distribution Pass/Fail probabilities.
   - Printable **Academic Progress Report Card PDF**.

7. **Data Security & Automated Backups**:
   - Non-blocking background daemon executing daily backups at `23:00`.
   - Native `pg_dump` with **GZIP compression (`.sql.gz`)** and **SHA-256 integrity checksum**.
   - 30-day rolling retention policy automatically pruning expired files.
   - Manual *"Create Instant Backup Now"* button.

---

## 🚀 Launching as an Online Website (Access Anywhere)

The system includes a modern, full-featured **Online Web Portal** accessible from any web browser on desktop, laptop, tablet, or smartphone.

### Option 1: 1-Click Windows Launchers
- **Local / Campus Wi-Fi**: Double-click `start_web.bat`
- **Online Anywhere (Internet Tunnel)**: Double-click `start_web_online.bat`

### Option 2: Command Line
```bash
# Start the web server (accessible on local PC & campus Wi-Fi)
python run_web.py

# Or via main.py
python main.py --web

# Start with instant public HTTPS tunnel for internet access anywhere
python run_web.py --public
```

### 📱 Accessing from Different Devices
1. **On the Server PC**: Open your browser at `http://localhost:8000`
2. **On Campus / Office Wi-Fi**: Open `http://<YOUR-IP>:8000` (e.g. `http://192.168.1.8:8000`) on any phone or laptop connected to the same Wi-Fi.
3. **From Anywhere in the World (Home, Mobile Data, Travel)**:
   - **Cloudflare Quick Tunnel (Free, no account needed)**:
     ```bash
     cloudflared tunnel --url http://localhost:8000
     ```
   - **ngrok (Free HTTPS tunnel)**:
     ```bash
     python run_web.py --public
     ```
   - **24/7 Cloud Hosting**: Deploy directly to **Render.com**, **Railway**, or **Fly.io** using the included `render.yaml`, `Procfile`, and `Dockerfile`.

---

## 🔑 Default Login Credentials
- **Username**: `admin`
- **Password**: `admin123`
- *(Role: Full System Administrator)*

---

## 💻 Desktop Application Mode (Optional)
If you prefer the offline desktop GUI instead of the web portal:
```bash
python main.py
```

---

## 📦 Compiling Standalone Windows .exe
To package the desktop application into a standalone Windows executable:
```bash
python build_exe.py
```
The compiled output will be generated inside `dist/ModernEduComplex_SMS/`.
