import os
os.environ['DATABASE_URL']='sqlite:///./data/test_farmlink.db'
os.environ['SECRET_KEY']='test-secret-key'
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
def test_health():
    assert client.get('/api/health').status_code==200

def test_public_farmer_submission():
    r=client.post('/api/public/farmers',json={"farm_name":"Test Farm","contact_person":"Test Person","phone":"0712345678","email":"test@example.com","location":"Gauteng","producer_type":"Emerging farmer","weekly_capacity":100,"egg_sizes":"Large","packaging":"30-egg trays","delivery_capability":"Can deliver","notes":"Test"})
    assert r.status_code==201
    assert r.json()['reference'].startswith('FAR-')
