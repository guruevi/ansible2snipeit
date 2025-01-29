#!/usr/bin/env python3
from configparser import RawConfigParser
from datetime import datetime, timedelta

from snipeit_api.api import SnipeITApi
from snipeit_api.models import Users
import oracledb

CONFIG = RawConfigParser()
CONFIG.read("settings.conf")
user = CONFIG.get('oracle', 'user')
userpwd = CONFIG.get('oracle', 'password')
host = CONFIG.get('oracle', 'host')
db = CONFIG.get('oracle', 'db')
api = SnipeITApi(url=CONFIG['snipe-it']['url'], api_key=CONFIG['snipe-it']['apikey'])

# Connect to Oracle
connection = oracledb.connect(user=user, password=userpwd, host=host, port=1521, sid=db)

cursor = connection.cursor()

# Get users from Snipe-IT
offset = 0
total = 0
limit = 200
while offset <= total:
    users = api.call('users', payload={"limit": limit, "offset": offset}, method='get')
    total = users['total']
    offset += limit

    for user in users['rows']:
        # Parse datetime from string
        parsed_datetime = datetime.strptime(user['updated_at']['datetime'], "%Y-%m-%d %H:%M:%S")

        # If the user was updated more than 30 days ago, skip
        if parsed_datetime < datetime.now() - timedelta(days=30) or not user['employee_num']:
            continue

        # Get the manager from Oracle. Snipe-IT only allows 1 manager per employee - so we limit it to 1
        cursor.execute("SELECT REPORTS_TO "
                       "FROM itim_dbuser.idm_snipeit_view WHERE URID='%s' FETCH NEXT 1 ROWS ONLY" % user['employee_num'])
        # Get the column names
        rows = cursor.fetchall()
        for row in rows:
            reports_to = row[0]
            person = Users(api=api, id=user['id']).get_by_id().store_state()
            manager = Users(api=api).get_by_employee_num(reports_to)
            person.manager_id = manager.id
            person.avatar = None  # This is a bug in the API
            person.email = None  # Don't update email addresses
            try:
                person.upsert()
            except ValueError as e:
                continue

# Close the cursor
cursor.close()
