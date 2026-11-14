Feature: Manage wishlists through the Admin UI
  As an eCommerce manager
  I need to manage customer wishlists through the Admin UI
  So that I can help customers maintain their wishlists

  Background:
    Given the following wishlists
      | name     | customer_id |
      | Birthday | 1001        |

  Scenario: Create a wishlist
    When I visit the "Home Page"
    And I set the "Name" to "Wedding"
    And I set the "Customer ID" to "3003"
    And I press the "Create" button
    Then I should see the message "Success"
    When I copy the "ID" field
    And I press the "Clear" button
    Then the "Name" field should be empty
    When I paste the "ID" field
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "Wedding" in the "Name" field
    And I should see "3003" in the "Customer ID" field
