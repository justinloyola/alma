"""Tests for the leads API endpoints."""

import os
import sys
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.base import Base, get_db
from app.db.models import LeadDB, UserDB

# Use an in-memory SQLite database for testing
TEST_DB_URL = "sqlite:///:memory:"
os.environ["DATABASE_URL"] = TEST_DB_URL

# Create a test database engine
engine = create_engine(
    TEST_DB_URL, connect_args={"check_same_thread": False, "timeout": 30}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create test tables
@pytest.fixture(scope="module")
def test_db() -> Generator[Session, None, None]:
    """Create a clean test database and yield a session for testing."""
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine)


def override_get_db():
    """Override the get_db dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Create test client
@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden dependencies."""
    from app.main import app

    # Override the get_db dependency to use our test database
    def override_get_db():
        try:
            yield db
        finally:
            pass  # We'll handle cleanup in the db fixture

    # Override the get_db dependency in the main app
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up after tests
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db: Session) -> Dict[str, Any]:
    """Create a test user in the database."""
    from app.db.models import UserDB

    # Create a unique email
    email = f"test_{datetime.utcnow().timestamp()}@example.com"

    # Clean up any existing user with the same email
    db.query(UserDB).filter(UserDB.email == email).delete()

    # Create and save the user
    user = UserDB(
        email=email,
        hashed_password=(
            "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
        ),  # password = testpassword
        is_active=True,
        is_superuser=False,
    )

    # Add the new user
    db.add(user)
    db.commit()
    db.refresh(user)

    # Verify the user was saved to the database
    db_user = db.query(UserDB).filter(UserDB.email == email).first()
    assert db_user is not None, f"User {email} was not saved to the database"

    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
    }


@pytest.fixture(scope="function")
def test_user_token(test_user: Dict[str, Any], db: Session) -> str:
    """Create a test user token."""
    from datetime import timedelta

    from app.core.config import settings
    from app.core.security import create_access_token
    from app.db.models import UserDB

    # Get the user from the database
    user = db.query(UserDB).filter(UserDB.email == test_user["email"]).first()
    assert user is not None, f"User {test_user['email']} not found in database"

    # Create a token with the user's email as the subject
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(subject=user.email, expires_delta=access_token_expires)

    print(f"\nCreated token for user: {user.email}")
    print(f"User ID: {user.id}")
    print(f"Is Active: {user.is_active}")
    print(f"Token: {token}")

    return token


@pytest.fixture(scope="function")
def auth_headers(test_user_token: str) -> Dict[str, str]:
    """Return headers with the test user's authorization token."""
    return {
        "Authorization": f"Bearer {test_user_token}",
        "Content-Type": "application/json",
    }


# Create a single engine for all tests
@pytest.fixture(scope="session")
def engine() -> Generator[create_engine, None, None]:
    from app.db.database import create_db_engine

    # Use in-memory SQLite for testing to avoid file locking issues
    engine = create_db_engine("sqlite:///:memory:")
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Clean up
    Base.metadata.drop_all(bind=engine)


