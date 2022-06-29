class ConditionallyVisible {

    constructor(field, condition_value) {
        this.field = field;
        this.condition_value = condition_value;
        this.parentElement = field.parentElement.parentElement.parentElement;
    }

    on_change(element) { /* implemented by subclasses */ }

    /**
     * update the number of fields based on the dependsOn field
     */
    update(visible) {
        if (visible) {
            this.parentElement.style.display = "";
        } else {
            this.parentElement.style.display = "none";
            if (this.field.type === "checkbox" || this.field.type === "radio") {
                this.field.checked = false;
                
                const changeEvent = document.createEvent("HTMLEvents");
                changeEvent.initEvent("change", false, true);
                this.field.dispatchEvent(changeEvent);
            }
        }
    }
}

class ConditionallyVisibleIfChecked extends ConditionallyVisible {
    on_change(element) {
        this.update(element.checked && (this.condition_value === element.value));
    }
}

window.addEventListener('load', function () {
    // hook up a listener for each matching element
    document.querySelectorAll("[data-conditional-if-checked-name]").forEach((e) => {
        const name = e.attributes["data-conditional-if-checked-name"].value;
        const value = e.attributes["data-conditional-if-checked-value"].value;
        const handler = new ConditionallyVisibleIfChecked(e, value);
        const selector = 'input[name="' + name + '"]';

        const typeTestElement = document.querySelector(selector);
        if (!typeTestElement) return;
        if (typeTestElement.type == "radio") {
            // address the radio button issue (no events on deselect), setup a change listener for each button
            document.querySelectorAll(selector).forEach((inputElement) => {
                if (inputElement.value === value) {
                    handler.on_change(inputElement);
                }
                inputElement.addEventListener("change", (e) => { handler.on_change(e.target); });
            });
        } else {
            // only setup listener for matching element
            document.querySelectorAll(selector).forEach((inputElement) => {
                if (inputElement.value === value) {
                    handler.on_change(inputElement);
                    inputElement.addEventListener("change", (e) => { handler.on_change(e.target); });
                }
            });
        }

    });
});