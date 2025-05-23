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

from alembic import command
from alembic.config import Config

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


def run_migrations():
    """Run Alembic migrations on the test database."""
    # Get the directory containing this file
    test_dir = Path(__file__).parent
    # Get the project root directory (one level up from tests)
    project_root = test_dir.parent
    # Path to the alembic.ini file
    alembic_ini = project_root / "alembic.ini"

    # Configure Alembic
    alembic_cfg = Config(alembic_ini)
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)

    # Run migrations
    command.upgrade(alembic_cfg, "head")


# Create test tables using Alembic
@pytest.fixture(scope="module")
def test_db() -> Generator[Session, None, None]:
    """Create a clean test database with migrations and yield a session for testing."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    try:
        # Run migrations
        run_migrations()
        yield
    finally:
        # Drop all tables
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
    """Create and configure the test database engine."""
    from app.db.database import create_db_engine

    # Use in-memory SQLite for testing to avoid file locking issues
    engine = create_db_engine("sqlite:///:memory:")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Run migrations
    test_dir = Path(__file__).parent
    project_root = test_dir.parent
    alembic_ini = project_root / "alembic.ini"

    alembic_cfg = Config(alembic_ini)
    alembic_cfg.set_main_option("sqlalchemy.url", "sqlite:///:memory:")

    # Run migrations
    command.upgrade(alembic_cfg, "head")

    yield engine

    # Clean up
    Base.metadata.drop_all(bind=engine)


# Create a session for each test function
@pytest.fixture(scope="function")
def db(engine: create_engine) -> Generator[Session, None, None]:
    """Create a test database session with proper transaction handling."""
    from app.db.database import SessionLocal

    # Begin a transaction
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    # Create a test user if it doesn't exist
    from app.db.models import UserDB

    test_user = session.query(UserDB).filter_by(email="test@example.com").first()
    if not test_user:
        test_user = UserDB(
            email="test@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password = "secret"
            is_active=True,
            is_superuser=False,
        )
        session.add(test_user)
        session.commit()

    try:
        yield session
    finally:
        # Rollback the transaction to undo any changes made during the test
        session.close()
        transaction.rollback()
        connection.close()


def test_create_lead(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
) -> None:
    """Test creating a new lead."""
    # Use a unique email for this test
    test_email = f"test_create_lead_{datetime.utcnow().timestamp()}@example.com"

    # Clean up any existing test data
    db.query(LeadDB).filter(LeadDB.email == test_email).delete()
    db.commit()

    # Prepare form data
    test_resume_path = os.path.join(os.path.dirname(__file__), "test_resume.pdf")

    # Use the test_resume.pdf file
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
    print(f"Response content: {response.text}")

    if response.status_code != 201:
        print("Error details:")
        try:
            error_data = response.json()
            print(f"Error type: {type(error_data)}")
            print(f"Error content: {error_data}")
            if "detail" in error_data:
                for detail in error_data["detail"]:
                    print(f"- {detail}")
        except Exception as e:
            print(f"Failed to parse error response: {e}")

    assert (
        response.status_code == 201
    ), f"Expected status code 201, got {response.status_code}. Response: {response.text}"

    data = response.json()
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"
    assert data["email"] == test_email
    assert data["status"] == "pending"  # Default status should be 'pending'

    # Clean up
    if "id" in data:
        db.query(LeadDB).filter(LeadDB.id == data["id"]).delete()
        db.commit()


def test_get_lead(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
) -> None:
    """Test retrieving a lead by ID."""
    # Create a test lead first
    test_email = f"test_get_lead_{datetime.utcnow().timestamp()}@example.com"

    # Create lead via API to ensure all required fields are set
    lead_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": test_email,
        "phone": "+1234567890",
        "notes": "Test lead",
    }

    response = client.post(
        "/api/v1/leads/",
        json=lead_data,
        headers=auth_headers,
    )

    assert response.status_code == 201, f"Failed to create test lead: {response.text}"
    created_lead = response.json()

    try:
        # Test getting the lead
        response = client.get(
            f"/api/v1/leads/{created_lead['id']}",
            headers=auth_headers,
        )

        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")

        assert (
            response.status_code == 200
        ), f"Expected status code 200, got {response.status_code}"

        data = response.json()
        assert data["id"] == created_lead["id"]
        assert data["id"] == test_lead.id
        assert data["email"] == test_email
    finally:
        # Clean up
        db.delete(test_lead)
        db.commit()


def create_test_lead(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
    email: str,
) -> dict:
    """Helper function to create a test lead."""
    test_resume_path = os.path.join(os.path.dirname(__file__), "test_resume.pdf")
    with open(test_resume_path, "rb") as f:
        resume_file = NamedTemporaryFile(suffix=".pdf")
        resume_file.write(f.read())
    resume_file.seek(0)

    files = {"resume": ("resume.pdf", resume_file, "application/pdf")}
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "phone": "+1234567890",
        "notes": "Test lead",
    }

    response = client.post(
        "/api/v1/leads",
        data=data,
        files=files,
        headers={"Authorization": auth_headers["Authorization"]},
    )

    assert response.status_code == 201, f"Failed to create test lead: {response.text}"
    return response.json()


def test_update_lead(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
) -> None:
    """Test updating a lead's status."""
    # Create a test lead first
    test_email = f"test_update_{datetime.utcnow().timestamp()}@example.com"

    # Create lead via the helper function
    created_lead = create_test_lead(client, db, auth_headers, test_email)

    try:
        # Test updating the lead
        update_data = {"status": "reached_out"}
        response = client.put(
            f"/api/v1/leads/{created_lead['id']}",
            data=update_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                **auth_headers,
            },
        )

        print(f"Update response status code: {response.status_code}")
        print(f"Update response content: {response.text}")

        assert (
            response.status_code == 200
        ), f"Expected status code 200, got {response.status_code}"

        updated_lead = response.json()
        assert updated_lead["status"] == "reached_out"
        assert updated_lead["id"] == created_lead["id"]
        assert updated_lead["email"] == test_email

    finally:
        # Clean up
        db.query(LeadDB).filter(LeadDB.id == created_lead["id"]).delete()
        db.commit()


