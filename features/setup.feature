@setup
Feature: Browser test environment
  As a developer
  I need a working browser test environment
  So that teammates can add their own acceptance scenarios

  Scenario: Open a local test page in a real browser
    When I open the local BDD test page
    Then the browser title is "Wishlist BDD Smoke Test"
