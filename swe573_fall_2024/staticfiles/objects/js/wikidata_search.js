document.addEventListener('DOMContentLoaded', function() {
    // Get the search box element
    const searchBox = document.querySelector('.search-box');
    
    // Create the filter button if it doesn't exist
    if (!document.querySelector('.filter-button')) {
        const filterButton = document.createElement('button');
        filterButton.type = 'button';
        filterButton.className = 'filter-button';
        filterButton.innerHTML = '<i class="fas fa-sliders-h"></i>';
        searchBox.appendChild(filterButton);
    }

    // Get the filter button and dropdown
    const filterButton = document.querySelector('.filter-button');
    const filterDropdown = document.getElementById('filterDropdown');

    // Add click event to filter button
    filterButton.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        filterDropdown.classList.toggle('show');
        
        // Position the dropdown under the search box
        if (filterDropdown.classList.contains('show')) {
            const searchBoxRect = searchBox.getBoundingClientRect();
            filterDropdown.style.top = `${searchBoxRect.bottom}px`;
            filterDropdown.style.left = `${searchBoxRect.left}px`;
            filterDropdown.style.width = `${searchBoxRect.width}px`;
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!filterDropdown.contains(e.target) && !filterButton.contains(e.target)) {
            filterDropdown.classList.remove('show');
        }
    });
}); 