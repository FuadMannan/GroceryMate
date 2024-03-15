document.addEventListener("DOMContentLoaded", function () {
    const itemList = document.getElementById('grocery-list-items-container');

    // Add event listeners to Add new Item button
    document.querySelectorAll('#add-new-item-btn').forEach(button => {
        button.addEventListener('click', function () {
            let addListModal = new bootstrap.Modal(document.getElementById("add-item-modal"), {});
            addListModal.show();
        });
    });

    // Add event listeners to all delete buttons
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function () {
            const listItem = this.closest('.list-group-item');
            deleteItem(listItem);
        });
    });

    // Save new list item
    document.getElementById('search-btn').addEventListener('click', function () {
        let itemName = $("#search-item-input").val();

        // Remove previous search results
        let result_table = document.getElementById('searchResults');
        if (result_table != null) {
            result_table.remove();
        }

        response = find_items(itemName)['items'];

        // Show search results
        const search_results = format_search_results(response);
        const inputGroup = document.getElementsByClassName('input-group')[0];
        inputGroup.insertAdjacentHTML('afterend', search_results);

        // Add item to list and update page
        document.querySelectorAll('[data-price-id]').forEach(button => {
            button.addEventListener('click', function () {
                let listID = document.URL.split('items/')[1].split('#')[0];
                let priceID = this.getAttribute('data-price-id');
                let listItemID = add_item(listID, priceID)['id'];
                let li = this.closest('li');

                const new_item = format_list_item(li.children[0].textContent.trim(), li.children[1].textContent, li.children[2].textContent, listItemID);

                itemList.insertAdjacentHTML('beforeend', new_item);
                document.getElementById('searchResults').remove();

                // Add event listeners to all delete buttons
                document.querySelectorAll('.delete-btn').forEach(button => {
                    button.addEventListener('click', function () {
                        const listItem = this.closest('.list-group-item');
                        deleteItem(listItem);
                    });
                });

                var popoverTriggerList = [].slice.call(document.querySelectorAll('.nutrition-info-btn'));
                var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
                    name = popoverTriggerEl.dataset.name;
                    return new bootstrap.Popover(popoverTriggerEl, {
                        animation: true,
                        title: 'Nutrition Information',
                        content: getTable(name),
                        trigger: 'focus',
                        html: true,
                    });
                });
            });
        });
    });

    // Function to handle searching for items
    function find_items(itemName) {
        return ajax_req("POST", "/find_products/", {name: itemName});
    }

    // Function to handle adding item to list
    function add_item(listID, priceID) {
        return ajax_req("POST", "/add_grocery_list_item/", {listID: listID, priceID: priceID});
    }

    // Function to handle item deletion
    function deleteItem(item) {
        if (confirm('Are you sure you want to remove this item?')) {
            delete_item(item.dataset.id)
            itemList.removeChild(item);
        }
    }

    function delete_item(listItemId) {
        ajax_req("POST", "/delete_grocery_list_item/" + listItemId, {});
    }

    function format_search_results(results) {
        let result_table = `<div id="searchResults" class="grocery-list-items-container pb-5">
            <h5>Products</h5>
            <span class="container d-flex px-3">
                <span class="col-6">Name</span>
                <span class="text-center col-2">Chain</span>
                <span class="text-center col-2">Price</span>
                <span class="col-2"></span>
            </span>
            <ul class="list-group">`;
        for (i in results) {
            result_table += `<li class="list-group-item d-flex justify-content-between align-items-center">
                <a href="#" class="grocery-list-item-link col-6">
                    ${results[i]['ProductName']}
                </a>
                <span class="item-name text-center col-2">${results[i]['ChainName']}</span>
                <span class="item-name text-center col-2">$${results[i]['Price']}</span>
                <div class="btn-group col-2" role="group">
                    <button class="btn btn-primary" type="button" data-price-id="${results[i]['PriceID']}">
                        Add
                    </button>
                </div>
            </li>`
        }
        result_table += `</ul></div>`;
        return result_table;
    }

    function format_list_item(product, chain, price, listItemID) {
        let item = `<li class="list-group-item d-flex justify-content-between align-items-center" data-id=${listItemID}>
            <a href="#" class="grocery-list-item-link col-6">
                <span class="item-name">${product}</span>
            </a>
            <span class="item-name text-center col-2">${chain}</span>
            <span class="item-name text-center col-2">${price}</span>
            <div class="btn-group col-2" role="group">
                <button type="button" class="btn btn-outline-primary rename-btn nutrition-info-btn" data-name=${product}>Nutrition
                    Info</i>
                </button>
                <button type="button" class="btn btn-outline-danger delete-btn"><i class="fas fa-trash-alt"></i>
                </button>
            </div>
        </li>`;
        return item;
    }

    var popoverTriggerList = [].slice.call(document.querySelectorAll('.nutrition-info-btn'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        name = popoverTriggerEl.dataset.name;
        return new bootstrap.Popover(popoverTriggerEl, {
            animation: true, title: 'Nutrition Information', content: getTable(name), trigger: 'focus', html: true,
        });
    });
});

function saveItem(itemName, listId) {
    return ajax_req("POST", `/save_grocery_item/${listId}`, {name: itemName});
}

function getTable(name) {
    data = ajax_req("GET", `/get_nutrition_info/${name}`);

    // Create a table element
    var table = document.createElement('table');
    table.className = 'table table-hover';

    // Create table header
    var thead = document.createElement('thead');
    var tr = document.createElement('tr');
    var th1 = document.createElement('th');
    th1.textContent = 'Nutrient';
    var th2 = document.createElement('th');
    th2.textContent = 'Value';
    tr.appendChild(th1);
    tr.appendChild(th2);
    thead.appendChild(tr);
    table.appendChild(thead);

    // Create table body
    var tbody = document.createElement('tbody');
    for (var key in data) {
        var tr = document.createElement('tr');
        var td1 = document.createElement('td');
        td1.textContent = key.replace(/_/g, ' ').toUpperCase();
        var td2 = document.createElement('td');
        td2.textContent = data[key];
        tr.appendChild(td1);
        tr.appendChild(td2);
        tbody.appendChild(tr);
    }
    table.appendChild(tbody);

    return table;
}