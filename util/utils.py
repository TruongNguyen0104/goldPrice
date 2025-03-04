from datetime import datetime, timedelta, timezone

# Get current time in GMT+7
GMT_PLUS_7 = timezone(timedelta(hours=7))
NOW = datetime.now(GMT_PLUS_7).strftime("%d/%m/%Y %H:%M:%S")  # Get the current date and time