import asyncio
import os
import uuid
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure test settings
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from backend.app.core.config import settings
from backend.app.core.database import Base, get_db
from backend.app.core.security import create_test_jwt
from backend.app.main import app
from backend.app.models import Organization, OrganizationMember, UserProfile

# Test async SQLite in-memory database engine
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Creates fresh database tables before each test and drops them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides an isolated database session for setup in tests."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an async HTTP client connected to the FastAPI application with test database override."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def make_jwt():
    """Factory fixture to create signed test JWTs."""
    def _maker(user_id: str, email: str, is_platform_admin: bool = False, expires_in: int = 3600):
        return create_test_jwt(
            user_id=user_id,
            email=email,
            expires_in_seconds=expires_in,
            is_platform_admin=is_platform_admin,
        )
    return _maker


@pytest_asyncio.fixture
async def owner_setup(client: AsyncClient, make_jwt):
    """Provisions a test organization with an owner user."""
    user_id = str(uuid.uuid4())
    token = make_jwt(user_id=user_id, email=f"owner_{uuid.uuid4().hex[:6]}@example.com")
    resp = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Artisan Craft Studio", "category": "Home & Decor"},
    )
    assert resp.status_code == 201
    org_id = resp.json()["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-Id": org_id}
    return {"headers": headers, "org_id": org_id, "token": token, "user_id": user_id}


@pytest_asyncio.fixture
async def owner_headers(owner_setup):
    """Provides pre-authenticated headers with X-Organization-Id for an organization owner."""
    return owner_setup["headers"]


@pytest_asyncio.fixture
async def owner_org_id(owner_setup):
    """Provides the organization ID for the owner."""
    return owner_setup["org_id"]


@pytest_asyncio.fixture
async def member_headers(client: AsyncClient, make_jwt):
    """Provides headers for a different organization (used for tenant isolation tests)."""
    user_id = str(uuid.uuid4())
    token = make_jwt(user_id=user_id, email=f"other_{uuid.uuid4().hex[:6]}@example.com")
    resp = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Separate Brand Corp", "category": "Fashion"},
    )
    assert resp.status_code == 201
    org_id = resp.json()["id"]
    return {"Authorization": f"Bearer {token}", "X-Organization-Id": org_id}
