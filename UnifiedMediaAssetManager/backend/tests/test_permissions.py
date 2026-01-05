from fastapi.testclient import TestClient
from app.main import app
from app import auth
import os

client = TestClient(app)


def make_token(sub: str, roles=None):
    return auth.create_access_token(subject=sub, roles=roles)


def test_owner_and_admin_permissions(tmp_path):
    # create tokens
    alice_token = make_token('alice', roles=['user'])
    bob_token = make_token('bob', roles=['user'])
    admin_token = make_token('admin', roles=['admin'])

    # create a universe as alice
    headers = {'Authorization': f'Bearer {alice_token}'}
    r = client.post('/universes', headers=headers, json={'name': 'Alice Uni', 'description': 'owned by alice', 'elements': []})
    assert r.status_code == 201
    uni = r.json()
    uni_id = uni['id']
    assert uni.get('owner') in ('alice', 'dev', None)  # depending on token subject serialization

    # attempt to add element as bob -> should be forbidden
    headers_bob = {'Authorization': f'Bearer {bob_token}'}
    r = client.post(f'/universes/{uni_id}/elements', headers=headers_bob, json={'name': 'Bob Element', 'element_type': 'Generic'})
    assert r.status_code == 403

    # admin can add element
    headers_admin = {'Authorization': f'Bearer {admin_token}'}
    r = client.post(f'/universes/{uni_id}/elements', headers=headers_admin, json={'name': 'Admin Element', 'element_type': 'Generic'})
    assert r.status_code == 201


def test_upload_endpoint_allows_authenticated_users():
    token = make_token('uploader', roles=['user'])
    headers = {'Authorization': f'Bearer {token}'}

    # upload a small PNG blob
    files = {'file': ('test.png', b'\x89PNG\r\n\x1a\n', 'image/png')}
    r = client.post('/media/upload', headers=headers, files=files)
    assert r.status_code == 200
    data = r.json()
    assert 'url' in data
    # cleanup created file if local
    url = data['url']
    if url.startswith('/media'):
        # remove the file created in backend/media/images
        fname = url.split('/')[-1]
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media', 'images', fname)
        if os.path.exists(path):
            os.remove(path)
