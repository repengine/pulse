import { createRoot } from 'react-dom/client';
import React from 'react';
import ReactDOM from 'react-dom';

const App: React.FC = () => {
  return (
    <div>
      <h2>Hello, Pulse Desktop!</h2>
    </div>
  );
};

const container = document.getElementById('root');
const root = createRoot(container!); // createRoot(container!) if using TypeScript
root.render(<App />);