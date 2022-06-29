
class TypeConversionWidget {

     constructor(typeSelectorElement) {
        this.typeSelector = typeSelectorElement;
        this.rootElement = this.typeSelector.parentNode.parentNode;
        this.updateVisibility();

        this.typeSelector.addEventListener("change", () => {this.updateVisibility()});
     }

     FIELD_CLASS_NAME_MAPPING = {
        "1": "field-value_bool",
        "2": "field-value_int",
        "3": "field-value_float",
        "default": "field-value_string"
     }

     updateVisibility() {
        let value = this.typeSelector.value,
            showClassName = this.FIELD_CLASS_NAME_MAPPING[value]
                            || this.FIELD_CLASS_NAME_MAPPING["default"];

        for (const className of Object.values(this.FIELD_CLASS_NAME_MAPPING)) {
            let element = this.rootElement.querySelector("." + className);

            if (className === showClassName) {
                 element.style.visibility = "";
            } else {
                 element.style.visibility = "hidden";
            }
        }
     }
}

window.addEventListener('load', function() {
    // hook up a listener for each matching element
    document.querySelectorAll(".field-value_type select").forEach((e) => {
        new TypeConversionWidget(e)
    });
});
