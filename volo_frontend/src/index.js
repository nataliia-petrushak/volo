import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import App2 from "./App2";
import {App3} from "./App3";


const router = createBrowserRouter([
  {
    path: "/text-to-speech",
    element: <App />,
  },
  {
    path: "/text-to-text",
    element: <App />,
  },
  {
    path: "/voice-to-voice",
    element: <App3 />,
  },
]);

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
      <RouterProvider router={router}>
          <App />
      </RouterProvider>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
