# 🏙 Smart Apartment System

[![WebApp CI](https://github.com/your-org/your-repo/actions/workflows/webapp.yml/badge.svg)](https://github.com/your-org/your-repo/actions/workflows/webapp.yml)
[![Sensor Simulator CI](https://github.com/your-org/your-repo/actions/workflows/simulator.yml/badge.svg)](https://github.com/your-org/your-repo/actions/workflows/simulator.yml)
[![Alert Engine CI](https://github.com/your-org/your-repo/actions/workflows/alert.yml/badge.svg)](https://github.com/your-org/your-repo/actions/workflows/alert.yml)

A multi-subsystem smart building backend platform featuring virtual sensors, automated safety alerts, maintenance workflows, package delivery tracking, and a resident community exchange system.

---

## 📌 Table of Contents
- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
- [Subsystems](#subsystems)
- [Core Features](#core-features)
- [Data Model](#data-model)
- [How to Run](#how-to-run)
- [Environment Variables](#environment-variables)
- [Database Initialization](#database-initialization)
- [Docker Hub Images](#docker-hub-images)
- [Team Members](#team-members)
- [Project Structure](#project-structure)

---

## 🧠 **Project Overview**

The **Smart Apartment System** simulates how a modern apartment building operates.  
It integrates multiple subsystems to provide:

- Real-time sensor monitoring (temperature, smoke, noise, motion)
- Automated safety alerts using rule-based detection
- Maintenance request system for residents and building managers
- Package delivery tracking
- Community exchange platform for item sharing

The goal is to create a system that *feels like a real smart apartment backend*, not just a classroom exercise.

---

## 🏗 **System Architecture**

The system consists of 4 containerized subsystems:

### **1. Web Application (Flask)**
- Resident & Admin dashboards  
- Authentication + session control  
- REST API endpoints  
- Views for alerts, packages, maintenance, community posts  

### **2. Sensor Simulator (Python)**
- Generates virtual sensor readings  
- Simulates apartments + rooms  
- Writes continuous data to MongoDB  

### **3. Alert Engine (Python)**
- Reads latest sensor readings  
- Applies rules:
  - High temperature → fire risk  
  - Smoke level → smoke alarm  
  - High noise → disturbance  
  - Motion anomalies → suspicious activity  
- Saves alerts to MongoDB  

### **4. MongoDB Database**
Stores:
- users  
- apartments  
- sensor_readings  
- alerts  
- maintenance_requests  
- packages  
- community_posts  
- comments  

---

## 🚀 **Core Features**

### 🔥 **IoT & Safety Monitoring**
- Real-time temperature, smoke, noise, motion  
- Alert Engine generates safety alerts  
- Severity levels: `low`, `medium`, `high`  

### 🛠 **Maintenance Request System**
Residents:
- Submit tickets (plumbing, electrical, HVAC, etc.)

Admins:
- Manage tickets: `pending → in_progress → resolved`

### 📦 **Package Delivery Management**
Residents:
- View packages & pickup status

Admins:
- Register new packages  
- Mark as notified/collected  

### 🤝 **Community Exchange**
Residents can:
- Post items to share or exchange  
- Filter by categories  
- Leave comments  

Admins:
- Moderate posts  

---

## 🗂 **Data Model Overview**

Collections include:

```plaintext
users
apartments
sensor_readings
alerts
maintenance_requests
packages
community_posts
comments
