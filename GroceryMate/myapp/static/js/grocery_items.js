document.addEventListener("DOMContentLoaded", function () {
    const itemList = document.getElementById('grocery-list-items-container');

    document.getElementById('add-item-modal').addEventListener('hidden.bs.modal', (event) => {
        $('.modal-title')[0].textContent = 'Prices';
        $('#prices-list').remove();
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

        const productsResponse = get_products(itemName)['items'];

        // Show search results
        const products_list = format_product_results(productsResponse);
        const inputGroup = document.getElementsByClassName('input-group')[0];
        inputGroup.insertAdjacentHTML('afterend', products_list);

        // Add event listeners to Add new Item button
        document.querySelectorAll('[data-product-id]').forEach(button => {
            button.addEventListener('click', function () {
                const productRow = this.closest('li').children;
                const productID = this.getAttribute('data-product-id');
                const pricesResponse = get_prices(productID)['items'];
                const prices_list = format_price_results(pricesResponse);
                const priceListModal = new bootstrap.Modal(document.getElementById("add-item-modal"), {});
                $('.modal-title')[0].textContent += ` for ${productRow[0].text.trim()}`;
                $('.modal-body')[0].children[0].insertAdjacentHTML('afterend', prices_list);
                priceListModal.show();
                // Add item to list and update page
                document.querySelectorAll('[data-price-id]').forEach(button => {
                    button.addEventListener('click', function () {
                        priceListModal.hide();
                        $('.modal-title')[0].textContent = 'Prices';
                        $('#prices-list').remove();
                        $('#searchResults').remove();
                        const productName = productRow[0].text.trim();
                        const brandName = productRow[1].textContent;
                        const listID = document.URL.split('items/')[1].split('#')[0];
                        const priceID = this.getAttribute('data-price-id');
                        const children = this.closest('li').children;
                        const price = children[1].textContent;
                        const quantity = children[2].children[0].value;
                        const listItemID = add_item(listID, priceID, quantity)['id'];

                        const new_item = format_list_item(productName, brandName, quantity, '', price, listItemID);
                        itemList.insertAdjacentHTML('beforeend', new_item);


                        // Add event listener for new delete button
                        const new_elem = document.querySelector(`[data-id="${listItemID}"]`);
                        new_elem.querySelector('.delete-btn').addEventListener('click', function () {
                            const listItem = this.closest('.list-group-item');
                            deleteItem(listItem);
                        });

                        // Add nutrition info popover for new item
                        new bootstrap.Popover(new_elem.querySelector('.nutrition-info-btn'), {
                            animation: true,
                            title: 'Nutrition Information',
                            content: getTable(productName),
                            trigger: 'focus',
                            html: true,
                        });
                    });
                });
            });
        });

    });

    // Function to handle searching for items
    function get_products(itemName) {
        return ajax_req("POST", "/get_products/", {name: itemName});
    }

    function get_prices(productID) {
        return ajax_req("POST", "/get_prices/", {id: productID})
    }

    // Function to handle adding item to list
    function add_item(listID, priceID, quantity) {
        return ajax_req("POST", "/add_grocery_list_item/", {listID: listID, priceID: priceID, quantity: quantity});
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

    function format_product_results(results) {
        let result_table = `<div id="searchResults" class="grocery-list-items-container pb-5">
            <h5>Products</h5>
            <span class="container d-flex px-3">
                <span class="col-5">Name</span>
                <span class="text-center col-5">Brand</span>
                <span class="col-2"></span>
            </span>
            <ul class="list-group">`;
        for (i in results) {
            result_table += `<li class="list-group-item d-flex justify-content-between align-items-center">
                <a href="#" class="grocery-list-item-link col-5">
                    ${results[i]['ProductName']}
                </a>
                <span class="text-center col-5">${results[i]['BrandName']}</span>
                <div class="btn-group col-2" role="group">
                    <button class="btn btn-primary" type="button" data-product-id="${results[i]['ProductID']}">
                        View Prices
                    </button>
                </div>
            </li>`;
        }
        result_table += `</ul></div>`;
        return result_table;
    }

    function format_price_results(results) {
        let result_table = `<ul id="prices-list" class="list-group">`;
        for (i in results) {
            result_table += `<li class="list-group-item d-flex justify-content-between align-items-center">
                <span class="col">${results[i]['ChainName']}</span>
                <span class="col">$${results[i]['Price']}</span>
                <span class="col">
                    <input id="quantity" type="number" min="1" max="100" value="1" class="form-control w-75">
                </span>
                <div class="btn-group col" role="group">
                    <button class="btn btn-primary" type="button" data-price-id="${results[i]['PriceID']}">
                        Add Item
                    </button>
                </div>
            </li>`;
        }
        result_table += `</ul></div>`;
        return result_table;
    }

    function format_list_item(productName, brandName, quantity, unit, price, listItemID) {
        let item = `<li class="list-group-item d-flex align-items-center" data-id=${listItemID}>
            <a href="#" class="grocery-list-item-link col">
                ${productName}
            </a>
            <span class="text-center col">${brandName}</span>
            <span class="text-center col">${quantity}</span>
            <span class="text-center col">${unit}</span>
            <span class="text-center col">${price}</span>
            <div class="btn-group col" role="group">
                <button type="button" class="btn btn-outline-primary rename-btn nutrition-info-btn" data-name="${productName}">
                    Nutrition Info</i>
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