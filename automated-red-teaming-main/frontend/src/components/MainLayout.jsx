
import Header from './Header';
import { Outlet } from 'react-router-dom';

export default function MainLayout() {

    return (
        <div className="flex flex-col h-screen overflow-hidden">
            <Header title='Automated Red Teaming Demo' />
            <main className="overflow-hidden flex-1">
                <Outlet />
            </main>
        </div>
    );
}