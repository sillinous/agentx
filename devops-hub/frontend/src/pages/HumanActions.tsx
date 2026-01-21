import { useState } from 'react';
import {
  useHITLRequests,
  useHITLStatistics,
  useFulfillHITLRequest,
  useRejectHITLRequest,
} from '../api/hooks/useHITL';
import type { HITLRequest } from '../api/hooks/useHITL';
import { Card, Badge, Button, Select, SkeletonCard, EmptyState, useToast } from '../components/ui';

type StatusFilter = 'all' | 'pending' | 'in_review' | 'fulfilled' | 'rejected';
type PriorityFilter = 'all' | 'low' | 'medium' | 'high' | 'critical';

export default function HumanActions() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>('all');
  const [selectedRequest, setSelectedRequest] = useState<HITLRequest | null>(null);

  const { data: requests = [], isLoading } = useHITLRequests(
    statusFilter === 'all' ? undefined : statusFilter,
    priorityFilter === 'all' ? undefined : priorityFilter
  );
  const { data: stats } = useHITLStatistics();

  const pendingRequests = requests.filter((r) => r.status === 'pending' || r.status === 'in_review');
  const completedRequests = requests.filter((r) => r.status === 'fulfilled' || r.status === 'rejected');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Human Actions</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Manage requests from AI agents that require human input
        </p>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Pending</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {stats.pending_requests}
                </p>
              </div>
              <div className="w-12 h-12 bg-amber-100 dark:bg-amber-900 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Total</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {stats.total_requests}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Fulfilled</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {stats.by_status.fulfilled || 0}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Avg Response</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {stats.average_response_time_hours.toFixed(1)}h
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4">
        <Select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
        >
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="in_review">In Review</option>
          <option value="fulfilled">Fulfilled</option>
          <option value="rejected">Rejected</option>
        </Select>

        <Select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value as PriorityFilter)}
        >
          <option value="all">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </Select>
      </div>

      {/* Requests List */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : requests.length === 0 ? (
        <EmptyState
          title="No human actions required"
          description="All agents are running smoothly. Requests will appear here when agents need your help."
          illustration="workflows"
        />
      ) : (
        <div className="space-y-6">
          {/* Pending Requests */}
          {pendingRequests.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Pending Requests ({pendingRequests.length})
              </h2>
              <div className="grid grid-cols-1 gap-4">
                {pendingRequests.map((request) => (
                  <RequestCard
                    key={request.id}
                    request={request}
                    onClick={() => setSelectedRequest(request)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Completed Requests */}
          {completedRequests.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Completed Requests ({completedRequests.length})
              </h2>
              <div className="grid grid-cols-1 gap-4">
                {completedRequests.map((request) => (
                  <RequestCard
                    key={request.id}
                    request={request}
                    onClick={() => setSelectedRequest(request)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Request Detail Modal */}
      {selectedRequest && (
        <RequestDetailModal
          request={selectedRequest}
          onClose={() => setSelectedRequest(null)}
        />
      )}
    </div>
  );
}

interface RequestCardProps {
  request: HITLRequest;
  onClick: () => void;
}

function RequestCard({ request, onClick }: RequestCardProps) {
  const priorityColors = {
    critical: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
    high: 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200',
    medium: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200',
    low: 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200',
  };

  const statusColors = {
    pending: 'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200',
    in_review: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
    fulfilled: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
    rejected: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
    cancelled: 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200',
  };

  const typeIcons: Record<string, string> = {
    api_key: '🔑',
    account_creation: '👤',
    legal_document: '📄',
    payment_authorization: '💳',
    business_setup: '🏢',
    strategic_decision: '🎯',
    custom: '📋',
  };

  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={onClick}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">{typeIcons[request.request_type] || '📋'}</span>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {request.title}
            </h3>
          </div>
          
          <p className="text-gray-600 dark:text-gray-300 mb-3">{request.description}</p>
          
          <div className="flex items-center gap-2 flex-wrap">
            <Badge className={statusColors[request.status]}>
              {request.status.replace('_', ' ')}
            </Badge>
            <Badge className={priorityColors[request.priority]}>
              {request.priority}
            </Badge>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Agent: {request.agent_id}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {new Date(request.created_at).toLocaleString()}
            </span>
          </div>
        </div>

        <svg className="w-5 h-5 text-gray-400 dark:text-gray-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </Card>
  );
}

interface RequestDetailModalProps {
  request: HITLRequest;
  onClose: () => void;
}

function RequestDetailModal({ request, onClose }: RequestDetailModalProps) {
  const [fulfillData, setFulfillData] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [userName, setUserName] = useState('');
  
  const fulfillMutation = useFulfillHITLRequest(request.id);
  const rejectMutation = useRejectHITLRequest(request.id);
  const toast = useToast();

  const handleFulfill = async () => {
    if (!userName.trim()) {
      toast.showToast('error', 'Name required', 'Please enter your name');
      return;
    }

    try {
      await fulfillMutation.mutateAsync({
        fulfilled_by: userName,
        response_data: fulfillData,
        notes: notes || undefined,
      });
      toast.showToast('success', 'Request fulfilled', 'The agent has been notified');
      onClose();
    } catch (error) {
      toast.showToast('error', 'Failed to fulfill', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const handleReject = async () => {
    if (!userName.trim() || !rejectReason.trim()) {
      toast.showToast('error', 'Required fields missing', 'Please provide your name and reason');
      return;
    }

    try {
      await rejectMutation.mutateAsync({
        rejected_by: userName,
        reason: rejectReason,
      });
      toast.showToast('success', 'Request rejected', 'The agent has been notified');
      onClose();
    } catch (error) {
      toast.showToast('error', 'Failed to reject', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const canFulfill = request.status === 'pending' || request.status === 'in_review';
  const isCompleted = request.status === 'fulfilled' || request.status === 'rejected';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-6 space-y-6">
          {/* Header */}
          <div className="flex items-start justify-between">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{request.title}</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Request Details */}
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Description</h3>
              <p className="text-gray-900 dark:text-gray-100">{request.description}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Type</h3>
                <p className="text-gray-900 dark:text-gray-100">{request.request_type.replace('_', ' ')}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Priority</h3>
                <p className="text-gray-900 dark:text-gray-100 capitalize">{request.priority}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Agent</h3>
                <p className="text-gray-900 dark:text-gray-100">{request.agent_id}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Created</h3>
                <p className="text-gray-900 dark:text-gray-100">{new Date(request.created_at).toLocaleString()}</p>
              </div>
            </div>

            {/* Required Fields */}
            {Object.keys(request.required_fields).length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Required Information</h3>
                <div className="space-y-3">
                  {Object.entries(request.required_fields).map(([key, description]) => (
                    <div key={key}>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        {description}
                      </label>
                      {isCompleted ? (
                        <p className="text-gray-900 dark:text-gray-100 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                          {String(request.response_data?.[key] ?? 'N/A')}
                        </p>
                      ) : (
                        <input
                          type="text"
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-100"
                          value={fulfillData[key] || ''}
                          onChange={(e) => setFulfillData({ ...fulfillData, [key]: e.target.value })}
                          disabled={!canFulfill}
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Context Information */}
            {Object.keys(request.context).length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Context</h3>
                <pre className="text-xs text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 p-3 rounded-lg overflow-x-auto">
                  {JSON.stringify(request.context, null, 2)}
                </pre>
              </div>
            )}

            {/* Completion Info */}
            {isCompleted && (
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      {request.status === 'fulfilled' ? 'Fulfilled By' : 'Rejected By'}
                    </h3>
                    <p className="text-gray-900 dark:text-gray-100">{request.fulfilled_by}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      {request.status === 'fulfilled' ? 'Fulfilled At' : 'Rejected At'}
                    </h3>
                    <p className="text-gray-900 dark:text-gray-100">
                      {request.fulfilled_at ? new Date(request.fulfilled_at).toLocaleString() : 'N/A'}
                    </p>
                  </div>
                </div>
                {request.notes && (
                  <div className="mt-4">
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Notes</h3>
                    <p className="text-gray-900 dark:text-gray-100">{request.notes}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Form */}
          {canFulfill && (
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Your Name *
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-100"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  placeholder="Enter your name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-100"
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add any additional notes..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Reject Reason (if rejecting)
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-red-500 dark:bg-gray-700 dark:text-gray-100"
                  rows={2}
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Why are you rejecting this request?"
                />
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={handleFulfill}
                  disabled={fulfillMutation.isPending}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                >
                  {fulfillMutation.isPending ? 'Fulfilling...' : 'Fulfill Request'}
                </Button>
                <Button
                  onClick={handleReject}
                  disabled={rejectMutation.isPending}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                >
                  {rejectMutation.isPending ? 'Rejecting...' : 'Reject Request'}
                </Button>
              </div>
            </div>
          )}

          {!canFulfill && !isCompleted && (
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
              <Button onClick={onClose} className="w-full">
                Close
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
