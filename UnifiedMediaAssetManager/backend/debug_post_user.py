from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
print('Client created, making POST /users')
from app.database import SessionLocal
from app.models.database import UserDB

# Inspect existing users in DB
with SessionLocal() as s:
     users = s.query(UserDB).all()
     print('existing users before POST:', [u.username for u in users])

r = client.post('/users', params={'username': 'dev', 'display_name': 'Dev User'})
print('status:', r.status_code)
try:
    print('json:', r.json())
except Exception:
    print('text:', r.text)
