@setup
Feature: Browser test environment
  As a developer
  I need a working browser test environment
  So that teammates can add their own acceptance scenarios

  Scenario: Open the running service in a real browser
    When I open the service health endpoint
    Then the browser displays a healthy service
