document.addEventListener('DOMContentLoaded', function() {
    initializeDropdowns();
    initializeSearchInputs();
    initializeCheckboxes();
});

function initializeDropdowns() {
    document.querySelectorAll('.dropdown-header').forEach(header => {
        header.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const dropdown = document.getElementById(targetId);
            
            // Close all other dropdowns
            document.querySelectorAll('.dropdown-content').forEach(content => {
                if (content.id !== targetId) {
                    content.classList.remove('active');
                }
            });
            
            dropdown.classList.toggle('active');
        });
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown-container')) {
            document.querySelectorAll('.dropdown-content').forEach(content => {
                content.classList.remove('active');
            });
        }
    });
}

function initializeSearchInputs() {
    document.querySelectorAll('.search-input').forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const options = this.closest('.dropdown-content').querySelectorAll('.option');
            
            options.forEach(option => {
                const text = option.textContent.toLowerCase();
                option.style.display = text.includes(searchTerm) ? 'flex' : 'none';
            });
        });
    });
}

function initializeCheckboxes() {
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const propertyType = this.name;
            updateSelectedTags(propertyType);
        });
    });
}

function updateSelectedTags(propertyType) {
    const container = document.getElementById(`selected-${propertyType}s`);
    const checkedBoxes = document.querySelectorAll(`input[name="${propertyType}"]:checked`);
    
    container.innerHTML = '';
    
    checkedBoxes.forEach(box => {
        const tag = createTag(box.nextElementSibling.textContent, () => {
            box.checked = false;
            updateSelectedTags(propertyType);
        });
        container.appendChild(tag);
    });
}

function createTag(text, onRemove) {
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.innerHTML = `
        ${text}
        <span class="tag-remove">×</span>
    `;
    tag.querySelector('.tag-remove').addEventListener('click', onRemove);
    return tag;
} 