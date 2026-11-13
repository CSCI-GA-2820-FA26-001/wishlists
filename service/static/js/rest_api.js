$(function () {

    // ****************************************
    //  U T I L I T Y   F U N C T I O N S
    // ****************************************

    // Updates the form with data from the response
    function update_form_data(res) {
        $("#wishlist_id").val(res.id);
        $("#wishlist_name").val(res.name);
        $("#wishlist_customer_id").val(res.customer_id);
        $("#wishlist_note").val(res.note ? res.note : "");
        $("#wishlist_item_count").val(res.items ? res.items.length : 0);
    }

    // Clears all form fields except the ID
    function clear_form_data() {
        $("#wishlist_name").val("");
        $("#wishlist_customer_id").val("");
        $("#wishlist_note").val("");
        $("#wishlist_item_count").val("");
    }

    // Updates the flash message area
    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    // Shows the error message returned by the service
    function flash_error(res) {
        if (res.responseJSON && res.responseJSON.message) {
            flash_message(res.responseJSON.message);
        } else {
            flash_message("Server error!");
        }
    }

    // Escapes text before putting it in the results table
    function escape_html(text) {
        return $("<div>").text(text === null || text === undefined ? "" : text).html();
    }

    // Builds the JSON payload from the form.
    // customer_id is sent as a number when it looks like one; anything else is
    // sent as typed so the service can reject it with a 400.
    function form_payload() {
        let customer_id = $("#wishlist_customer_id").val().trim();
        let note = $("#wishlist_note").val();
        return {
            "name": $("#wishlist_name").val(),
            "customer_id": /^\d+$/.test(customer_id) ? parseInt(customer_id, 10) : customer_id,
            "note": note ? note : null
        };
    }

    // ****************************************
    // Create a Wishlist
    // ****************************************

    $("#create-btn").click(function () {

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "POST",
            url: "/wishlists",
            contentType: "application/json",
            data: JSON.stringify(form_payload()),
        });

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_error(res)
        });
    });


    // ****************************************
    // Update a Wishlist
    // ****************************************

    $("#update-btn").click(function () {

        let wishlist_id = $("#wishlist_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "PUT",
            url: `/wishlists/${wishlist_id}`,
            contentType: "application/json",
            data: JSON.stringify(form_payload())
        })

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_error(res)
        });

    });

    // ****************************************
    // Retrieve a Wishlist
    // ****************************************

    $("#retrieve-btn").click(function () {

        let wishlist_id = $("#wishlist_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/wishlists/${wishlist_id}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_error(res)
        });

    });

    // ****************************************
    // Delete a Wishlist
    // ****************************************

    $("#delete-btn").click(function () {

        let wishlist_id = $("#wishlist_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "DELETE",
            url: `/wishlists/${wishlist_id}`,
            contentType: "application/json",
            data: '',
        })

        ajax.done(function(res){
            clear_form_data()
            flash_message("Wishlist has been Deleted!")
        });

        ajax.fail(function(res){
            flash_message("Server error!")
        });
    });

    // ****************************************
    // Clear all items from a Wishlist (action)
    // ****************************************

    $("#clear_items-btn").click(function () {

        let wishlist_id = $("#wishlist_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "PUT",
            url: `/wishlists/${wishlist_id}/clear`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_error(res)
        });
    });

    // ****************************************
    // Clear the form
    // ****************************************

    $("#clear-btn").click(function () {
        $("#wishlist_id").val("");
        $("#flash_message").empty();
        clear_form_data()
    });

    // ****************************************
    // Search for Wishlists
    // ****************************************

    $("#search-btn").click(function () {

        let customer_id = $("#wishlist_customer_id").val().trim();
        let name = $("#wishlist_name").val().trim();

        // The service filters by customer_id; a name typed in the form
        // narrows the results shown on the page.
        let queryString = ""
        if (customer_id) {
            queryString = 'customer_id=' + encodeURIComponent(customer_id)
        }

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/wishlists?${queryString}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            let wishlists = res;
            if (name) {
                wishlists = res.filter(function (wishlist) { return wishlist.name == name; });
            }

            $("#search_results").empty();
            let table = '<table class="table table-striped" cellpadding="10">'
            table += '<thead><tr>'
            table += '<th class="col-md-1">ID</th>'
            table += '<th class="col-md-3">Name</th>'
            table += '<th class="col-md-2">Customer ID</th>'
            table += '<th class="col-md-4">Note</th>'
            table += '<th class="col-md-2">Items</th>'
            table += '</tr></thead><tbody>'
            let firstWishlist = "";
            for(let i = 0; i < wishlists.length; i++) {
                let wishlist = wishlists[i];
                table +=  `<tr id="row_${i}"><td>${wishlist.id}</td><td>${escape_html(wishlist.name)}</td>`
                table +=  `<td>${wishlist.customer_id}</td><td>${escape_html(wishlist.note)}</td><td>${wishlist.items.length}</td></tr>`;
                if (i == 0) {
                    firstWishlist = wishlist;
                }
            }
            table += '</tbody></table>';
            $("#search_results").append(table);

            // copy the first result to the form
            if (firstWishlist != "") {
                update_form_data(firstWishlist)
            }

            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_error(res)
        });

    });

})