def test_mark_lead_reached_out(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
) -> None:
    """Test marking a lead as reached out using the specialized endpoint."""
    # Create a test lead first
    test_email = f"test_reached_out_{datetime.utcnow().timestamp()}@example.com"

    # Create lead via the helper function
    created_lead = create_test_lead(client, db, auth_headers, test_email)

    try:
        # Test marking the lead as reached out
        response = client.put(
            f"/api/v1/leads/{created_lead['id']}/reached-out",
            headers=auth_headers,
        )

        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")

        assert (
            response.status_code == 200
        ), f"Expected status code 200, got {response.status_code}"

        updated_lead = response.json()
        assert updated_lead["status"] == "reached_out"
        assert updated_lead["id"] == created_lead["id"]
        assert updated_lead["email"] == test_email

        # Test that the status cannot be changed back to new
        response = client.put(
            f"/api/v1/leads/{created_lead['id']}/reached-out",
            headers=auth_headers,
        )

        assert (
            response.status_code == 400
        ), "Should not be able to mark as reached out again"

    finally:
        # Clean up
        db.query(LeadDB).filter(LeadDB.id == created_lead["id"]).delete()
        db.commit()


def test_update_nonexistent_lead(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
) -> None:
    """Test updating a lead that doesn't exist."""
    # Test updating a non-existent lead
    non_existent_id = 999999
    response = client.put(
        f"/api/v1/leads/{non_existent_id}",
        data={"status": "reached_out"},
        headers={"Content-Type": "application/x-www-form-urlencoded", **auth_headers},
    )

    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")

    assert (
        response.status_code == 404
    ), f"Expected status code 404, got {response.status_code}. Response: {response.text}"


def test_mark_nonexistent_lead_reached_out(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
) -> None:
    """Test marking a non-existent lead as reached out."""
    non_existent_id = 999999
    response = client.put(
        f"/api/v1/leads/{non_existent_id}/reached-out",
        headers=auth_headers,
    )

    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")

    assert (
        response.status_code == 404
    ), f"Expected status code 404, got {response.status_code}"


def test_get_leads(
    client: TestClient,
    db: Session,
    auth_headers: Dict[str, str],
) -> None:
    """Test retrieving a list of leads with pagination."""
    # Create test leads via API
    test_emails = [
        f"test_get_leads_{i}_{datetime.utcnow().timestamp()}@example.com"
        for i in range(1, 6)
    ]

    created_lead_ids = []

    try:
        # Create test leads using the helper function
        for i, email in enumerate(test_emails):
            lead = create_test_lead(
                client=client, db=db, auth_headers=auth_headers, email=email
            )
            # Update additional fields
            lead["first_name"] = f"Test{i}"
            lead["last_name"] = f"User{i}"
            lead["phone"] = f"+12345678{i:02d}"
            lead["notes"] = f"Test lead {i}"
            created_lead_ids.append(lead["id"])

        # Test getting all leads
        response = client.get("/api/v1/leads", headers=auth_headers)

        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")

        assert (
            response.status_code == 200
        ), f"Expected status code 200, got {response.status_code}"

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5  # Should be at least our 5 test leads

        # Test pagination
        response = client.get(
            "/api/v1/leads",
            params={"skip": 2, "limit": 2},
            headers=auth_headers,
        )

        print(f"Paginated response status code: {response.status_code}")
        print(f"Paginated response content: {response.text}")

        assert (
            response.status_code == 200
        ), f"Expected status code 200, got {response.status_code}"

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2  # Should return exactly 2 items due to pagination

    finally:
        # Clean up
        for lead_id in created_lead_ids:
            db.query(LeadDB).filter(LeadDB.id == lead_id).delete()
        db.commit()
        # Test with limit exceeding total
        response = client.get(
            "/api/v1/leads/", params={"skip": 0, "limit": 10}, headers=auth_headers
        )

        print(f"Limit exceeding response status code: {response.status_code}")
        print(f"Limit exceeding response content: {response.text}")

        assert (
            response.status_code == 200
        ), f"Expected status code 200, got {response.status_code}"

        data = response.json()
        assert len(data) >= 5  # Should return all test leads

        # Test with skip exceeding total
        response = client.get(
            "/api/v1/leads/", params={"skip": 100, "limit": 5}, headers=auth_headers
        )

        print(f"Skip exceeding response status code: {response.status_code}")
        print(f"Skip exceeding response content: {response.text}")

        assert (
            response.status_code == 200
        ), f"Expected status code 200, got {response.status_code}"

        data = response.json()
        assert len(data) == 0  # Should return empty list
