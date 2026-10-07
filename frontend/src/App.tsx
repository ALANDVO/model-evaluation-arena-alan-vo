import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import { AdvisoryReportView } from './components/AdvisoryReportView';
import { ArenaBenchmarkView } from './components/ArenaBenchmarkView';
import { DatasetManager } from './components/DatasetManager';
import { ModelRunUploader } from './components/ModelRunUploader';
import { Navbar } from './components/Navbar';
import { SliceDisparityView } from './components/SliceDisparityView';
import { useAuth } from './context/AuthContext';
import { ArenaEvaluationResponse, Dataset, ModelRun } from './types/api';

export const App: React.FC = () => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('arena');
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [modelRuns, setModelRuns] = useState<ModelRun[]>([]);
  const [evaluationResult, setEvaluationResult] = useState<ArenaEvaluationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const data = await api.listDatasets();
      setDatasets(data);
      if (data.length > 0 && !selectedDataset) {
        setSelectedDataset(data[0]);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const fetchRunsForDataset = async (datasetId: number) => {
    try {
      const runs = await api.listModelRuns(datasetId);
      setModelRuns(runs);
      if (runs.length >= 2) {
        // Auto-run evaluation for instantaneous arena visualization
        const evalRes = await api.runEvaluation({
          dataset_id: datasetId,
          model_run_ids: runs.map((r) => r.id),
          resamples: 300,
          confidence_level: 0.95,
        });
        setEvaluationResult(evalRes);
      }
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchDatasets();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (selectedDataset) {
      fetchRunsForDataset(selectedDataset.id);
    }
  }, [selectedDataset]);

  if (authLoading) {
    return <div className="app-loading">Initializing Model Evaluation Arena...</div>;
  }

  return (
    <div className="app-layout">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="main-content">
        {loading && datasets.length === 0 ? (
          <div className="card loading-card">Loading benchmark datasets...</div>
        ) : (
          <>
            {activeTab === 'arena' && (
              <ArenaBenchmarkView
                datasets={datasets}
                selectedDataset={selectedDataset}
                onSelectDataset={setSelectedDataset}
                modelRuns={modelRuns}
                evaluationResult={evaluationResult}
                onEvaluationComplete={setEvaluationResult}
              />
            )}

            {activeTab === 'datasets' && (
              <div className="datasets-tab-layout">
                <DatasetManager
                  datasets={datasets}
                  selectedDataset={selectedDataset}
                  onSelectDataset={setSelectedDataset}
                  onRefresh={fetchDatasets}
                />
                {selectedDataset && (
                  <ModelRunUploader
                    dataset={selectedDataset}
                    runs={modelRuns}
                    onRefreshRuns={() => fetchRunsForDataset(selectedDataset.id)}
                  />
                )}
              </div>
            )}

            {activeTab === 'slices' && (
              <SliceDisparityView
                slices={evaluationResult?.slice_breakdowns || []}
                models={evaluationResult?.models || []}
              />
            )}

            {activeTab === 'reports' && (
              <AdvisoryReportView
                selectedDataset={selectedDataset}
                modelRuns={modelRuns}
                reportId={evaluationResult?.report_id}
              />
            )}
          </>
        )}
      </main>

      <footer className="footer">
        <div className="footer-container">
          <span>Model Evaluation Arena &bull; Developed by Alan Vo (<code>alanvo@gmail.com</code>)</span>
          <span>Provider-Agnostic AI/ML Benchmark System</span>
        </div>
      </footer>
    </div>
  );
};
