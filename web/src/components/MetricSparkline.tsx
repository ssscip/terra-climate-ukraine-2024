import React from 'react';

interface Props { series: number[]; width?: number; height?: number; }

const MetricSparkline: React.FC<Props> = ({ series, width = 120, height = 30 }) => {
  if (!series.length) return <svg width={width} height={height}></svg>;
  const min = Math.min(...series); const max = Math.max(...series);
  const norm = series.map(v => (v - min) / (max - min || 1));
  const points = norm.map((v,i) => `${(i/(series.length-1))*width},${(1-v)*height}`).join(' ');
  return (
    <svg width={width} height={height} className="sparkline">
      <polyline fill="none" stroke="#ff6600" strokeWidth="2" points={points} />
    </svg>
  );
};

export default MetricSparkline;
