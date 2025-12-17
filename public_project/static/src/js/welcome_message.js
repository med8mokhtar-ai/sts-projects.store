/** @odoo-module **/

import { registry } from '@web/core/registry';

const WelcomeMessageService = {
    dependencies: ['notification'],
    async start(env) {
        const userName = env.services.user.name;
        env.services.notification.add(
            `Bienvenue à la plateforme de suivi d’exécution des contrats, ${userName}`,
            { type: 'info' }
        );
    },
};

registry.category('services').add('welcome_message', WelcomeMessageService);
