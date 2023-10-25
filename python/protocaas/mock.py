_globals = {
    'use_mock': False
}

def using_mock() -> bool:
    return _globals['use_mock']

def set_use_mock(use_mock: bool):
    _globals['use_mock'] = use_mock
