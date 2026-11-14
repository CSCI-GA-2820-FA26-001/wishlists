Feature: Wishlist Admin UI
  As an eCommerce manager
  I need a web page to manage wishlists
  So that I can help customers without calling the REST API directly

  Background:
    Given the following wishlists
      | name     | customer_id | note        |
      | Birthday | 1001        | Gift ideas  |
      | Holiday  | 1001        | Winter trip |
      | Books    | 2002        | Reading     |

  Scenario: Retrieve a wishlist
    When I visit the "Home Page"
    And I set the "Name" to "Birthday"
    And I press the "Search" button
    Then I should see the message "Success"
    When I copy the "Id" field
    And I press the "Clear" button
    And I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "Birthday" in the "Name" field
    And I should see "1001" in the "Customer ID" field
    And I should see "Gift ideas" in the "Note" field
