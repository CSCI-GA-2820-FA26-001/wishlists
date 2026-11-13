@setup
Feature: Browser test environment
  As a developer
  I need a working browser test environment
  So that teammates can add their own acceptance scenarios

  Scenario: Open the running Wishlist Admin home page
    When I visit the "Home Page"
    Then I should see "Wishlist Admin" in the title
