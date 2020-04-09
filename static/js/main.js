// Automatically populate the slug fields in create forms.
(function autoSlug() {
    'use strict';

    var titleInput = document.querySelector('form.create #id_title');
    if(titleInput){
        titleInput.addEventListener('input', function (e) {
            document.getElementById('id_slug').value = window.URLify(this.value);
        });
    }
    var nameInput = document.querySelector('form.create #id_name');
    if(nameInput){
        nameInput.addEventListener('input', function (e) {
            document.getElementById('id_slug').value = window.URLify(this.value);
        });
    }
    var resourceInput = document.querySelector('form.create #id_resource');
    if(resourceInput){
        resourceInput.addEventListener('input', function (e) {
            document.getElementById('id_resource_slug').value = window.URLify(this.value);
        });
    }
})();

//Check the validity of an agreement body.
(function checkBodyValid() {
    var bodyInput = document.querySelector('#id_body');
    if(bodyInput){
        bodyInput.addEventListener('change', function (e) {
            var testElem = document.createElement('div');
            testElem.innerHTML = bodyInput.value;
            if(testElem.innerHTML !== bodyInput.value){
                this.parentNode.classList.add('errors');
                var errorList = this.parentNode.querySelector('ul.errorlist');
                if(!errorList){
                    errorList = document.createElement('ul');
                    errorList.classList.add('errorlist');
                    this.insertAdjacentElement('afterend', errorList);
                }
                var invalidHttpError = document.createElement('li');
                invalidHttpError.setAttribute('id', '#body-invalid-http-error');
                var invalidHttpErrorContent = document.createTextNode('Invalid HTML.');
                invalidHttpError.appendChild(invalidHttpErrorContent);
                errorList.appendChild(invalidHttpError);
            } else {
                this.parentNode.classList.remove('errors');
                var oldInvalidHttpError = document.getElementById('#body-invalid-http-error');
                if(oldInvalidHttpError){
                    var oldErrorList = this.parentNode.querySelector('ul.errorlist');
                    oldErrorList.removeChild(oldInvalidHttpError);
                    if(oldErrorList.getElementsByTagName("li").length == 0){
                        this.parentNode.removeChild(oldErrorList);
                    }
                }
            }
        });
    }
})();
