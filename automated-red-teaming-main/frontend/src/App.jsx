import {
    createBrowserRouter,
    RouterProvider,
    Navigate,
} from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import MainLayout from "./components/MainLayout";
import { useMemo } from "react";
import { ApiContextProvider } from "./context/ApiContext";

export default function App() {
    const router = useMemo(
        () =>
            createBrowserRouter([
                {
                    path: "/",
                    element: <MainLayout />,
                    children: [
                        {
                            index: true,
                            element: <ChatPage />,
                        },
                        {
                            path: "demo",
                            element: <ChatPage />,
                        },
                    ],
                },
            ]),
        []
    );


    return (
        <ApiContextProvider>
            <RouterProvider router={router} />
        </ApiContextProvider>
    );
}