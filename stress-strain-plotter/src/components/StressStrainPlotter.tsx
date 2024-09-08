'use client'

import React, { useState, useMemo, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

const StressStrainPlotter = () => {
  const [data, setData] = useState<Array<{stress: number, strain: number}>>([])
  const [stress, setStress] = useState('')
  const [strain, setStrain] = useState('')
  const [graphTitle, setGraphTitle] = useState('Stress vs Strain Graph')
  const chartRef = useRef<any>(null)

  const addDataPoint = () => {
    if (stress && strain) {
      const newPoint = { stress: parseFloat(stress), strain: parseFloat(strain) };
      const newData = [...data, newPoint].sort((a, b) => a.strain - b.strain);
      setData(newData);
      setStress('');
      setStrain('');
    }
  }

  const clearData = () => {
    setData([])
  }

  const calculateMaterialProperties = useMemo(() => {
    if (data.length < 2) return null;

    // Tensile Strength (maximum stress)
    const tensileStrength = Math.max(...data.map(point => point.stress));

    // Young's Modulus (slope of the linear portion)
    const linearRegionCutoff = Math.ceil(data.length / 3);
    const linearRegion = data.slice(0, linearRegionCutoff);
    const avgStrain = linearRegion.reduce((sum, point) => sum + point.strain, 0) / linearRegion.length;
    const avgStress = linearRegion.reduce((sum, point) => sum + point.stress, 0) / linearRegion.length;
    const numerator = linearRegion.reduce((sum, point) => sum + (point.strain - avgStrain) * (point.stress - avgStress), 0);
    const denominator = linearRegion.reduce((sum, point) => sum + Math.pow(point.strain - avgStrain, 2), 0);
    const youngsModulus = numerator / denominator;

    // Yield Strength (0.2% offset method)
    const offsetStrain = 0.002; // 0.2% offset
    const yieldLine = data.map(point => ({
      strain: point.strain,
      stress: youngsModulus * (point.strain - offsetStrain)
    }));
    let yieldStrength = 0;
    for (let i = 0; i < data.length; i++) {
      if (data[i].stress >= yieldLine[i].stress) {
        yieldStrength = data[i].stress;
        break;
      }
    }

    // Toughness calculation (area under the stress-strain curve)
    let toughness = 0;
    for (let i = 1; i < data.length; i++) {
      const prevPoint = data[i - 1];
      const currentPoint = data[i];
      toughness += (currentPoint.strain - prevPoint.strain) * 
                   (currentPoint.stress + prevPoint.stress) / 2;
    }

    // Ductility (total elongation)
    const ductility = data[data.length - 1].strain - data[0].strain;

    // Resilience (area under the stress-strain curve up to the yield point)
    let resilience = 0;
    for (let i = 1; i < data.length && data[i].stress <= yieldStrength; i++) {
      const prevPoint = data[i - 1];
      const currentPoint = data[i];
      resilience += (currentPoint.strain - prevPoint.strain) * 
                    (currentPoint.stress + prevPoint.stress) / 2;
    }

    return {
      tensileStrength: tensileStrength.toFixed(2),
      youngsModulus: (youngsModulus / 1000).toFixed(2), // Convert to GPa
      yieldStrength: yieldStrength.toFixed(2),
      toughness: toughness.toFixed(4),
      ductility: ductility.toFixed(4),
      resilience: resilience.toFixed(4)
    };
  }, [data]);

  const exportGraph = () => {
    if (chartRef.current) {
      const svgElement = chartRef.current.container.children[0];
      const svgData = new XMLSerializer().serializeToString(svgElement);
      const svgBlob = new Blob([svgData], {type: "image/svg+xml;charset=utf-8"});
      const svgUrl = URL.createObjectURL(svgBlob);
      const downloadLink = document.createElement("a");
      downloadLink.href = svgUrl;
      downloadLink.download = "stress_strain_graph.svg";
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
      URL.revokeObjectURL(svgUrl);
    }
  }

  return (
    <div className="p-4 max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Stress vs Strain Plotter</h2>
      <div className="mb-4">
        <Input
          type="text"
          placeholder="Graph Title"
          value={graphTitle}
          onChange={(e) => setGraphTitle(e.target.value)}
          className="w-full mb-2"
        />
      </div>
      <div className="mb-4 flex space-x-2">
        <Input
          type="number"
          placeholder="Stress"
          value={stress}
          onChange={(e) => setStress(e.target.value)}
          className="w-1/3"
        />
        <Input
          type="number"
          placeholder="Strain"
          value={strain}
          onChange={(e) => setStrain(e.target.value)}
          className="w-1/3"
        />
        <Button onClick={addDataPoint} className="w-1/6">Add Point</Button>
        <Button onClick={clearData} className="w-1/6">Clear</Button>
      </div>
      <h3 className="text-xl font-semibold mb-2">{graphTitle}</h3>
      <div className="h-80 w-full mb-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart ref={chartRef} data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="strain" label={{ value: 'Strain', position: 'bottom' }} />
          <YAxis label={{ value: 'Stress', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Line type="monotone" dataKey="stress" stroke="#8884d8" />
        </LineChart>
      </ResponsiveContainer>
    </div>
      <Button onClick={exportGraph} className="mb-4">Export Graph</Button>
      {calculateMaterialProperties && (
        <div className="mb-4 p-4 bg-gray-100 rounded-md">
          <h3 className="text-lg font-semibold mb-2">Material Properties:</h3>
          <ul>
            <li>Tensile Strength: {calculateMaterialProperties.tensileStrength} MPa</li>
            <li>Young's Modulus: {calculateMaterialProperties.youngsModulus} GPa</li>
            <li>Yield Strength (0.2% offset): {calculateMaterialProperties.yieldStrength} MPa</li>
            <li>Toughness: {calculateMaterialProperties.toughness} MJ/m³</li>
            <li>Ductility: {calculateMaterialProperties.ductility} mm/mm</li>
            <li>Resilience: {calculateMaterialProperties.resilience} MJ/m³</li>
          </ul>
        </div>
      )}
      <div className="mt-4">
        <h3 className="text-lg font-semibold mb-2">Data Points:</h3>
        <ul className="list-disc pl-5">
          {data.map((point, index) => (
            <li key={index}>
              Stress: {point.stress}, Strain: {point.strain}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default StressStrainPlotter