import React, { useEffect, useRef, useState } from 'react';
import Globe from 'three-globe';
import * as THREE from 'three';
import { fetchEvents } from '../lib/api';
import EventPanel from './EventPanel';
import Timeline from './Timeline';

interface EventItem { id: string; title: string; year: number; lat: number; lon: number; category: string; }

const GlobeView: React.FC = () => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [globeObj, setGlobeObj] = useState<Globe | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [year, setYear] = useState<number | null>(null);
  const [active, setActive] = useState<EventItem | null>(null);

  useEffect(() => {
    fetchEvents().then(setEvents).catch(console.error);
  }, []);

  useEffect(() => {
    if (!containerRef.current || globeObj) return;
    const scene = new THREE.Scene();
    const renderer = new THREE.WebGLRenderer();
    renderer.setSize(containerRef.current.clientWidth, 500);
    containerRef.current.appendChild(renderer.domElement);

    const camera = new THREE.PerspectiveCamera(40, containerRef.current.clientWidth / 500, 0.1, 1000);
    camera.position.z = 300;

    const globe = new Globe();
    globe.arcsData([]);
    scene.add(globe);
    setGlobeObj(globe);

    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(5,5,5);
    scene.add(light);

    const animate = () => {
      requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();
  }, [globeObj]);

  useEffect(() => {
    if (!globeObj) return;
    const filtered = year ? events.filter(e => e.year === year) : events;
    globeObj.labelsData(filtered.map(e => ({
      lat: e.lat, lng: e.lon, text: e.title, id: e.id, year: e.year, category: e.category
    }))).labelLat('lat').labelLng('lng').labelText('text')
      .onLabelClick((obj: any) => {
        const ev = events.find(ev => ev.id === obj.id);
        if (ev) setActive(ev);
      });
  }, [globeObj, events, year]);

  return (
    <div className="globe-wrapper">
      <div ref={containerRef} className="globe-canvas" />
      <Timeline years={[...new Set(events.map(e => e.year))].sort()} onYearChange={setYear} />
      <EventPanel event={active} onClose={() => setActive(null)} />
    </div>
  );
};

export default GlobeView;
