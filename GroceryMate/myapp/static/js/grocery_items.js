document.addEventListener("DOMContentLoaded", function () {
    data = {
        "calories": 261.6,
        "serving_size_g": 100.0,
        "fat_total_g": 3.4,
        "fat_saturated_g": 0.7,
        "protein_g": 8.8,
        "sodium_mg": 495,
        "potassium_mg": 98,
        "cholesterol_mg": 0,
        "carbohydrates_total_g": 50.2,
        "fiber_g": 2.7,
        "sugar_g": 5.7,
    };


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

    var button = document.getElementById('nutrition-info')

    // Initialize popover on the button
    new bootstrap.Popover(button, {
        animation: true,
        title: 'Nutrition Information',
        content: table,
        trigger: 'focus',
        html: true,
    });

});