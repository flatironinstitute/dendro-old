import pytest
from dendro.common._api_request import _processor_get_api_request, _processor_put_api_request
from dendro.common._api_request import _client_get_api_request
from dendro.common._api_request import _gui_get_api_request, _gui_put_api_request, _gui_post_api_request, _gui_delete_api_request

@pytest.mark.api
def test_api_request_failures():
    from dendro.common._api_request import _use_api_test_client
    from dendro.mock import set_use_mock
    from test_integration import _get_fastapi_app
    from dendro.api_helpers.clients._get_mongo_client import _clear_mock_mongo_databases

    from fastapi.testclient import TestClient
    app = _get_fastapi_app()
    test_client = TestClient(app)
    _use_api_test_client(test_client)
    set_use_mock(True)

    try:
        # from requests import exceptions
        with pytest.raises(Exception):
            _processor_get_api_request(url_path='/api/incorrect', headers={})
        with pytest.raises(Exception):
            _processor_put_api_request(url_path='/api/incorrect', headers={}, data={})
        with pytest.raises(Exception):
            _client_get_api_request(url_path='/api/incorrect')
        with pytest.raises(Exception):
            _gui_get_api_request(url_path='/api/incorrect', github_access_token='incorrect')
        with pytest.raises(Exception):
            _gui_put_api_request(url_path='/api/incorrect', github_access_token='incorrect', data={})
        with pytest.raises(Exception):
            _gui_post_api_request(url_path='/api/incorrect', github_access_token='incorrect', data={})
        with pytest.raises(Exception):
            _gui_delete_api_request(url_path='/api/incorrect', github_access_token='incorrect')
    finally:
        _use_api_test_client(None)
        set_use_mock(False)
        _clear_mock_mongo_databases()
