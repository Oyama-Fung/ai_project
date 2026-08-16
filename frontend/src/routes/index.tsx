import { BasicLayout } from "@/layouts/BasicLayout";
import { HomePage } from "@/pages/HomePage";
import { createBrowserRouter } from "react-router-dom";
import { DocumentPage } from "@/pages/DocumentsPage";
import { DocumentDetailPage } from "@/pages/DocumentDetailPage"

export const router = createBrowserRouter([
    {
        path: '/',
        element: <BasicLayout />,
        children: [
            { index: true, element: <HomePage /> },
            { path: 'documents', element: <DocumentPage /> },
            { path: 'documents/:id', element: <DocumentDetailPage /> },
        ]
    }
])