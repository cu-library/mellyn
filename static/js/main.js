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

// Check the validity of an HTML input.
(function checkHTMLInputValid(){
    'use strict';

    function addValidationEventListener(element){
        element.addEventListener('input', function (e){
            const INVALID_MESSAGE_ID = `id_${this.id}_error_message_invalid_html`;
            const parser = new DOMParser();
            // allowedTags is extracted from the model and passed through the view.
            const allowedTags = this.dataset.allowedTags.split(',');
            // Parse the text.
            let doc = parser.parseFromString(this.value, 'text/html');
            // Did the parser return an error document?
            let parseErrors = doc.getElementsByTagName('parsererror');
            if(parseErrors.length > 0){
                window.setErrorOnElement(this.id, INVALID_MESSAGE_ID, 'Invalid HTML.');
                return;
            }
            // Did the parser have to 'fix' the input?
            if(doc.body.innerHTML!==this.value){
                window.setErrorOnElement(this.id, INVALID_MESSAGE_ID, 'Invalid HTML.');
                return;
            }
            // Did the parser encounter any 'bad' tags?
            let allElems = doc.body.getElementsByTagName('*');
            for(const elem of allElems){
                const tag = elem.tagName.toLowerCase();
                if(!allowedTags.includes(tag)){
                    window.setErrorOnElement(this.id, INVALID_MESSAGE_ID, 'Invalid HTML tag: ' + tag);
                    return;
                }
            }
            // All good, remove previous errors if found.
            window.removeErrorOnElement(this.id, INVALID_MESSAGE_ID);
        });
    }

    const htmlInputsIds = ['id_body', 'id_description'];
    for (const htmlInputId of htmlInputsIds) {
        // Does this page have an HTML text area?
        const htmlInput = document.getElementById(htmlInputId);
        // If not, return early.
        if(!htmlInput){
            continue;
        }
        addValidationEventListener(htmlInput);
        // Run it once, manually, on page load.
        var event = new Event('input');
        htmlInput.dispatchEvent(event);
    }
})();
