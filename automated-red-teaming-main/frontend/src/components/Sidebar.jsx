import {
    Clock,
    CheckCircle,
    AlertCircle,
    Globe,
    Flag,
    Code,
    Shield,
    Activity,
    ChevronRight,
    ChevronLeft
} from 'lucide-react';
import { useState } from 'react';

export function Sidebar({ children }) {

    const [isCollapsed, setIsCollapsed] = useState(true);
    const onToggle = () => setIsCollapsed((prev) => !prev);

    return (
        <>
            {/* Toggle handle */}
            <button
                onClick={onToggle}
                aria-label={isCollapsed ? 'Open panel' : 'Close panel'}
                className={[
                    'fixed top-20 right-0 z-30',
                    'transition-transform duration-500 ease-in-out',
                    isCollapsed ? 'translate-x-0' : '-translate-x-96',
                    'p-2 bg-neutral-400/60 text-white rounded-l-lg  hover:bg-neutral-600 '
                ].join(' ')}
            >
                {isCollapsed ? <ChevronLeft className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
            </button>


            {/* Sidebar */}
            <div
                className={[
                    `fixed inset-y-0 top-18 right-0 w-96 bg-gray-50 border-l border-t shadow-lg`,
                    'flex flex-col overflow-hidden z-20',
                    'transition-transform duration-500 ease-in-out',
                    isCollapsed ? 'translate-x-full' : 'translate-x-0'
                ].join(' ')}
            >
                {children}
            </div>
        </>
    );
};
