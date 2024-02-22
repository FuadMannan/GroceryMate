document.addEventListener("DOMContentLoaded", function () {
    const itemList = document.getElementById('grocery-lists-container');

    // Add event listeners to Add new List button
    document.querySelectorAll('#add-new-list-btn').forEach(button => {
        button.addEventListener('click', function () {
            let addListModal = new bootstrap.Modal(document.getElementById("add-list-modal"), {});
            addListModal.show();
        });
    });

    // Add event listeners to all rename buttons
    document.querySelectorAll('.rename-btn').forEach(button => {
        button.addEventListener('click', function () {
            const listItem = this.closest('.list-group-item');
            renameItem(listItem);
        });
    });

    // Add event listeners to all delete buttons
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function () {
            const listItem = this.closest('.list-group-item');
            deleteItem(listItem);
        });
    });

    // Save new list
    document.getElementById('add-new-list-modal-save').addEventListener('click', function () {
        let listName = $("#add-new-list-input").val();

        save_list(listName);

        const elements = `<li class="list-group-item d-flex justify-content-between align-items-center">
            <span class="item-name">${listName}</span>
            <div class="btn-group" role="group">
                <button type="button" class="btn btn-outline-primary rename-btn"><i class="fas fa-edit"></i>
                </button>
                <button type="button" class="btn btn-outline-danger delete-btn"><i class="fas fa-trash-alt"></i>
                </button>
            </div>
        </li>`
        itemList.insertAdjacentHTML('beforeend', elements);

        let myModalEl = document.getElementById('add-list-modal');
        let modal = bootstrap.Modal.getInstance(myModalEl)
        modal.hide();

        // Add event listeners to all rename buttons
        document.querySelectorAll('.rename-btn').forEach(button => {
            button.addEventListener('click', function () {
                const listItem = this.closest('.list-group-item');
                renameItem(listItem);
            });
        });

        // Add event listeners to all delete buttons
        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', function () {
                const listItem = this.closest('.list-group-item');
                deleteItem(listItem);
            });
        });
    });


    // Function to handle item renaming
    function renameItem(item) {
        const newName = prompt('Enter new name:');
        if (newName) {
            const itemName = item.querySelector('.item-name');
            edit_list(item.dataset.id, newName);
            itemName.textContent = newName;
        }
    }

    // Function to handle item deletion
    function deleteItem(item) {
        if (confirm('Are you sure you want to delete this item?')) {
            delete_list(item.dataset.id)
            itemList.removeChild(item);
        }
    }

});


function save_list(listName) {
    ajax_req("POST", "/save_grocery_lists/", {name: listName})
}

function delete_list(listId) {
    ajax_req("POST", "/delete_grocery_list/" + listId, {})
}

function edit_list(listId, newName) {
    ajax_req("POST", "/edit_grocery_list/" + listId, {
        name: newName,
    })
}