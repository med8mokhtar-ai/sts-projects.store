/** @odoo-module */
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { registry } from '@web/core/registry';
import { kanbanView } from '@web/views/kanban/kanban_view';
export class FeedbackKanbanController extends KanbanController {
    setup() {
        super.setup();
    }
    OnTestClick() {
        // Return an object representing the
        console.log(this.props.context.active_id);


        if (this.props.context) {
            const activeId = this.props.context.active_id;
            // Now use activeId in your code
           
            if (this.props.context) {
                this.actionService.doAction({
                    type: 'ir.actions.act_url',
                    url: '/my/projects',
                });
            }
        } else {
            // Handle the case where context is undefined
            console.error("Context is undefined");
        }
    }
}
registry.category("views").add("feedback_button_in_kanban", {
    ...kanbanView,
    Controller: FeedbackKanbanController,
    buttonTemplate: "button_feedback.KanbanView.Buttons",
});
