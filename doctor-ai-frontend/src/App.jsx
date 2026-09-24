import React, { useState } from 'react';
import axios from 'axios';
import { Stethoscope, FileText, Mic, FileSearch, Loader2, AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000'; // FastAPI backend server URL

export default function App() {
  const [activeTab, setActiveTab] = useState('consultation');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // Form states
  const [consultationText, setConsultationText] = useState('');
  const [historyText, setHistoryText] = useState('');
  const [audioFile, setAudioFile] = useState(null);
  const [ocrFile, setOcrFile] = useState(null);

  const resetState = () => {
    setError(null);
    setResult(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    resetState();
    setLoading(true);

    try {
      let res;
      if (activeTab === 'consultation') {
        res = await axios.post(`${API_BASE}/doctor-ai`, { consultation: consultationText });
      } else if (activeTab === 'history') {
        res = await axios.post(`${API_BASE}/history-summarize`, { history: historyText });
      } else if (activeTab === 'audio') {
        const formData = new FormData();
        formData.append('audio', audioFile);
        res = await axios.post(`${API_BASE}/doctor-ai/audio`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      } else if (activeTab === 'ocr') {
        const formData = new FormData();
        formData.append('file', ocrFile);
        res = await axios.post(`${API_BASE}/ai/ocr-parser`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      {/* Header */}
      <header className="bg-slate-900 text-white p-4 shadow-md">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <Stethoscope className="w-8 h-8 text-blue-400" />
          <h1 className="text-xl font-bold tracking-wide">Doctor AI Assistant</h1>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-6xl mx-auto p-6 grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Navigation & Input Column */}
        <section className="md:col-span-5 bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <div className="flex border-b border-slate-200 mb-6 gap-2">
            {[
              { id: 'consultation', label: 'Consult', icon: FileText },
              { id: 'history', label: 'History', icon: FileText },
              { id: 'audio', label: 'Audio', icon: Mic },
              { id: 'ocr', label: 'OCR Lab', icon: FileSearch },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id);
                    resetState();
                  }}
                  className={`flex items-center gap-1.5 pb-3 px-2 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {activeTab === 'consultation' && (
              <div>
                <label className="block text-sm font-medium mb-2 text-slate-700">
                  Consultation Text
                </label>
                <textarea
                  rows={8}
                  className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
                  placeholder="Paste physician notes or consultation narrative..."
                  value={consultationText}
                  onChange={(e) => setConsultationText(e.target.value)}
                  required
                />
              </div>
            )}

            {activeTab === 'history' && (
              <div>
                <label className="block text-sm font-medium mb-2 text-slate-700">
                  Patient Medical History
                </label>
                <textarea
                  rows={8}
                  className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
                  placeholder="Paste past clinical history..."
                  value={historyText}
                  onChange={(e) => setHistoryText(e.target.value)}
                  required
                />
              </div>
            )}

            {activeTab === 'audio' && (
              <div>
                <label className="block text-sm font-medium mb-2 text-slate-700">
                  Upload Audio Recording
                </label>
                <input
                  type="file"
                  accept="audio/*"
                  onChange={(e) => setAudioFile(e.target.files[0])}
                  className="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  required
                />
              </div>
            )}

            {activeTab === 'ocr' && (
              <div>
                <label className="block text-sm font-medium mb-2 text-slate-700">
                  Upload Lab Report (PDF or Image)
                </label>
                <input
                  type="file"
                  accept="image/*,application/pdf"
                  onChange={(e) => setOcrFile(e.target.files[0])}
                  className="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  required
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {loading ? 'Processing...' : 'Analyze & Process'}
            </button>
          </form>
        </section>

        {/* Results Column */}
        <section className="md:col-span-7 bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-lg font-semibold border-b pb-3 mb-4 text-slate-800">
            Structured Output
          </h2>

          {error && (
            <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-200 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 mt-0.5 shrink-0" />
              <div>
                <span className="font-semibold block">Error</span>
                <span className="text-sm">{error}</span>
              </div>
            </div>
          )}

          {!result && !error && !loading && (
            <div className="text-center py-12 text-slate-400 text-sm">
              Submit an input on the left to display AI-structured outputs here.
            </div>
          )}

          {result && (
            <div className="space-y-4">
              {result.transcript && (
                <div className="bg-slate-50 p-3 rounded-lg border text-sm">
                  <span className="font-semibold block text-slate-700 mb-1">
                    Transcript (Lang: {result.language}):
                  </span>
                  <p className="text-slate-600 italic">"{result.transcript}"</p>
                </div>
              )}

              {result.results && Array.isArray(result.results) ? (
                <div className="space-y-3">
                  <div className="text-sm text-slate-600">
                    <p><strong>Patient:</strong> {result.patient_name || 'N/A'}</p>
                    <p><strong>Lab:</strong> {result.lab_name || 'N/A'}</p>
                    <p><strong>Date:</strong> {result.report_date || 'N/A'}</p>
                  </div>
                  <table className="w-full text-sm text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-100 border-b">
                        <th className="p-2">Test</th>
                        <th className="p-2">Result</th>
                        <th className="p-2">Ref Range</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.results.map((res, i) => (
                        <tr
                          key={i}
                          className={`border-b ${res.is_abnormal ? 'bg-red-50 font-medium' : ''}`}
                        >
                          <td className="p-2">{res.test_name}</td>
                          <td className={`p-2 ${res.is_abnormal ? 'text-red-600' : ''}`}>
                            {res.observed_value} {res.unit}
                          </td>
                          <td className="p-2 text-slate-500">{res.reference_range || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto text-xs leading-relaxed">
                  {JSON.stringify(result, null, 2)}
                </pre>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}