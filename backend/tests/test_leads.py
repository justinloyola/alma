"""Tests for the leads API endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from io import BytesIO

from app.main import app
from app.db.base import Base, get_db
from app.db.models import LeadDB

# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override the get_db dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the get_db dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


def test_create_lead():
    """Test creating a new lead."""
    # Clean up any existing test data
    db = next(override_get_db())
    db.query(LeadDB).filter(LeadDB.email == "test@example.com").delete()
    db.commit()

    # Open the test resume file
    with open("tests/test_resume.pdf", "rb") as f:
        resume_content = f.read()

    # Create a file-like object in memory
    resume_file = BytesIO(resume_content)
    resume_file.name = "test_resume.pdf"  # Add a name attribute for the file

    # Test creating a new lead with form data
    response = client.post(
        "/api/leads",
        files={"resume": ("resume.pdf", resume_file, "application/pdf")},
        data={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "storage_type": "filesystem",
        },
    )

    assert response.status_code == 201  # 201 Created
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["status"] == "pending"

    # Clean up
    if "id" in data:
        db.query(LeadDB).filter(LeadDB.id == data["id"]).delete()
        db.commit()


def test_get_lead():
    """Test retrieving a lead by ID."""
    db = next(override_get_db())

    # Create a test lead
    test_lead = LeadDB(
        first_name="Test", last_name="User", email="test_get@example.com"
    )
    db.add(test_lead)
    db.commit()
    db.refresh(test_lead)

    try:
        # Test getting the lead
        response = client.get(f"/api/leads/{test_lead.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_lead.id
        assert data["email"] == "test_get@example.com"
    finally:
        # Clean up
        db.delete(test_lead)
        db.commit()


def test_update_lead():
    """Test updating a lead's status."""
    db = next(override_get_db())

    # Create a test lead
    test_lead = LeadDB(
        first_name="Test", last_name="User", email="test_update@example.com"
    )
    db.add(test_lead)
    db.commit()
    db.refresh(test_lead)

    try:
        # Test updating the status
        update_data = {"status": "reached_out"}
        response = client.put(f"/api/leads/{test_lead.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reached_out"

        # Verify the update
        response = client.get(f"/api/leads/{test_lead.id}")
        assert response.json()["status"] == "reached_out"
    finally:
        # Clean up
        db.delete(test_lead)
        db.commit()


def test_mark_lead_reached_out():
    """Test marking a lead as reached out using the specialized endpoint."""
    db = next(override_get_db())

    # Create a test lead
    test_lead = LeadDB(
        first_name="Test", last_name="User", email="test_reached_out@example.com"
    )
    db.add(test_lead)
    db.commit()
    db.refresh(test_lead)

    try:
        # Test marking as reached out
        response = client.put(f"/api/leads/{test_lead.id}/reached-out")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reached_out"

        # Verify the update
        response = client.get(f"/api/leads/{test_lead.id}")
        assert response.json()["status"] == "reached_out"
    finally:
        # Clean up
        db.delete(test_lead)
        db.commit()


def test_update_nonexistent_lead():
    """Test updating a lead that doesn't exist."""
    response = client.put("/api/leads/9999", json={"status": "reached_out"})
    assert response.status_code == 404


def test_mark_nonexistent_lead_reached_out():
    """Test marking a non-existent lead as reached out."""
    response = client.put("/api/leads/9999/reached-out")
    assert response.status_code == 404
