import MySQLdb
import sys

passwords = ['', '123456', 'classora_user', 'password']
for p in passwords:
    try:
        conn = MySQLdb.connect(host='localhost', user='classora_user', passwd=p, db='classora_lms')
        print(f"SUCCESS with password: '{p}'")
        conn.close()
        sys.exit(0)
    except Exception as e:
        print(f"FAILED with password: '{p}' - {e}")
