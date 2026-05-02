import jwt
import pytest
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("ALLOW_LEGACY_HEADER_AUTH", "false")


class DummySession:
    def __init__(self, user):
        self._user = user

    def get(self, model, key):
        return self._user


def test_auth_requires_bearer_token():
    app = FastAPI()

    def get_current_user(authorization: str | None = Header(None)):
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        token = authorization[7:].strip()
        try:
            payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e
        return payload

    @app.get("/protected")
    def protected(_=Depends(get_current_user)):
        return {"ok": True}

    client = TestClient(app)
    res = client.get("/protected")
    assert res.status_code == 401


def test_jwt_allows_access():
    app = FastAPI()

    def get_current_user(authorization: str | None = Header(None)):
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        token = authorization[7:].strip()
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        return payload

    @app.get("/protected")
    def protected(me=Depends(get_current_user)):
        return {"id": int(me["sub"]), "role": me["role"]}

    client = TestClient(app)
    token = jwt.encode({"sub": "123", "role": "doctor"}, "test-secret", algorithm="HS256")
    res = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 123
    assert data["role"] == "doctor"

