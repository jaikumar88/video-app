import sqlite3

# Use the correct database file (app.db)
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Check if meetings table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meetings'")
if not cursor.fetchone():
    print("Meetings table does not exist!")
else:
    # Get recent meetings
    cursor.execute('SELECT meeting_id, title, status, created_at FROM meetings ORDER BY created_at DESC LIMIT 10')
    meetings = cursor.fetchall()
    
    print(f"\nTotal meetings found: {len(meetings)}")
    print("\nRecent meetings:")
    for row in meetings:
        print(f"  ID: {row[0]}, Title: {row[1]}, Status: {row[2]}, Created: {row[3]}")
    
    # Check for the specific meeting ID
    cursor.execute('SELECT * FROM meetings WHERE meeting_id = ?', ('864679880',))
    specific = cursor.fetchone()
    if specific:
        print(f"\nMeeting 864679880 found: {specific}")
    else:
        print(f"\nMeeting 864679880 NOT found in database")

conn.close()
