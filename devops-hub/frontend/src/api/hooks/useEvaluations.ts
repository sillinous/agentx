import { useState, useCallback, useEffect } from 'react';
import type { Evaluation } from '../../types';

const STORAGE_KEY = 'devops-hub-evaluations';

function loadEvaluations(): Evaluation[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveEvaluations(evaluations: Evaluation[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(evaluations));
}

export function useEvaluations() {
  const [evaluations, setEvaluations] = useState<Evaluation[]>(() => loadEvaluations());

  useEffect(() => {
    saveEvaluations(evaluations);
  }, [evaluations]);

  const addEvaluation = useCallback(
    (evaluation: Omit<Evaluation, 'id' | 'createdAt'>) => {
      const newEvaluation: Evaluation = {
        ...evaluation,
        id: crypto.randomUUID(),
        createdAt: new Date().toISOString(),
      };
      setEvaluations((prev) => [newEvaluation, ...prev]);
      return newEvaluation;
    },
    []
  );

  const deleteEvaluation = useCallback((id: string) => {
    setEvaluations((prev) => prev.filter((e) => e.id !== id));
  }, []);

  const getEvaluationsForTarget = useCallback(
    (targetType: 'agent' | 'workflow', targetId: string) => {
      return evaluations.filter(
        (e) => e.targetType === targetType && e.targetId === targetId
      );
    },
    [evaluations]
  );

  const getAverageRating = useCallback(
    (targetType: 'agent' | 'workflow', targetId: string) => {
      const targetEvaluations = getEvaluationsForTarget(targetType, targetId);
      if (targetEvaluations.length === 0) return null;
      const sum = targetEvaluations.reduce((acc, e) => acc + e.rating, 0);
      return sum / targetEvaluations.length;
    },
    [getEvaluationsForTarget]
  );

  const exportToCsv = useCallback(() => {
    const headers = [
      'ID',
      'Type',
      'Target ID',
      'Target Name',
      'Rating',
      'Feedback',
      'Execution ID',
      'Created At',
    ];
    const rows = evaluations.map((e) => [
      e.id,
      e.targetType,
      e.targetId,
      e.targetName,
      e.rating.toString(),
      `"${e.feedback.replace(/"/g, '""')}"`,
      e.executionId || '',
      e.createdAt,
    ]);
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evaluations-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [evaluations]);

  return {
    evaluations,
    addEvaluation,
    deleteEvaluation,
    getEvaluationsForTarget,
    getAverageRating,
    exportToCsv,
  };
}
