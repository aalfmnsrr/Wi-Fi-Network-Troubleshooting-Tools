# Wi-Fi Network Troubleshooting Tool

A Python Flask diagnostic dashboard built during my internship at AXA Group Operations, integrating Cisco DNA Center APIs and CLI-based data collection to give network engineers real-time visibility into Wi-Fi infrastructure health — without manually checking each device.

## 🎯 The Problem

Engineers had to manually check individual devices (Access Points, Switches, WLCs) to trace where a Wi-Fi fault originated — slow and error-prone across a network spanning hundreds of devices across multiple countries.

## ⚙️ How It Works

1. Runs locally — no database or deployment, data is generated fresh on each run
2. Retrieves network device information via the Cisco DNA Center REST API
3. For data not exposed by the API, connects directly to devices via CLI (using Netmiko) to pull additional details
4. Combines and saves all retrieved data into structured JSON files
5. Flask serves the dashboard, reading from the JSON files to render real-time topology and device health views

## ✨ Features

- Real-time network topology visualisation: User → AP → Switch → WLC
- Per-device health dashboards for Access Points, Switches, and Wireless LAN Controllers
- CDP (Cisco Discovery Protocol) data integration for accurate device relationship mapping
- Hybrid data collection — REST API combined with CLI (Netmiko) for data not exposed via API
- Client-level lookup and reporting
- Excel-based reporting for inventory and device status tracking

## 🛠️ Tech Stack

Python · Flask · Cisco DNA Center REST API · Netmiko (CLI automation) · JSON · HTML/CSS (Jinja templates)

## 📂 Project Structure
|- main.py # Application entry point
|- dashboard_page.py # Dashboard rendering logic
|- access_point.py # AP data retrieval & processing
├── switch.py # Switch data retrieval & processing
├── wlcs.py # WLC data retrieval & processing
├── client_function.py # Client device lookup logic
├── function.py # Shared helper functions
├── config_example.py # Example config (real credentials excluded)
├── templates/ # HTML templates (Jinja)
└── static/assets/ # CSS & static assets

## 🔒 Note on Configuration

`config_example.py` is a template only — real credentials, tokens, and internal endpoint values are excluded from this repository for security reasons. To run this project, populate your own `config.py` with valid Cisco DNA Center API credentials.

## 📸 Screenshots

<img width="694" height="341" alt="image" src="https://github.com/user-attachments/assets/e2205c4e-e3ab-40da-a24a-1618f7fe1400" />

Figure for Switch Dashboard

## 🧠 What I Learned

The Cisco DNA Center API didn't expose every data point we needed, so I combined it with direct CLI queries via Netmiko to fill the gaps — a good lesson in working around real API limitations rather than assuming an API always has everything. Handling inconsistent data formats between REST responses and raw CLI output, then unifying both into clean JSON for the dashboard, was the core technical challenge. This project was presented to the full Asia network team as a step toward network automation.
