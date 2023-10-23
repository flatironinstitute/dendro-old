from protocaas.sdk import App


def test_app():
    App(
        name='test-app',
        help='This is a test app',
        app_image='fake-image'
    )
