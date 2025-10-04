import React from 'react';

interface Props { event: any | null; onClose: () => void; }

const EventPanel: React.FC<Props> = ({ event, onClose }) => {
  if (!event) return null;
  return (
    <div className="event-panel">
      <button className="close" onClick={onClose}>×</button>
      <h2>{event.title}</h2>
      <p><strong>Category:</strong> {event.category}</p>
      <p><strong>Dates:</strong> {event.start_date} – {event.end_date}</p>
      {event.metrics && (
        <div className="metrics">
          {Object.entries(event.metrics).map(([k,v]) => <div key={k}>{k}: {String(v)}</div>)}
        </div>
      )}
      {event.media?.thumbnail && <img src={`/${event.media.thumbnail}`} alt="thumb" style={{maxWidth:'100%'}} />}
      {event.narrative?.short && <p>{event.narrative.short}</p>}
      {event.narrative?.long && <p style={{fontSize:'0.85rem', lineHeight:1.3}}>{event.narrative.long}</p>}
    </div>
  );
};

export default EventPanel;
