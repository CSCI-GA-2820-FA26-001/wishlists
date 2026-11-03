Feature: Wishlist administration
  As an administrator
  I want to create and retrieve wishlists
  So that I can verify that a customer's wishlist was saved

  Scenario: Create a wishlist and retrieve it after refreshing
    Given I am on the wishlist administration page
    When I create a new wishlist for customer 1001
    Then I see the saved wishlist details
    When I refresh and retrieve the saved wishlist
    Then I see the saved wishlist details

  Scenario: Duplicate wishlist names show an error
    Given I am on the wishlist administration page
    When I create a new wishlist for customer 1001
    Then I see the saved wishlist details
    When I submit the same wishlist again
    Then I see an error containing "Wishlist already exists"

  Scenario: A missing wishlist shows an error
    Given I am on the wishlist administration page
    When I retrieve wishlist 2147483647
    Then I see an error containing "was not found"

  Scenario: User-provided markup is displayed as text
    Given I am on the wishlist administration page
    When I create a wishlist with HTML in its note
    Then the note is displayed as text
