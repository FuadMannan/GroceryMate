document.addEventListener("DOMContentLoaded", function() {
    const itemList = document.getElementById('grocery-lists-container');

    // Function to handle item renaming
    function renameItem(item) {
      const newName = prompt('Enter new name:');
      if (newName) {
        const itemName = item.querySelector('.item-name');
        itemName.textContent = newName;
      }
    }

    // Function to handle item deletion
    function deleteItem(item) {
      if (confirm('Are you sure you want to delete this item?')) {
        itemList.removeChild(item);
      }
    }

    // Add event listeners to Add new List button
    document.querySelectorAll('#add-new-list-btn').forEach(button => {
      button.addEventListener('click', function() {
        var addListModal = new bootstrap.Modal(document.getElementById("add-list-modal"), {});
        addListModal.show();
      });
    });

    document.getElementById('add-new-list-modal-save').addEventListener('click', function() {
      const elements = `<li class="list-group-item d-flex justify-content-between align-items-center">
        <span class="item-name">Item 1</span>
        <div class="btn-group" role="group">
            <button type="button" class="btn btn-outline-primary rename-btn"><i class="fas fa-edit"></i>
            </button>
            <button type="button" class="btn btn-outline-danger delete-btn"><i class="fas fa-trash-alt"></i>
            </button>
        </div>
      </li>`
      itemList.insertAdjacentHTML('beforeend', elements);

     var myModalEl = document.getElementById('add-list-modal');
     var modal = bootstrap.Modal.getInstance(myModalEl)
     modal.hide();

     // Add event listeners to all rename buttons
    document.querySelectorAll('.rename-btn').forEach(button => {
      button.addEventListener('click', function() {
        const listItem = this.closest('.list-group-item');
        renameItem(listItem);
      });
    });

    // Add event listeners to all delete buttons
    document.querySelectorAll('.delete-btn').forEach(button => {
      button.addEventListener('click', function() {
        const listItem = this.closest('.list-group-item');
        deleteItem(listItem);
      });
    });
    });
});
