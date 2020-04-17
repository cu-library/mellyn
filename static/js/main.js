/*jshint esversion: 6 */

// Automatically populate the slug fields in create forms.
(function autoSlug(){
    'use strict';

    const titleInput = document.querySelector('form.create #id_title');
    if(titleInput){
        titleInput.addEventListener('input', function (e){
            document.getElementById('id_slug').value = window.URLify(this.value);
        });
    }
    const nameInput = document.querySelector('form.create #id_name');
    if(nameInput){
        nameInput.addEventListener('input', function (e){
            document.getElementById('id_slug').value = window.URLify(this.value);
        });
    }
    const resourceInput = document.querySelector('form.create #id_resource');
    if(resourceInput){
        resourceInput.addEventListener('input', function (e){
            document.getElementById('id_resource_slug').value = window.URLify(this.value);
        });
    }
})();

// Set and remove an error on a form element.
(function setupErrorOnElementFuncs(){
    'use strict';

    function setErrorOnElement(id, errorId, errorMessage){
        const elem = document.getElementById(id);
        let errorList = elem.parentNode.querySelector('ul.errorlist');
        if(!errorList){
            errorList = document.createElement('ul');
            errorList.classList.add('errorlist');
            elem.insertAdjacentElement('afterend', errorList);
            elem.parentNode.classList.add('errors');
        }
        let err = document.getElementById(errorId);
        if(!err){
            err = document.createElement('li');
            err.setAttribute('id', errorId);
            errorList.appendChild(err);
        }
        err.textContent = errorMessage;
    }
    window.setErrorOnElement = setErrorOnElement;

    function removeErrorOnElement(id, errorId){
        let err = document.getElementById(errorId);
        if(!err){
            return;
        }
        err.remove();
        const elem = document.getElementById(id);
        let errorList = elem.parentNode.querySelector('ul.errorlist');
        if(errorList && errorList.getElementsByTagName("li").length == 0){
            errorList.remove();
            elem.parentNode.classList.remove('errors');
        }
    }
    window.removeErrorOnElement = removeErrorOnElement;

})();

// Check the validity of an agreement body.
(function checkBodyValid(){
    'use strict';

    // Does this page have the body text area?
    const bodyInput = document.getElementById('id_body');
    // If not, return early.
    if(!bodyInput){
        return;
    }

    const INVALID_MESSAGE_ID = 'id_body_error_message_invalid_html';
    const parser = new DOMParser();

    // allowedTags is extracted from the model and passed through the view.
    const allowedTags = bodyInput.dataset.allowedTags.split(',');

    bodyInput.addEventListener('input', function (e){
        // Parse the body text.
        let doc = parser.parseFromString(this.value, 'text/html');
        // Did the parser return an error document?
        let parseErrors = doc.getElementsByTagName('parsererror');
        if(parseErrors.length > 0){
            window.setErrorOnElement('id_body', INVALID_MESSAGE_ID, 'Invalid HTML.');
            return;
        }
        // Did the parser have to 'fix' the input?
        if(doc.body.innerHTML!==this.value){
            window.setErrorOnElement('id_body', INVALID_MESSAGE_ID, 'Invalid HTML.');
            return;
        }
        // Did the parser encounter any 'bad' tags?
        let allElems = doc.body.getElementsByTagName('*');
        for(const elem of allElems){
            const tag = elem.tagName.toLowerCase();
            if(!allowedTags.includes(tag)){
                window.setErrorOnElement('id_body', INVALID_MESSAGE_ID, 'Invalid HTML tag: ' + tag);
                return;
            }
        }
        // All good, remove previous errors if found.
        window.removeErrorOnElement('id_body', INVALID_MESSAGE_ID);
    });

    // Run it once, manually, on page load.
    var event = new Event('input');
    bodyInput.dispatchEvent(event);
})();
