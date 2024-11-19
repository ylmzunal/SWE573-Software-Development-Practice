document.getElementById('create-post-btn').addEventListener('click', function () {
    fetch('/create-post-form/')
        .then(response => response.text())
        .then(html => {
            const mainContent = document.getElementById('main-content');
            mainContent.innerHTML = html;

            // Post formunu dinle
            const postForm = document.getElementById('post-form');
            postForm.addEventListener('submit', function (event) {
                event.preventDefault();

                const formData = new FormData(postForm);

                fetch('/create-post/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    },
                    body: formData,
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Yeni postu listeye ekle
                            const postList = document.getElementById('post-list');
                            postList.insertAdjacentHTML('afterbegin', `
                                <div class="post" onclick="loadPostDetails(${data.post.id})">
                                    <h3>${data.post.title}</h3>
                                    <p>${data.post.content}</p>
                                    <small>By ${data.post.author}</small>
                                </div>
                            `);

                            // Post Details bölümünü güncelle
                            const mainContent = document.getElementById('main-content');
                            mainContent.innerHTML = `
                                <h2>${data.post.title}</h2>
                                <p>${data.post.content}</p>
                                <small>By ${data.post.author}</small>
                            `;
                        } else {
                            alert('Error: ' + JSON.stringify(data.errors));
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Unexpected error occurred.');
                    });
            });
        });
});