import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/globals.css';
import GlobeView from './components/Globe';

const App = () => {
  return (
    <div className="app-root">
      <header>
        <h1>TerraTales — 25 Years of Earth’s Wonders</h1>
      </header>
      <GlobeView />
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(<App />);
