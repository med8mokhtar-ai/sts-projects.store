/** @odoo-module **/
import { registry } from "@web/core/registry";
import { progressBarField, ProgressBarField } from "@web/views/fields/progress_bar/progress_bar_field";

export class ProjectCustomProgressBarField extends ProgressBarField {
    // setup() {
    //     super.setup();
    //     this.user = useService("user");
    //     // this.orm = useService("orm");
    //     // this.actionService = useService("action");
    //     // this.askRecurrenceUpdatePolicy = useAskRecurrenceUpdatePolicy();

    //     // onWillStart(this.onWillStart);
    // }
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
    get progressBarColorClass() {
        // if (this.currentValue > this.maxValue) {
        //     return super.progressBarColorClass;
        // }

        if (this.currentValue <= 50) {
            return "bg-primary";
        } else if (this.currentValue > 50 && this.currentValue <= 75) {
            return "bg-success";
        } else if (this.currentValue > 75 && this.currentValue <= 100) {
            return "bg-warning";
        } else if (this.currentValue > 100) {
            return "bg-danger";
        } else {
            return "bg-info";
        }
        // return this.currentValue < 80 ? "bg-success" : "bg-warning";
    }
}
/**
 * Define the template name used on the component.
 */
export const projectCustomProgressBarField = {
    ...progressBarField,
    component: ProjectCustomProgressBarField,
};

registry.category("fields").add("project_custom_progressbar", projectCustomProgressBarField);
