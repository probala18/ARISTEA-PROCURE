'use client';

import React, { useState } from 'react';
import { PrimarySourceItem, ComplianceTaskItem } from '@/lib/api';

interface PrimarySourceTrackerSectionProps {
  primarySources?: PrimarySourceItem[];
  initialTasks?: ComplianceTaskItem[];
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

export const PrimarySourceTrackerSection: React.FC<PrimarySourceTrackerSectionProps> = ({
  primarySources = [],
  initialTasks = [],
  onToast,
}) => {
  const [tasks, setTasks] = useState<ComplianceTaskItem[]>(initialTasks);
  const [newTitle, setNewTitle] = useState('');
  const [newSource, setNewSource] = useState(primarySources[0]?.name || 'BIS Manakonline');
  const [newPriority, setNewPriority] = useState<'High' | 'Medium' | 'Low'>('High');

  const completedCount = tasks.filter(t => t.status === 'COMPLETED').length;
  const progressPct = tasks.length > 0 ? Math.round((completedCount / tasks.length) * 100) : 0;

  const handleToggleStatus = (taskId: string) => {
    setTasks(prev =>
      prev.map(t => {
        if (t.id !== taskId) return t;
        const nextStatus = t.status === 'PENDING' ? 'IN_PROGRESS' : t.status === 'IN_PROGRESS' ? 'COMPLETED' : 'PENDING';
        return { ...t, status: nextStatus };
      })
    );
    onToast('Task status updated.', 'info');
  };

  const handleAddTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) {
      onToast('Please enter a task title.', 'error');
      return;
    }
    const matchedSource = primarySources.find(s => s.name === newSource);
    const newTask: ComplianceTaskItem = {
      id: `TASK-${Date.now().toString().slice(-4)}`,
      title: newTitle.trim(),
      description: `Action item set in app linked to ${newSource}.`,
      primary_source_name: newSource,
      primary_source_url: matchedSource?.url || 'https://www.manakonline.in',
      priority: newPriority,
      status: 'PENDING',
      due_stage: 'Active Procurement Vetting',
    };
    setTasks(prev => [newTask, ...prev]);
    setNewTitle('');
    onToast(`Added task: "${newTask.title}"`, 'success');
  };

  const handleDeleteTask = (taskId: string) => {
    setTasks(prev => prev.filter(t => t.id !== taskId));
    onToast('Task removed.', 'info');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Primary Authoritative Sources List */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: 'var(--radius-lg, 12px)',
          border: '1px solid #e2e8f0',
          padding: '20px',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
        }}
      >
        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#0f172a' }}>
            🏛️ Statutory Primary Sources Directory
          </h3>
          <p style={{ margin: '2px 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
            Authoritative portals to inspect original gazette orders, BIS product licenses, and standard specifications.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
          {primarySources.map((source, idx) => (
            <div
              key={idx}
              style={{
                padding: '16px',
                borderRadius: '10px',
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '10px',
              }}
            >
              <div>
                <span
                  style={{
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: '#e0e7ff',
                    color: '#4338ca',
                  }}
                >
                  {source.category}
                </span>
                <div style={{ fontSize: '0.94rem', fontWeight: 700, color: '#0f172a', marginTop: '6px' }}>
                  {source.name}
                </div>
                <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '4px', lineHeight: 1.4 }}>
                  {source.description}
                </div>
              </div>

              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  background: '#ffffff',
                  border: '1px solid #cbd5e1',
                  color: '#4f46e5',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  textDecoration: 'none',
                  alignSelf: 'flex-start',
                }}
              >
                <span>🌐 Visit Primary Portal</span>
                <span style={{ fontSize: '0.7rem' }}>↗</span>
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* Task Tracker & Form */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: 'var(--radius-lg, 12px)',
          border: '1px solid #e2e8f0',
          padding: '20px',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#0f172a' }}>
              🎯 In-App Compliance Task Tracker & Action List
            </h3>
            <p style={{ margin: '2px 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
              Assign and track compliance vetting actions directly inside the app with one-click links to primary source evidence.
            </p>
          </div>

          {/* Progress Indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#0f172a' }}>
              {completedCount} of {tasks.length} Completed ({progressPct}%)
            </span>
            <div style={{ width: '120px', height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
              <div
                style={{
                  height: '100%',
                  width: `${progressPct}%`,
                  background: progressPct === 100 ? '#10b981' : '#4f46e5',
                  borderRadius: '4px',
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
          </div>
        </div>

        {/* Set Task in App Form */}
        <form
          onSubmit={handleAddTask}
          style={{
            padding: '14px 16px',
            borderRadius: '10px',
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            marginBottom: '20px',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '12px',
            alignItems: 'center',
          }}
        >
          <input
            type="text"
            placeholder="Type a compliance action (e.g. Verify pump ISI mark on Manakonline)..."
            value={newTitle}
            onChange={e => setNewTitle(e.target.value)}
            style={{
              flex: '1 1 300px',
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              fontSize: '0.84rem',
            }}
          />

          <select
            value={newSource}
            onChange={e => setNewSource(e.target.value)}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              fontSize: '0.84rem',
              background: '#ffffff',
            }}
          >
            {primarySources.map((s, idx) => (
              <option key={idx} value={s.name}>
                {s.name}
              </option>
            ))}
          </select>

          <select
            value={newPriority}
            onChange={e => setNewPriority(e.target.value as any)}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              fontSize: '0.84rem',
              background: '#ffffff',
            }}
          >
            <option value="High">🔴 High Priority</option>
            <option value="Medium">🟡 Medium Priority</option>
            <option value="Low">🟢 Low Priority</option>
          </select>

          <button
            type="submit"
            style={{
              padding: '8px 18px',
              borderRadius: '6px',
              background: '#4f46e5',
              color: '#ffffff',
              fontSize: '0.84rem',
              fontWeight: 700,
              border: 'none',
              cursor: 'pointer',
              boxShadow: '0 2px 8px rgba(79, 70, 229, 0.25)',
            }}
          >
            ➕ Set Task in App
          </button>
        </form>

        {/* Task Cards List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {tasks.map(task => {
            const isDone = task.status === 'COMPLETED';
            const inProg = task.status === 'IN_PROGRESS';

            return (
              <div
                key={task.id}
                style={{
                  padding: '14px 16px',
                  borderRadius: '10px',
                  background: isDone ? '#f0fdf4' : inProg ? '#fefce8' : '#ffffff',
                  border: isDone ? '1px solid #bbf7d0' : inProg ? '1px solid #fef08a' : '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px',
                  flexWrap: 'wrap',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: '1 1 350px' }}>
                  {/* Status Toggle Button */}
                  <button
                    onClick={() => handleToggleStatus(task.id)}
                    style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      border: isDone ? '2px solid #059669' : '2px solid #cbd5e1',
                      background: isDone ? '#059669' : '#ffffff',
                      color: isDone ? '#ffffff' : '#64748b',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                      fontWeight: 800,
                    }}
                    title="Click to toggle status"
                  >
                    {isDone ? '✓' : inProg ? '↻' : '○'}
                  </button>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          fontSize: '0.9rem',
                          fontWeight: 700,
                          color: isDone ? '#15803d' : '#0f172a',
                          textDecoration: isDone ? 'line-through' : 'none',
                        }}
                      >
                        {task.title}
                      </span>
                      <span
                        style={{
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          padding: '1px 6px',
                          borderRadius: '4px',
                          background: task.priority === 'High' ? '#fee2e2' : '#fef3c7',
                          color: task.priority === 'High' ? '#b91c1c' : '#b45309',
                        }}
                      >
                        {task.priority}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
                      {task.description} • <em>Stage: {task.due_stage}</em>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <a
                    href={task.primary_source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      background: '#ffffff',
                      border: '1px solid #cbd5e1',
                      color: '#4f46e5',
                      fontSize: '0.74rem',
                      fontWeight: 600,
                      textDecoration: 'none',
                    }}
                  >
                    <span>Inspect on {task.primary_source_name}</span>
                    <span style={{ fontSize: '0.66rem' }}>↗</span>
                  </a>

                  <button
                    onClick={() => handleDeleteTask(task.id)}
                    style={{
                      border: 'none',
                      background: 'transparent',
                      color: '#94a3b8',
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                      padding: '4px',
                    }}
                    title="Delete task"
                  >
                    ✕
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
