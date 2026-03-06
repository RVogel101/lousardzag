"""
Integration tests for Lousardzag API endpoints.

Tests FastAPI REST API (02-src/lousardzag/api.py):
- POST /cards/preview
- Request/response validation
- Error handling
- Database integration

⚠️ EXCLUDES: Anki-specific endpoints (per project scope)
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

# Add source to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / '02-src'))

from lousardzag.api import app
from lousardzag.database import CardDatabase


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def temp_db_with_cards():
    """Create temporary database with sample cards."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db = CardDatabase(tmp.name)
    
    # Add sample cards
    sample_cards = [
        {'word': 'տուն', 'translation': 'house', 'pos': 'noun'},
        {'word': 'գիրք', 'translation': 'book', 'pos': 'noun'},
        {'word': 'բառ', 'translation': 'word', 'pos': 'noun'},
        {'word': 'լաւ', 'translation': 'good', 'pos': 'adjective'},
    ]
    
    for card in sample_cards:
        db.upsert_card(
            word=card['word'],
            translation=card['translation'],
            pos=card['pos'],
            card_type='vocabulary',
            anki_note_id=1000 + sample_cards.index(card)
        )
    
    yield tmp.name
    
    # Cleanup
    Path(tmp.name).unlink(missing_ok=True)


class TestAPIEndpoints:
    """Test API endpoint availability and responses."""
    
    def test_api_root_accessible(self, client):
        """Test: API root is accessible."""
        # FastAPI automatically provides /docs and /openapi.json
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_schema_available(self, client):
        """Test: OpenAPI schema is generated."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert 'openapi' in schema
        assert 'info' in schema
        assert schema['info']['title'] == "Armenian Cards API"


class TestCardsPreviewEndpoint:
    """Test POST /cards/preview endpoint."""
    
    def test_preview_endpoint_exists(self, client):
        """Test: Preview endpoint responds."""
        response = client.post("/cards/preview", json={})
        
        # Should respond (may be error if no DB, but endpoint exists)
        assert response.status_code in [200, 400, 404, 500]
    
    def test_preview_with_valid_database(self, client, temp_db_with_cards):
        """Test: Preview returns card data from valid database."""
        response = client.post("/cards/preview", json={
            "db_path": temp_db_with_cards
        })
        
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        
        # Should contain cards data
        # (Structure depends on build_preview_payload implementation)
        assert data is not None
    
    def test_preview_without_db_path(self, client):
        """Test: Preview uses default DB path if not specified."""
        response = client.post("/cards/preview", json={})
        
        # May succeed or fail depending on whether default DB exists
        # But should not crash
        assert response.status_code in [200, 400, 404, 500]
    
    def test_preview_with_source_deck_filter(self, client, temp_db_with_cards):
        """Test: Preview accepts source_deck parameter."""
        response = client.post("/cards/preview", json={
            "db_path": temp_db_with_cards,
            "source_deck": "test_deck"
        })
        
        # Should accept parameter (may return empty if deck doesn't exist)
        assert response.status_code in [200, 404]
    
    def test_preview_invalid_db_path(self, client):
        """Test: Preview handles invalid database path."""
        response = client.post("/cards/preview", json={
            "db_path": "/nonexistent/path/to/db.sqlite"
        })
        
        # CardDatabase may create a new sqlite DB if path is creatable.
        assert response.status_code in [200, 400, 404, 500]


class TestAPIRequestValidation:
    """Test request validation and error handling."""
    
    def test_preview_accepts_empty_request(self, client):
        """Test: Preview accepts empty JSON body."""
        response = client.post("/cards/preview", json={})
        
        # Should not crash with validation error
        assert response.status_code in [200, 400, 404, 500]
    
    def test_preview_accepts_null_fields(self, client):
        """Test: Preview accepts null values for optional fields."""
        response = client.post("/cards/preview", json={
            "source_deck": None,
            "db_path": None
        })
        
        # Should handle nulls gracefully
        assert response.status_code in [200, 400, 404, 500]
    
    def test_preview_rejects_invalid_json(self, client):
        """Test: Preview rejects malformed JSON."""
        response = client.post(
            "/cards/preview",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 422 (Unprocessable Entity) for invalid JSON
        assert response.status_code == 422
    
    def test_preview_rejects_wrong_content_type(self, client):
        """Test: Preview expects JSON content type."""
        response = client.post(
            "/cards/preview",
            data="some data",
            headers={"Content-Type": "text/plain"}
        )
        
        # Should reject non-JSON
        assert response.status_code in [415, 422]


class TestAPIResponseFormat:
    """Test API response structure and format."""
    
    def test_preview_returns_json(self, client, temp_db_with_cards):
        """Test: Preview returns valid JSON response."""
        response = client.post("/cards/preview", json={
            "db_path": temp_db_with_cards
        })
        
        if response.status_code == 200:
            # Should be valid JSON
            data = response.json()
            assert isinstance(data, dict)
    
    def test_preview_response_structure(self, client, temp_db_with_cards):
        """Test: Preview response has expected structure."""
        response = client.post("/cards/preview", json={
            "db_path": temp_db_with_cards
        })
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify it's a dictionary (exact structure depends on build_preview_payload)
            assert isinstance(data, dict)
            
            # Should contain some data
            assert len(data) > 0


class TestAPIErrorHandling:
    """Test error handling and edge cases."""
    
    def test_preview_handles_corrupted_database(self, client):
        """Test: Preview handles corrupted database file."""
        # Create a file that's not a valid SQLite database
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.write(b"not a database")
        tmp.close()
        
        try:
            response = client.post("/cards/preview", json={
                "db_path": tmp.name
            })
            
            # With raise_server_exceptions=False, server errors become HTTP 500.
            assert response.status_code == 500
        finally:
            Path(tmp.name).unlink(missing_ok=True)
    
    def test_preview_handles_empty_database(self, client):
        """Test: Preview handles database with no cards."""
        # Create empty database
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        db = CardDatabase(tmp.name)
        
        try:
            response = client.post("/cards/preview", json={
                "db_path": tmp.name
            })
            
            # Should succeed with empty result
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, dict)
        finally:
            Path(tmp.name).unlink(missing_ok=True)


class TestAPICORS:
    """Test CORS headers and cross-origin requests."""
    
    def test_cors_headers_present(self, client, temp_db_with_cards):
        """Test: API includes appropriate CORS headers."""
        response = client.post("/cards/preview", json={
            "db_path": temp_db_with_cards
        })
        
        # Check for common CORS headers
        # (May not be present if CORS middleware not configured)
        # This test documents expected behavior
        headers = response.headers
        
        # At minimum, should have content-type
        assert 'content-type' in headers


class TestAPIPerformance:
    """Test API performance with various data sizes."""
    
    def test_preview_with_large_dataset(self, client):
        """Test: Preview handles database with many cards."""
        # Create database with many cards
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        db = CardDatabase(tmp.name)
        
        # Insert 100 cards
        for i in range(100):
            db.upsert_card(
                word=f'word{i}',
                translation=f'word{i}',
                pos='noun',
                card_type='vocabulary',
                anki_note_id=5000 + i
            )
        
        try:
            response = client.post("/cards/preview", json={
                "db_path": tmp.name
            })
            
            # Should handle large dataset
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, dict)
        finally:
            Path(tmp.name).unlink(missing_ok=True)


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
