// import React from "react";
// import ReactDOM from "react-dom/client";
// import App from "./App.jsx";
// import "./index.css";
// import { ApiContextProvider } from './context/ApiContext.jsx'


// ReactDOM.createRoot(document.getElementById("root")).render(
//   <React.StrictMode>
//     <ApiContextProvider>
//       <App />
//     </ApiContextProvider>
//   </React.StrictMode>
// );

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './index.css';

createRoot(document.getElementById('root')).render(
  <App />
)