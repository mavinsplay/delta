# from sql import sql_search, sql_formate

# search, time = sql_search('79112013386')

# print(sql_formate(search))



# import json

# with open(r"C:\Users\mavinsplay\Desktop\GSM.json", errors="ignore", encoding='utf-8') as f:
#     data = json.load(f)
#     print(data)

from email_validator import validate_email, EmailUndeliverableError, EmailNotValidError, EmailSyntaxError

try:
    result = validate_email('@gmail.com')
    print(result.original)
except ValueError as error:
    print(error.__class__.__name__)
else:
    print("Email exists.")
