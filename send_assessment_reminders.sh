#!/bin/bash
# PrepIQ — Monthly assessment reminder cron script

TOKEN=$(curl -s -X POST http://localhost:5010/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@fa3tech.io&password=Admin@PrepIQ2025" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "$(date): Failed to get token" >> /home/ubuntu/prepiq/reminders.log
  exit 1
fi

curl -s -X POST "http://localhost:5010/api/notifications/admin/send-reminders?reminder_type=assessment" \
  -H "Authorization: Bearer $TOKEN" >> /home/ubuntu/prepiq/reminders.log 2>&1

echo "" >> /home/ubuntu/prepiq/reminders.log
echo "$(date): Assessment reminders sent" >> /home/ubuntu/prepiq/reminders.log
