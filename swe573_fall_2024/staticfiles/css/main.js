console.log("main.js loaded successfully");

// Event listener kontrolü
document.getElementById('create-post-btn').addEventListener('click', function () {
    console.log("Create post button clicked");
});


document.getElementById('create-post-btn').addEventListener('click', function () {
    fetch('/create-post-form/')
        .then(response => response.text())
        .then(html => {
            const mainContent = document.getElementById('main-content');
            mainContent.innerHTML = html;

            // Formu dinamik olarak gönderme işlemi
            const postForm = mainContent.querySelector('form');
            postForm.addEventListener('submit', async function (event) {
                event.preventDefault();

                const formData = new FormData(postForm);

                const response = await fetch('/create-post/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    },
                    body: formData,
                });

                if (response.ok) {
                    const post = await response.json(); // Yeni post verisini al
                    loadPostDetails(post.id); // Yeni postun detaylarını yükle
                } else {
                    alert('Post creation failed!');
                }
            });
        })
        .catch(error => {
            console.error('Error loading post form:', error);
        });
});