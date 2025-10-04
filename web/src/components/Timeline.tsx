import React from 'react';

interface Props { years: number[]; onYearChange: (y: number | null) => void; }

const Timeline: React.FC<Props> = ({ years, onYearChange }) => {
  if (!years.length) return <div className="timeline">No years</div>;
  return (
    <div className="timeline">
      <button onClick={() => onYearChange(null)}>All</button>
      {years.map(y => <button key={y} onClick={() => onYearChange(y)}>{y}</button>)}
    </div>
  );
};

export default Timeline;
