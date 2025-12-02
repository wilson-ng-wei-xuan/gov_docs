import {
    Clock,
    CheckCircle,
    AlertCircle,
    Globe,
    Flag,
    Code,
    Shield,
    Activity,
    LayoutDashboard 
} from 'lucide-react';
import { useApiContext } from '../hooks/useApiContext';
import { Sidebar } from './Sidebar';

export function Dashboard({ togglebutton }) {

    const { data } = useApiContext();
    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed':
                return <CheckCircle className="h-5 w-5 text-green-500" />;
            case 'in_progress':
                return <Clock className="h-5 w-5 text-yellow-500" />;
            case 'failed':
                return <AlertCircle className="h-5 w-5 text-red-500" />;
            default:
                return <AlertCircle className="h-5 w-5 text-gray-500" />;
        }
    };

    const getStageIcon = (stage) => {
        switch (stage) {
            case 'recon':
                return <Activity className="h-4 w-4" />;
            case 'fingerprinting':
                return <Shield className="h-4 w-4" />;
            default:
                return <Code className="h-4 w-4" />;
        }
    };

    const formatTaskName = (name) =>
        typeof name === 'string'
            ? name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
            : 'Unnamed Task';

    // Helper function to recursively count tasks from tree structure
    const countTreeTasks = (node) => {
        if (!node) return { total: 0, completed: 0 };
        
        let total = 1; // Count current node
        let completed = node.status === 'completed' ? 1 : 0;
        
        // Recursively count children
        if (Array.isArray(node.children)) {
            node.children.forEach(child => {
                const childCounts = countTreeTasks(child);
                total += childCounts.total;
                completed += childCounts.completed;
            });
        }
        
        return { total, completed };
    };

    // Helper function to flatten tree into array of tasks
    const flattenTree = (node) => {
        if (!node) return [];
        
        const tasks = [node];
        
        // Recursively add children
        if (Array.isArray(node.children)) {
            node.children.forEach(child => {
                tasks.push(...flattenTree(child));
            });
        }
        
        return tasks;
    };

    const taskCounts = data?.tree ? countTreeTasks(data.tree) : { total: 0, completed: 0 };
    const completedTasks = taskCounts.completed;
    const totalTasks = taskCounts.total;

    // Get flattened tasks and sort by status (incomplete first)
    const allTasks = data?.tree ? flattenTree(data.tree) : [];
    const sortedTasks = allTasks.sort((a, b) => {
        // Incomplete tasks first (not completed)
        if (a.status !== 'completed' && b.status === 'completed') return -1;
        if (a.status === 'completed' && b.status !== 'completed') return 1;
        return 0;
    });

    const sessionId = data?.session_id

    const target = data?.target ?? '—';
    const goal = data?.goal ?? '—';

    // const inputTokens =
    //     typeof data?.input_tokens === 'number' ? data.input_tokens.toLocaleString() : '0';
    // const outputTokens =
    //     typeof data?.output_tokens === 'number' ? data.output_tokens.toLocaleString() : '0';

    return (

        < Sidebar >
            
            <div
                className={[
                    'flex-1 overflow-y-auto p-4 space-y-4 transition-opacity duration-300',
                ].join(' ')}
            >
                {/* Header */}
                <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
                    <div className="mb-3">
                        <h1 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                            <LayoutDashboard className="h-5 w-5 text-purple-600" />
                            Dashboard
                        </h1>
                        <div className="text-xs text-gray-500 mt-1">{sessionId}</div>
                    </div>

                    <div className="space-y-3">
                        <div className="flex items-center gap-2 p-2 bg-blue-50 rounded">
                            <Globe className="h-4 w-4 text-blue-600" />
                            <div className="min-w-0 flex-1">
                                <div className="text-xs font-bold text-gray-600">Target</div>
                                <div className="text-sm  text-gray-900 truncate">{target}</div>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 p-2 bg-orange-50 rounded">
                            <Flag className="h-4 w-4 text-orange-400" />
                            <div className="min-w-0 flex-1">
                                <div className="text-xs font-bold text-gray-600">Goal</div>
                                <div className="text-sm  text-gray-900 truncate">{goal}</div>
                            </div>
                        </div>

                        <div className="flex items-center gap-2 p-2 bg-green-50 rounded">
                            <CheckCircle className="h-4 w-4 text-green-600" />
                            <div>
                                <div className="text-xs text-gray-600">Progress</div>
                                <div className="text-sm font-medium">
                                    {completedTasks}/{totalTasks}
                                </div>
                            </div>
                        </div>
                        <div>
                        {togglebutton}
                        </div>
                    </div>
                    
                </div>
                    

                {/* Tasks Overview */}
                <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
                    <h2 className="text-base font-semibold text-gray-900 mb-3">Tasks</h2>

                    {totalTasks === 0 ? (
                        <div className="text-sm text-gray-500">No tasks yet.</div>
                    ) : (
                        <div className="space-y-3">
                            {sortedTasks.map((task, idx) => (
                                <div
                                    key={task?.node_id ?? `${task?.label ?? 'task'}-${idx}`}
                                    className="border border-gray-200 rounded p-3"
                                >
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            {getStatusIcon(task?.status)}
                                            <div className="min-w-0">
                                                <h3 className="text-sm font-medium text-gray-900 truncate">
                                                    {formatTaskName(task?.label)}
                                                </h3>
                                                <div className="text-xs text-gray-500">
                                                    {task?.function && (
                                                        <span className="capitalize">
                                                            {task.function.replace(/_/g, ' ')}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {task?.result && (
                                        <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                                            <div className="text-gray-600 mb-1">Results:</div>
                                            {Array.isArray(task.result.endpoints) && task.result.endpoints.length > 0 && (
                                                <div>
                                                    {task.result.endpoints.map((endpoint, eIdx) => (
                                                        <div key={eIdx} className="space-y-1">
                                                            {endpoint?.url && (
                                                                <div className="text-gray-600 break-all">
                                                                    <strong>URL:</strong> {endpoint.url}
                                                                </div>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                            {task.result.assessments && (
                                                <div className="mt-1">
                                                    <div className="text-gray-600">Assessments: {task.result.assessments.length}</div>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {task?.status === 'in_progress' && (
                                        <div className="mt-2 p-2 bg-yellow-50 rounded">
                                            <div className="flex items-center gap-1 text-yellow-800 text-xs">
                                                <Clock className="h-3 w-3" />
                                                In progress...
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Remove for now because streaming doesn't correctly register token usage anyway */}
                {/* <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
                        <h2 className="text-base font-semibold text-gray-900 mb-3">Resources</h2>
                        <div className="grid grid-cols-2 gap-2">
                            <div className="p-2 bg-gray-50 rounded">
                                <div className="text-xs text-gray-600">Input</div>
                                <div className="text-sm font-semibold text-gray-900">{inputTokens}</div>
                            </div>
                            <div className="p-2 bg-gray-50 rounded">
                                <div className="text-xs text-gray-600">Output</div>
                                <div className="text-sm font-semibold text-gray-900">{outputTokens}</div>
                            </div>
                        </div>
                    </div> */}
            </div>
        </Sidebar >
    );
};
