/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
export class MilestoneListController extends ListController {
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
                    name: 'Analyse des jalons',
                    type: 'ir.actions.act_window',
                    res_model: 'milestone.wizard',
                    view_mode: 'graph',
                    view_type: 'graph',
                    domain: [['project_id', '=', activeId]],
                    views: [[false, 'graph']],
                    res_id: false,
                    context: {
                        'group_by': [], 'graph_measure': 'measure', 'graph_mode': 'line',
                        'graph_groupbys': ['milestone', 'type'], 'graph_order': 'date_start, id', 'graph_stacked': false,
                        'graph_cumulated': true
                    },
                });
            }
        } else {
            // Handle the case where context is undefined
            console.error("Context is undefined");
        }
    }
}
registry.category("views").add("button_in_tree", {
    ...listView,
    Controller: MilestoneListController,
    buttonTemplate: "button_milestone.ListView.Buttons",
});