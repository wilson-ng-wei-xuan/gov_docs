import { Radar, Bird } from "lucide-react";

export default function Header() {
    return (
        <header className="bg-white/90 border-b shadow-sm">
            <div className="ml-25 flex items-center max-w-5xl px-6 py-4 gap-x-3">
                <Bird className="w-10 h-10 text-neutral-500" />
                <h1 className="text-2xl md:text-3xl font-bold text-neutral-800">
                    Maya: Agentic Pentesting 
                </h1>
            </div>
        </header>
    );
}
