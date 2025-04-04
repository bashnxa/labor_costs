# Redmine Work Hours Tracker Bot  

![Telegram Bot Report Example](https://github.com/bashnxa/labor_costs/blob/main/assets/bot_report_example.png?raw=true)

## 🛠 Overview  
This **Telegram bot** automates tracking work hours in **Redmine**. It scrapes data from Redmine reports using **Selenium** and **BeautifulSoup**, then formats and sends work hour reports via Telegram. The bot also reminds employees to log their hours if they fall below the expected threshold.  

⚠ **Warning:** This bot is configured for a **custom Redmine report**. If you use a different Redmine setup, you must **modify the report parsing logic** in the code to match your report's structure.  

⚠ **Warning:** The bot sends error messages to a Telegram chat. Do not connect it to public groups, as confidential data from Redmine may be exposed.

## 🚀 Features  
- **Automated Redmine login** using Selenium  
- **Daily scheduled reports** of logged work hours  
- **Custom reminders** for employees who haven't logged enough time  
- **Manual report check** via the `/check` command in Telegram  
- **Configurable employee work rates**

## 💡 Follow on Telegram
Get bite-sized Python tips, best practices and refactoring tricks  
👉 [t.me/py_snack](https://t.me/py_snack)