# Create a session for each test function
@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a test database session."""
    from app.db.database import SessionLocal, engine

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create a new session with autocommit=False, autoflush=False,
    # expire_on_commit=False
    db = SessionLocal()

    # Make sure we're in a clean state
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()

    try:
        yield db
    finally:
        # Clean up
        db.rollback()
        db.close()

        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="function")
def create_test_user(db: Session, test_user: Dict[str, Any]) -> UserDB:
    """Create a test user in the database (for backward compatibility)."""
    # The test_user fixture now creates the user in the database
    # This is kept for backward compatibility with tests that expect this fixture
    user = db.query(UserDB).filter(UserDB.email == test_user["email"]).first()
    if not user:
        user = UserDB(
            email=test_user["email"],
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def test_create_lead(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
    create_test_user: None,
) -> None:
    """Test creating a new lead."""
    # Use a unique email for this test
    test_email = f"test_create_lead_{datetime.utcnow().timestamp()}@example.com"

    # Clean up any existing test data
    db.query(LeadDB).filter(LeadDB.email == test_email).delete()
    db.commit()

    # Use the test_resume.pdf file
    test_resume_path = os.path.join(os.path.dirname(__file__), "test_resume.pdf")
    with open(test_resume_path, "rb") as f:
        resume_file = NamedTemporaryFile(suffix=".pdf")
        resume_file.write(f.read())
    resume_file.seek(0)

    # Prepare form data with the file and other fields
    files = {"resume": ("resume.pdf", resume_file, "application/pdf")}
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": test_email,
    }

    # Make the request with the correct content type for form data
    response = client.post(
        "/api/v1/leads",
        data=data,
        files=files,
        headers={"Authorization": auth_headers["Authorization"]},
    )

    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")

    assert (
        response.status_code == 201
    ), f"Expected status code 201, got {response.status_code}. Response: {response.content}"  # 201 Created  # noqa: E501
    data = response.json()
    assert data["email"] == test_email
    assert data["status"] == "pending"

    # Clean up
    if "id" in data:
        db.query(LeadDB).filter(LeadDB.id == data["id"]).delete()
        db.commit()


def test_get_lead(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
    create_test_user: None,
) -> None:
    """Test retrieving a lead by ID."""
    # Create a test lead with a unique email
    test_email = f"test_get_{datetime.utcnow().timestamp()}@example.com"
    test_lead = LeadDB(
        first_name="Test",
        last_name="User",
        email=test_email,
        created_at=datetime.utcnow(),
    )
    db.add(test_lead)
    db.commit()
    db.refresh(test_lead)

    print(f"Created test lead with ID: {test_lead.id}")

    try:
        # Test getting the lead
        url = f"/api/v1/leads/{test_lead.id}"
        print(f"Making GET request to: {url}")
        response = client.get(url, headers=auth_headers)

        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")

        # Debug: Check if the lead exists in the database
        lead_in_db = db.query(LeadDB).filter(LeadDB.id == test_lead.id).first()
        print(f"Lead in database: {lead_in_db is not None}")
        if lead_in_db:
            print(f"Lead in DB - ID: {lead_in_db.id}, Email: {lead_in_db.email}")

        assert (
            response.status_code == 200
        ), f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["id"] == test_lead.id
        assert data["email"] == test_email
    finally:
        # Clean up
        db.delete(test_lead)
        db.commit()


def test_update_lead(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
    create_test_user: None,
) -> None:
    """Test updating a lead's status."""
    # Create a test lead with a unique email
    test_email = f"test_update_{datetime.utcnow().timestamp()}@example.com"
    test_lead = LeadDB(
        first_name="Test",
        last_name="User",
        email=test_email,
        created_at=datetime.utcnow(),
    )
    db.add(test_lead)
    db.commit()
    db.refresh(test_lead)
    try:
        # Test updating the lead
        response = client.put(
            f"/api/v1/leads/{test_lead.id}",
            json={"status": "reached_out"},
            headers=auth_headers,
        )
        print(f"Update response: {response.status_code}, {response.content}")
        assert (
            response.status_code == 200
        ), f"Expected status code 200, got {response.status_code}. Response: {response.content}"  # noqa: E501
        data = response.json()
        assert data["status"] == "reached_out"

        # Test getting the updated lead
        response = client.get(
            f"/api/v1/leads/{test_lead.id}",
            headers=auth_headers,
        )
        print(f"Get response: {response.status_code}, {response.content}")
        assert (
            response.status_code == 200
        ), f"Expected status code 200, got {response.status_code}. Response: {response.content}"  # noqa: E501
        data = response.json()
        assert data["status"] == "reached_out"
    finally:
        # Clean up
        db.delete(test_lead)
        db.commit()


