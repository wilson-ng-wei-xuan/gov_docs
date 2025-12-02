from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_email_otp_invalid_input():
    data = {}
    response = client.post('/email_otp', data)
    print(response)
    assert response.status_code == 404

def test_email_otp_invalid_account():
    data = {"email": "not_exists_account@gmail.com"}
    response = client.post('/email_otp', data)
    print(response)
    assert response.status_code == 404

def test_email_otp_valid_account():
    data = {"email": "mark.qj@gmail.com"}
    response = client.post('/email_otp', data)
    print(response)
    assert response.status_code == 200
