Feature: Gherkin Example Test

Scenario: Retrieving a specific study
  When a 'GET' request is sent to 'studies/Study_000001'
  Then the response has status code '200'
  And the response is a JSON body containing
    """
      {
        "uid": "Study_000001"
      }
    """