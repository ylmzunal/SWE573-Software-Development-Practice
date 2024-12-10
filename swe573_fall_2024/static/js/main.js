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


// Add this to your static/js/main.js file
document.addEventListener('DOMContentLoaded', function() {
    // Handle post editing
    document.querySelectorAll('.edit-post-btn').forEach(button => {
        button.addEventListener('click', function() {
            const postId = this.dataset.postId;
            window.location.href = `/post/${postId}/edit/`;
        });
    });

    // Handle comment editing
    document.querySelectorAll('.edit-comment-btn').forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.dataset.commentId;
            window.location.href = `/comment/${commentId}/edit/`;
        });
    });

    // Handle edit post form submission
    const editPostForm = document.getElementById('edit-post-form');
    if (editPostForm) {
        editPostForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const postId = window.location.pathname.split('/')[2];

            try {
                const response = await fetch(`/post/${postId}/edit/`, {
                    method: 'POST',
                    body: formData,
                });
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = `/post/${postId}/`;
                } else {
                    alert('Error updating post: ' + JSON.stringify(data.errors));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error updating post');
            }
        });
    }

    // Handle edit comment form submission
    const editCommentForm = document.getElementById('edit-comment-form');
    if (editCommentForm) {
        editCommentForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const commentId = window.location.pathname.split('/')[2];

            try {
                const response = await fetch(`/comment/${commentId}/edit/`, {
                    method: 'POST',
                    body: formData,
                });
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = document.referrer;
                } else {
                    alert('Error updating comment: ' + data.message);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error updating comment');
            }
        });
    }
});