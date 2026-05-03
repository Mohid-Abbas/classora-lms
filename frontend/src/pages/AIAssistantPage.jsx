import React from 'react';
import DashboardLayout from '../components/DashboardLayout';
import AIAssistant from '../components/AIAssistant';

export default function AIAssistantPage() {
    const user = JSON.parse(localStorage.getItem("current_user") || "{}");

    return (
        <DashboardLayout user={user}>
            <AIAssistant user={user} />
        </DashboardLayout>
    );
}
