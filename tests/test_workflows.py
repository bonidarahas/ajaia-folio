"""Core authorization, formatting, sharing, and file import integration tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import main


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_engine = create_engine(f'sqlite:///{tmp_path / "test.db"}', connect_args={'check_same_thread': False})
    monkeypatch.setattr(main, 'engine', db_engine)
    monkeypatch.setattr(main, 'SessionLocal', sessionmaker(bind=db_engine, expire_on_commit=False))
    main.init_db()
    with TestClient(main.app) as test_client:
        yield test_client
    db_engine.dispose()


def headers(user_id):
    return {'X-User-ID': str(user_id)}


def test_create_save_share_and_revoke(client):
    doc = client.post('/api/documents', headers=headers(1), json={'title': 'Project plan'})
    assert doc.status_code == 201
    doc_id = doc.json()['id']
    assert client.get(f'/api/documents/{doc_id}', headers=headers(2)).status_code == 403
    saved = client.patch(f'/api/documents/{doc_id}', headers=headers(1), json={'content': '<h1>Roadmap</h1><p><strong>Important</strong></p><script>alert(1)</script>'})
    assert saved.status_code == 200
    assert '<strong>Important</strong>' in saved.json()['content']
    assert '<script>' not in saved.json()['content']
    assert client.post(f'/api/documents/{doc_id}/share', headers=headers(2), json={'user_id': 3}).status_code == 403
    assert client.post(f'/api/documents/{doc_id}/share', headers=headers(1), json={'user_id': 2}).status_code == 201
    assert len(client.get('/api/documents', headers=headers(2)).json()['shared']) == 1
    assert client.patch(f'/api/documents/{doc_id}', headers=headers(2), json={'title': 'Edited by Jordan'}).status_code == 200
    assert client.get(f'/api/documents/{doc_id}', headers=headers(1)).json()['title'] == 'Edited by Jordan'
    assert client.delete(f'/api/documents/{doc_id}/share/2', headers=headers(1)).status_code == 204
    assert client.get(f'/api/documents/{doc_id}', headers=headers(2)).status_code == 403


def test_import_markdown_and_validate_types(client):
    r = client.post('/api/import', headers=headers(1), files={'file': ('notes.md', b'# Hello\n\n- First\n- Second', 'text/markdown')})
    assert r.status_code == 201
    assert '<h1>Hello</h1>' in r.json()['content']
    assert '<li>First</li>' in r.json()['content']
    bad = client.post('/api/import', headers=headers(1), files={'file': ('pic.png', b'bad', 'image/png')})
    assert bad.status_code == 415
    huge = client.post('/api/import', headers=headers(1), files={'file': ('huge.txt', b'a'*(512*1024+1), 'text/plain')})
    assert huge.status_code == 413


def test_owner_lists_distinct_from_shared(client):
    assert client.get('/api/documents', headers=headers(1)).json() == {'owned': [], 'shared': []}
    assert client.get('/api/documents').status_code == 401
    assert client.post('/api/documents', headers=headers(1), json={'title': '   '}).status_code == 422
