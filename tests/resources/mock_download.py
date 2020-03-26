# This method mocks requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == 'https://test_url.org/test_1234.pdf':
        return MockResponse({}, 200)

    return MockResponse(None, 404)
