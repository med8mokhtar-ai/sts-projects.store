/** @odoo-module **/
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
export class FeedbackListController extends ListController {
    setup() {
        debugger;
        super.setup();
    }
    OnTestClick() {
        // Return an object representing the
        console.log(this.props);


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
registry.category("views").add("feedback_button_in_tree", {
    ...listView,
    Controller: FeedbackListController,
    buttonTemplate: "button_feedback.ListView.Buttons",
});
