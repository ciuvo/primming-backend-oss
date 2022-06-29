
class ConditionalMultiField {

     constructor(baseField, dependsOnName) {
        this.baseField = baseField;
        this.baseFieldParent = baseField.parentElement;
        this.dependsOnName = dependsOnName;

        const fieldSet = this.baseField.parentElement.parentElement.parentElement.parentElement;
        this.dependsOnField = fieldSet.querySelector('[name="' + dependsOnName + '"]');
        this.update();
        this.dependsOnField.addEventListener("change", () => {this.update()});
     }

     /**
      * update the number of fields based on the dependsOn field
      */
     update() {
        let number = parseInt(this.dependsOnField.value);
        if (isNaN(number)) number = 0;

        if (number === 0) {
            this.baseFieldParent.parentElement.style.display = "None";
            this.baseField.value = "";
        } else {
            this.baseFieldParent.parentElement.style.display = "";
        }

        let children = this.baseFieldParent.children;

        while (children.length > number) {
            this.baseFieldParent.removeChild(children[children.length - 1]);
        }

        while (children.length < number) {
            let clone = this.baseField.cloneNode();
            clone.value = "";
            this.baseFieldParent.appendChild(clone);
        }
    }
}

window.addEventListener('load', function() {
    // hook up a listener for each matching element
    document.querySelectorAll("[data-depends-on]").forEach((e) => {
        const value = e.attributes["data-depends-on"].value;
        if (value) {
            new ConditionalMultiField(e, value);
        }
    });
});
