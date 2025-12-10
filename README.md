  UW PICO 5.09                        File: README.md                           

# Final Project
# 🏙 Smart Apartment System – Final Project

This repository contains my final project for **CSCI-UA.0480 Software Engineering (Fall 2025)**.

The **Smart Apartment System** is a backend platform for a modern apartment building.  
It simulates:

- Safety monitoring (sensors + automated alerts)
- Building management (maintenance, packages)
- Resident community features (exchange board)

The goal is to create a project that looks like a real deployable system, not just a simple coursework demo.

---

## 1. Project Overview

The system is composed of four cooperating subsystems:

- A **Flask Web Application** for residents and managers  
- A **Sensor Simulator** that produces virtual IoT data  
- An **Alert Engine** that analyzes sensor readings  
- A **MongoDB Database** storing all application data  

Main capabilities include:

- Real-time virtual sensor monitoring  
- Automatic alert generation based on rules  
- Maintenance request workflow  
- Package delivery tracking  
- Community exchange platform  

---

## 2. User Roles & Use Cases

### 2.1 Resident

Residents can:

- Register and log in  
- View live sensor data (temperature, smoke, noise, motion)  
- View alerts related to their rooms  
- Submit maintenance requests  
- View package status (arrived, notified, picked up)  
- Post items in a community exchange board  
- Browse posts and leave comments  

### 2.2 Building Manager

Managers can:

- View sensor data for the entire building  
- See all alerts (fire risk, smoke, noise, suspicious motion)  
- Manage maintenance tickets (pending / in_progress / resolved)  
- Manage packages (record arrival, notify resident, mark pickup)  
- Moderate community posts if needed  

---

## 3. System Architecture

The system includes multiple subsystems, each capable of running in its own container:

### 3.1 Flask Web Application

- Provides Web UI for residents and managers  
- Handles authentication, session management, and permissions  
- Implements dashboards for sensors, alerts, packages, maintenance, and community features  
- Reads and writes data using MongoDB  

### 3.2 Sensor Simulator

- Simulates apartments and rooms:
  - Example: A-101, A-102, etc.  
  - Rooms: living room, bedroom, kitchen  
- Generates virtual sensors:
  - temperature  
  - smoke  
  - noise  
  - motion  
- Writes periodic readings into `sensor_readings` in MongoDB  

### 3.3 Alert Engine

- Reads recent sensor data  
- Applies rule-based logic:
  - High temperature → fire risk alert  
  - Smoke → smoke alert  
  - High noise → disturbance alert  
  - Nighttime motion → suspicious activity  
- Writes results to `alerts` collection  

### 3.4 MongoDB Database

Stores all persistent data:

- users  
- apartments and rooms  
- sensor_readings  
- alerts  
- maintenance_requests  
- packages  
- community_posts  
- comments  

---

## 4. Core Functional Modules

### 4.1 Sensor Monitoring & Safety

- Virtual sensor stream for each room  
- Real-time dashboard  
- Automatic alert creation with severity levels  

### 4.2 Maintenance Requests

Residents:

- Submit maintenance tickets  

Managers:

- View all requests  
- Update status: pending → in_progress → resolved  

### 4.3 Package Delivery Tracking

Residents:

- View list of packages and pickup information  

Managers:

- Record package arrival  
- Assign resident  
- Mark notification and pickup  

### 4.4 Community Exchange

Residents can:

- Create posts (title, description, category, status)  
- Browse posts  
- Leave comments  

---

## 5. Data Model Overview

Key MongoDB collections:

- `users`  
- `apartments`  
- `sensor_readings`  
- `alerts`  
- `maintenance_requests`  
- `packages`  
- `community_posts`  
- `comments`  

Each collection includes timestamps for tracking history.

---

## 6. Project Structure

```text
5-final-zckk7/
├── app.py                 # Main Flask application
├── alert_system/          # Alert engine logic
├── sensor_simulator/      # Sensor simulation scripts
├── templates/             # Jinja2 HTML templates
├── static/                # CSS / JS / images
├── init_db.py             # Optional database initialization
├── instructions.md        # Assignment instructions
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Multi-service orchestration
├── Dockerfile             # Image definition for Flask app
└── README.md              # This file