def test_mark_lead_reached_out(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
    create_test_user: None,
) -> None:
    """Test marking a lead as reached out using the specialized endpoint."""
    # Create a test lead with a unique email
    test_email = f"test_reached_out_{datetime.utcnow().timestamp()}@example.com"
    from app.db.models import LeadStatus, UserDB

    print("\n=== Starting test_mark_lead_reached_out ===")
    print(f"Creating test lead with email: {test_email}")

    # Print all users in the database before creating the lead
    print("\nUsers in database before test:")
    for user in db.query(UserDB).all():
        print(f"- {user.email} (ID: {user.id}, Active: {user.is_active})")

    test_lead = LeadDB(
        first_name="Test",
        last_name="User",
        email=test_email,
        created_at=datetime.utcnow(),
        status=LeadStatus.PENDING.value,
    )
    db.add(test_lead)
    db.commit()
    db.refresh(test_lead)
    print(f"\nCreated test lead with ID: {test_lead.id}, status: {test_lead.status}")

    # Print all leads in the database
    print("\nLeads in database:")
    for lead in db.query(LeadDB).all():
        print(f"- {lead.email} (ID: {lead.id}, Status: {lead.status})")

    try:
        # Test marking the lead as reached out
        print(f"Sending PUT request to /api/v1/leads/{test_lead.id}/reached-out")
        print(f"Auth headers: {auth_headers}")

        response = client.put(
            f"/api/v1/leads/{test_lead.id}/reached-out",
            headers=auth_headers,
            json={},
        )
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")

        assert response.status_code == 200, (  # noqa: E501
            f"Expected status code 200, got {response.status_code}. "
            f"Response: {response.content}"
        )
        data = response.json()
        assert data["status"] == "reached_out"

        # Verify the lead was updated in the database
        updated_lead = db.query(LeadDB).filter(LeadDB.id == test_lead.id).first()
        assert updated_lead.status == "reached_out"

        # Test getting the updated lead
        response = client.get(f"/api/v1/leads/{test_lead.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reached_out"
    finally:
        # Clean up
        db.delete(test_lead)
        db.commit()


def test_update_nonexistent_lead(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
    create_test_user: None,
) -> None:
    """Test updating a lead that doesn't exist."""
    response = client.put(
        "/api/v1/leads/9999",
        json={"status": "reached_out"},
        headers=auth_headers,
    )
    print(
        f"Update non-existent lead response: {response.status_code}, {response.content}"
    )
    assert response.status_code == 404


def test_mark_nonexistent_lead_reached_out(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
    create_test_user: None,
) -> None:
    """Test marking a non-existent lead as reached out."""
    response = client.put(
        "/api/v1/leads/9999/reached-out",
        headers=auth_headers,
    )
    print(
        f"Mark non-existent lead as reached out response: {response.status_code}, {response.content}"  # noqa: E501
    )
    assert response.status_code == 404


def test_get_leads(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
    create_test_user: None,
) -> None:
    """Test retrieving a list of leads with pagination."""
    from datetime import datetime

    from app.db.models import LeadDB

    # Test unauthenticated request
    response = client.get("/api/v1/leads")
    assert response.status_code == 401, "Unauthenticated request should return 401"

    # Create test leads
    test_leads = []
    for i in range(1, 6):
        lead = LeadDB(
            first_name=f"Test{i}",
            last_name=f"Lead{i}",
            email=f"test{i}@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(lead)
        test_leads.append(lead)
    db.commit()

    # Test getting all leads
    response = client.get("/api/v1/leads", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert isinstance(data, list)
    assert len(data) == 5  # Should return all 5 test leads

    # Verify lead data
    for i, lead in enumerate(data, 1):
        assert "id" in lead
        assert lead["first_name"] == f"Test{i}"
        assert lead["last_name"] == f"Lead{i}"
        assert lead["email"] == f"test{i}@example.com"

    # Test pagination
    response = client.get("/api/v1/leads?skip=2&limit=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Should return 2 leads
    assert data[0]["email"] == "test3@example.com"
    assert data[1]["email"] == "test4@example.com"

    # Test with limit exceeding total
    response = client.get("/api/v1/leads?skip=0&limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5  # Should return all 5 test leads

    # Test with skip exceeding total
    response = client.get("/api/v1/leads?skip=10&limit=5", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0  # Should return empty list
