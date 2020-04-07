(function autoSlug() {
    var titleInput = document.querySelector("form.create #id_title")
    if(titleInput){
        titleInput.addEventListener('input', function (e) {
            document.getElementById("id_slug").value = window.URLify(this.value);
        });
    }
    var titleInput = document.querySelector("form.create #id_resource")
    if(titleInput){
        titleInput.addEventListener('input', function (e) {
            document.getElementById("id_resource_slug").value = window.URLify(this.value);
        });
    }
    var titleInput = document.querySelector("form.create #id_name")
    if(titleInput){
        titleInput.addEventListener('input', function (e) {
            document.getElementById("id_slug").value = window.URLify(this.value);
        });
    }
})();
