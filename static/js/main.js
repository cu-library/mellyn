// Automatically populate the slug fields in create forms.
(function autoSlug() {
    'use strict';

    var titleInput = document.querySelector("form.create #id_title");
    if(titleInput){
        titleInput.addEventListener('input', function (e) {
            document.getElementById("id_slug").value = window.URLify(this.value);
        });
    }
    var nameInput = document.querySelector("form.create #id_name");
    if(nameInput){
        nameInput.addEventListener('input', function (e) {
            document.getElementById("id_slug").value = window.URLify(this.value);
        });
    }
    var resourceInput = document.querySelector("form.create #id_resource");
    if(resourceInput){
        resourceInput.addEventListener('input', function (e) {
            document.getElementById("id_resource_slug").value = window.URLify(this.value);
        });
    }
})();
