/** @odoo-module **/
import { registry } from "@web/core/registry";
import { progressBarField, ProgressBarField } from "@web/views/fields/progress_bar/progress_bar_field";
const formatters = registry.category("formatters");

export class ProgressBarFieldNoRounding extends ProgressBarField {

    // Override the formatCurrentValue method to disable rounding and display exact float values
    formatCurrentValue(humanReadable = !this.state.isEditing) {
        return this.currentValue.toFixed(2);
    }

    // Override the formatMaxValue method to disable rounding and display exact float values
    formatMaxValue(humanReadable = !this.state.isEditing) {
        return this.maxValue.toFixed(2);
    }

    // Override the onValueChange method to prevent automatic integer conversion
    onValueChange(value, fieldName) {
        let parsedValue;
        try {
            parsedValue = parseFloat(value);  // Parse the value as a float
        } catch {
            this.props.record.setInvalidField(this.props.name);
            return;
        }

        // Update the record with the parsed float value
        this.props.record.update({ [fieldName]: parsedValue }, { save: this.props.readonly });
    }
}
/**
 * Define the template name used on the component.
 */
export const progressBarFieldNoRounding = {
    ...progressBarField,
    component: ProgressBarFieldNoRounding,
};

registry.category("fields").add("progressbar_no_rounding", progressBarFieldNoRounding);
