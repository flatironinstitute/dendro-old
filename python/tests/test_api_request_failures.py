import pytest
from dendro.common._api_request import _processor_get_api_request, _processor_put_api_request
from dendro.common._api_request import _client_get_api_request
from dendro.common._api_request import _gui_get_api_request, _gui_put_api_request, _gui_post_api_request, _gui_delete_api_request

def test_api_request_failures():
    from requests import exceptions
    with pytest.raises(exceptions.HTTPError):
        _processor_get_api_request(url_path='/api/incorrect', headers={})
    with pytest.raises(exceptions.HTTPError):
        _processor_put_api_request(url_path='/api/incorrect', headers={}, data={})
    with pytest.raises(exceptions.HTTPError):
        _client_get_api_request(url_path='/api/incorrect')
    with pytest.raises(exceptions.HTTPError):
        _gui_get_api_request(url_path='/api/incorrect', github_access_token='incorrect')
    with pytest.raises(exceptions.HTTPError):
        _gui_put_api_request(url_path='/api/incorrect', github_access_token='incorrect', data={})
    with pytest.raises(exceptions.HTTPError):
        _gui_post_api_request(url_path='/api/incorrect', github_access_token='incorrect', data={})
    with pytest.raises(exceptions.HTTPError):
        _gui_delete_api_request(url_path='/api/incorrect', github_access_token='incorrect')
