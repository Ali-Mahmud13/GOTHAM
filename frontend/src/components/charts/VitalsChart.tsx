import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

// Placeholder data - will be replaced with real DB data later
const placeholderData = [
  { visit: 'Visit 1', bmi: 24.5, sysBP: 115, diaBP: 75, ogtt: 95 },
  { visit: 'Visit 2', bmi: 25.1, sysBP: 118, diaBP: 78, ogtt: 102 },
  { visit: 'Visit 3', bmi: 25.8, sysBP: 120, diaBP: 80, ogtt: 110 },
  { visit: 'Visit 4', bmi: 26.2, sysBP: 122, diaBP: 82, ogtt: 118 },
  { visit: 'Visit 5', bmi: 26.9, sysBP: 125, diaBP: 85, ogtt: 125 },
];

export const VitalsChart = () => {
  return (
    <div className="w-full h-[400px]">

      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={placeholderData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="visit" 
            tick={{ fill: '#6b7280', fontSize: 12 }}
          />
          <YAxis 
            tick={{ fill: '#6b7280', fontSize: 12 }}
            label={{ value: 'Value', angle: -90, position: 'insideLeft', style: { fill: '#374151' } }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '12px'
            }}
          />
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
          />
          
          {/* BMI Line */}
          <Line
            type="monotone"
            dataKey="bmi"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 4 }}
            activeDot={{ r: 6 }}
            name="BMI"
          />
          
          {/* Systolic BP Line */}
          <Line
            type="monotone"
            dataKey="sysBP"
            stroke="#ef4444"
            strokeWidth={2}
            dot={{ fill: '#ef4444', r: 4 }}
            activeDot={{ r: 6 }}
            name="Systolic BP"
          />
          
          {/* Diastolic BP Line */}
          <Line
            type="monotone"
            dataKey="diaBP"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={{ fill: '#f59e0b', r: 4 }}
            activeDot={{ r: 6 }}
            name="Diastolic BP"
          />
          
          {/* OGTT Line */}
          <Line
            type="monotone"
            dataKey="ogtt"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ fill: '#10b981', r: 4 }}
            activeDot={{ r: 6 }}
            name="OGTT (mg/dL)"
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Legend Explanation */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-3 rounded-lg">
          <p className="text-xs text-gray-600 font-semibold">BMI</p>
          <p className="text-lg font-bold text-blue-600">26.9</p>
          <p className="text-xs text-gray-500">Latest</p>
        </div>
        <div className="bg-red-50 p-3 rounded-lg">
          <p className="text-xs text-gray-600 font-semibold">Systolic BP</p>
          <p className="text-lg font-bold text-red-600">125</p>
          <p className="text-xs text-gray-500">mmHg</p>
        </div>
        <div className="bg-orange-50 p-3 rounded-lg">
          <p className="text-xs text-gray-600 font-semibold">Diastolic BP</p>
          <p className="text-lg font-bold text-orange-600">85</p>
          <p className="text-xs text-gray-500">mmHg</p>
        </div>
        <div className="bg-green-50 p-3 rounded-lg">
          <p className="text-xs text-gray-600 font-semibold">OGTT</p>
          <p className="text-lg font-bold text-green-600">125</p>
          <p className="text-xs text-gray-500">mg/dL</p>
        </div>
      </div>
    </div>
  );
};