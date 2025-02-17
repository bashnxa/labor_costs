# Redmine Work Hours Tracker Bot  

## 🛠 Overview  
This **Telegram bot** automates tracking work hours in **Redmine**. It scrapes data from Redmine reports using **Selenium** and **BeautifulSoup**, then formats and sends work hour reports via Telegram. The bot also reminds employees to log their hours if they fall below the expected threshold.  

⚠ **Warning:** This bot is configured for a **custom Redmine report**. If you use a different Redmine setup, you must **modify the report parsing logic** in the code to match your report's structure.  

## 🚀 Features  
- **Automated Redmine login** using Selenium  
- **Daily scheduled reports** of logged work hours  
- **Custom reminders** for employees who haven't logged enough time  
- **Manual report check** via the `/check` command in Telegram  
- **Configurable employee work rates**  

## 🏗 Tech Stack  
- **Python** (asyncio, aiogram, Selenium, BeautifulSoup)  
- **Aiogram** for Telegram bot API  
- **Selenium** for web scraping  
- **Apscheduler** for scheduled reports  
- **dotenv** for environment variables  

## 📌 Setup & Installation  

1. **Clone the repository**  
   ```bash
   git clone https://github.com/yourusername/labor_costs.git
   cd labor_costs
