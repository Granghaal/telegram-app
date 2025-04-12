import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

def export_tasks_to_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("google-credentials.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("Telegram Задачи").sheet1
    sheet.clear()
    sheet.append_row(["Название", "Категория", "Приоритет", "Дедлайн", "Автор"])

    with open("tasks.json", "r", encoding="utf-8") as f:
        tasks = json.load(f)

    for t in tasks:
        sheet.append_row([
            t.get("text", ""),
            t.get("category", ""),
            t.get("priority", ""),
            t.get("deadline", ""),
            t.get("author", "")
        ])

if __name__ == "__main__":
    export_tasks_to_google_sheet()
