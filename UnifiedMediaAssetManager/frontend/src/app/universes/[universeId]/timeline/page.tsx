'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Universe,
  Element,
  TimelineEvent,
  getUniverseById,
  listTimelineEvents,
  createTimelineEvent,
  updateTimelineEvent,
  deleteTimelineEvent,
  getEventParticipants,
} from '@/services/api';
import { useIsClient } from '@/hooks/useIsClient';
import { useToast } from '@/context/ToastContext';
import { ConfirmModal } from '@/components/Modal';
import { Skeleton, SkeletonText } from '@/components/Skeleton';
import { EmptyTimeline } from '@/components/EmptyState';

export default function TimelineViewerPage() {
  const params = useParams();
  const router = useRouter();
  const { universeId } = params;
  const toast = useToast();

  const [universe, setUniverse] = useState<Universe | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const isClient = useIsClient();

  // Delete confirmation modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [eventToDelete, setEventToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Form state for new event
  const [showAddForm, setShowAddForm] = useState(false);
  const [newEventTitle, setNewEventTitle] = useState('');
  const [newEventDescription, setNewEventDescription] = useState('');
  const [newEventTimestamp, setNewEventTimestamp] = useState('');
  const [newEventType, setNewEventType] = useState('');
  const [newEventSignificance, setNewEventSignificance] = useState('medium');
  const [newEventConsequences, setNewEventConsequences] = useState('');
  const [newEventLocationId, setNewEventLocationId] = useState('');
  const [newEventParticipants, setNewEventParticipants] = useState<string[]>([]);
  const [newParticipantId, setNewParticipantId] = useState('');

  // Edit state
  const [editingEvent, setEditingEvent] = useState<TimelineEvent | null>(null);
  const [editEventTitle, setEditEventTitle] = useState('');
  const [editEventDescription, setEditEventDescription] = useState('');
  const [editEventTimestamp, setEditEventTimestamp] = useState('');
  const [editEventType, setEditEventType] = useState('');
  const [editEventSignificance, setEditEventSignificance] = useState('medium');
  const [editEventConsequences, setEditEventConsequences] = useState('');
  const [editEventLocationId, setEditEventLocationId] = useState('');
  const [editEventParticipants, setEditEventParticipants] = useState<string[]>([]);

  // Filter state
  const [filterType, setFilterType] = useState('');
  const [filterSignificance, setFilterSignificance] = useState('');
  const [filterStartDate, setFilterStartDate] = useState('');
  const [filterEndDate, setFilterEndDate] = useState('');

  // Participant details cache
  const [participantDetails, setParticipantDetails] = useState<{ [eventId: string]: any }>({});

  useEffect(() => {
    if (isClient) {
      if (typeof universeId !== 'string') {
        setError('Invalid Universe ID.');
        setIsLoading(false);
        return;
      }

      async function loadData() {
        try {
          setIsLoading(true);

          // Load universe info
          const fetchedUniverse = await getUniverseById(universeId as string);
          if (fetchedUniverse) {
            setUniverse(fetchedUniverse);
          } else {
            setError('Universe not found.');
          }

          // Load timeline events
          await loadEvents();
        } catch (err) {
          console.error('Failed to load data:', err);
          setError('Failed to load timeline.');
        } finally {
          setIsLoading(false);
        }
      }
      loadData();
    }
  }, [isClient, universeId]);

  const loadEvents = async () => {
    try {
      const filters: any = {};
      if (filterType) filters.event_type = filterType;
      if (filterSignificance) filters.significance = filterSignificance;
      if (filterStartDate) filters.start_date = filterStartDate;
      if (filterEndDate) filters.end_date = filterEndDate;

      const fetchedEvents = await listTimelineEvents(
        universeId as string,
        Object.keys(filters).length > 0 ? filters : undefined
      );
      setEvents(fetchedEvents);
    } catch (err) {
      console.error('Failed to load events:', err);
    }
  };

  useEffect(() => {
    if (isClient && universeId) {
      loadEvents();
    }
  }, [filterType, filterSignificance, filterStartDate, filterEndDate, isClient, universeId]);

  const loadParticipantDetails = async (eventId: string) => {
    try {
      const details = await getEventParticipants(eventId);
      setParticipantDetails(prev => ({ ...prev, [eventId]: details }));
    } catch (err) {
      console.error('Failed to load participant details:', err);
    }
  };

  const handleAddEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEventTitle.trim() || !newEventTimestamp || typeof universeId !== 'string') {
      toast.warning('Please provide both a title and timestamp for the event.');
      return;
    }

    try {
      setIsSaving(true);
      setError(null);
      setSuccessMessage(null);

      const newEvent = await createTimelineEvent(universeId, {
        title: newEventTitle,
        description: newEventDescription || undefined,
        event_timestamp: newEventTimestamp,
        event_type: newEventType || undefined,
        significance: newEventSignificance,
        consequences: newEventConsequences || undefined,
        location_id: newEventLocationId || undefined,
        participants: newEventParticipants.length > 0 ? newEventParticipants : undefined,
      });

      setEvents([...events, newEvent].sort(
        (a, b) => new Date(a.event_timestamp).getTime() - new Date(b.event_timestamp).getTime()
      ));
      toast.success(`Event "${newEventTitle}" added to timeline`);

      // Reset form
      setNewEventTitle('');
      setNewEventDescription('');
      setNewEventTimestamp('');
      setNewEventType('');
      setNewEventSignificance('medium');
      setNewEventConsequences('');
      setNewEventLocationId('');
      setNewEventParticipants([]);
      setShowAddForm(false);
    } catch (err: any) {
      toast.error(err.message || 'Failed to create event. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdateEvent = async (eventId: string) => {
    if (!editingEvent) return;

    try {
      setIsSaving(true);
      setError(null);
      setSuccessMessage(null);

      const updatedEvent = await updateTimelineEvent(eventId, {
        title: editEventTitle,
        description: editEventDescription || undefined,
        event_timestamp: editEventTimestamp,
        event_type: editEventType || undefined,
        significance: editEventSignificance,
        consequences: editEventConsequences || undefined,
        location_id: editEventLocationId || undefined,
        participants: editEventParticipants.length > 0 ? editEventParticipants : undefined,
      });

      setEvents(
        events.map(e => (e.id === eventId ? updatedEvent : e)).sort(
          (a, b) => new Date(a.event_timestamp).getTime() - new Date(b.event_timestamp).getTime()
        )
      );
      toast.success('Event updated successfully');
      setEditingEvent(null);
    } catch (err: any) {
      toast.error(err.message || 'Failed to update event.');
    } finally {
      setIsSaving(false);
    }
  };

  const openDeleteModal = (eventId: string) => {
    setEventToDelete(eventId);
    setDeleteModalOpen(true);
  };

  const handleDeleteEvent = async () => {
    if (!eventToDelete) return;

    try {
      setIsDeleting(true);
      await deleteTimelineEvent(eventToDelete);
      setEvents(events.filter(e => e.id !== eventToDelete));
      toast.success('Event deleted successfully');
      setDeleteModalOpen(false);
      setEventToDelete(null);
    } catch (err: any) {
      toast.error(err.message || 'Failed to delete event.');
    } finally {
      setIsDeleting(false);
    }
  };

  const startEditingEvent = (event: TimelineEvent) => {
    setEditingEvent(event);
    setEditEventTitle(event.title);
    setEditEventDescription(event.description || '');
    setEditEventTimestamp(event.event_timestamp);
    setEditEventType(event.event_type || '');
    setEditEventSignificance(event.significance || 'medium');
    setEditEventConsequences(event.consequences || '');
    setEditEventLocationId(event.location_id || '');
    setEditEventParticipants(event.participants || []);
  };

  const cancelEditing = () => {
    setEditingEvent(null);
  };

  const addParticipant = (participantId: string, isEdit: boolean = false) => {
    if (!participantId.trim()) return;

    if (isEdit) {
      if (!editEventParticipants.includes(participantId)) {
        setEditEventParticipants([...editEventParticipants, participantId]);
      }
    } else {
      if (!newEventParticipants.includes(participantId)) {
        setNewEventParticipants([...newEventParticipants, participantId]);
        setNewParticipantId('');
      }
    }
  };

  const removeParticipant = (participantId: string, isEdit: boolean = false) => {
    if (isEdit) {
      setEditEventParticipants(editEventParticipants.filter(id => id !== participantId));
    } else {
      setNewEventParticipants(newEventParticipants.filter(id => id !== participantId));
    }
  };

  const getSignificanceColor = (significance?: string) => {
    switch (significance) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'major':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'minor':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // Render loading state
  if (!isClient || isLoading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <p className="text-gray-600">Loading timeline...</p>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0 max-w-6xl mx-auto">
      <Link href={`/universes/${universeId}`} className="text-indigo-600 hover:underline mb-6 block">
        &larr; Back to Universe
      </Link>

      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900">Timeline</h1>
        <p className="text-lg text-gray-600 mt-2">{universe?.name}</p>
        <p className="text-sm text-gray-500 mt-1">
          Track chronological events and their impact on your story world
        </p>
      </div>

      {/* Success/Error Messages */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg mb-6">
          {successMessage}
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Filters and Add Button */}
      <div className="bg-white shadow-lg rounded-lg p-6 mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-800">Filters</h2>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors duration-150 text-sm font-medium"
          >
            {showAddForm ? 'Cancel' : '+ Add Event'}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label htmlFor="filter-type" className="block text-sm font-medium text-gray-700 mb-1">
              Event Type
            </label>
            <select
              id="filter-type"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            >
              <option value="">All Types</option>
              <option value="battle">Battle</option>
              <option value="discovery">Discovery</option>
              <option value="political">Political</option>
              <option value="personal">Personal</option>
              <option value="technological">Technological</option>
              <option value="natural">Natural Disaster</option>
              <option value="cultural">Cultural</option>
            </select>
          </div>

          <div>
            <label htmlFor="filter-significance" className="block text-sm font-medium text-gray-700 mb-1">
              Significance
            </label>
            <select
              id="filter-significance"
              value={filterSignificance}
              onChange={(e) => setFilterSignificance(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            >
              <option value="">All Levels</option>
              <option value="critical">Critical</option>
              <option value="major">Major</option>
              <option value="medium">Medium</option>
              <option value="minor">Minor</option>
            </select>
          </div>

          <div>
            <label htmlFor="filter-start-date" className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              id="filter-start-date"
              type="datetime-local"
              value={filterStartDate}
              onChange={(e) => setFilterStartDate(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            />
          </div>

          <div>
            <label htmlFor="filter-end-date" className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              id="filter-end-date"
              type="datetime-local"
              value={filterEndDate}
              onChange={(e) => setFilterEndDate(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            />
          </div>
        </div>
      </div>

      {/* Add Event Form */}
      {showAddForm && (
        <div className="bg-white shadow-lg rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Create New Event</h2>
          <form onSubmit={handleAddEvent} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="event-title" className="block text-sm font-medium text-gray-700 mb-1">
                  Event Title <span className="text-red-500">*</span>
                </label>
                <input
                  id="event-title"
                  type="text"
                  value={newEventTitle}
                  onChange={(e) => setNewEventTitle(e.target.value)}
                  className="block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="e.g., The Battle of Neo-Tokyo"
                  required
                />
              </div>

              <div>
                <label htmlFor="event-timestamp" className="block text-sm font-medium text-gray-700 mb-1">
                  Date & Time <span className="text-red-500">*</span>
                </label>
                <input
                  id="event-timestamp"
                  type="datetime-local"
                  value={newEventTimestamp}
                  onChange={(e) => setNewEventTimestamp(e.target.value)}
                  className="block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="event-description" className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                id="event-description"
                value={newEventDescription}
                onChange={(e) => setNewEventDescription(e.target.value)}
                rows={3}
                className="block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Describe what happened during this event..."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="event-type" className="block text-sm font-medium text-gray-700 mb-1">
                  Event Type
                </label>
                <select
                  id="event-type"
                  value={newEventType}
                  onChange={(e) => setNewEventType(e.target.value)}
                  className="block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                >
                  <option value="">Select type...</option>
                  <option value="battle">Battle</option>
                  <option value="discovery">Discovery</option>
                  <option value="political">Political</option>
                  <option value="personal">Personal</option>
                  <option value="technological">Technological</option>
                  <option value="natural">Natural Disaster</option>
                  <option value="cultural">Cultural</option>
                </select>
              </div>

              <div>
                <label htmlFor="event-significance" className="block text-sm font-medium text-gray-700 mb-1">
                  Significance
                </label>
                <select
                  id="event-significance"
                  value={newEventSignificance}
                  onChange={(e) => setNewEventSignificance(e.target.value)}
                  className="block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                >
                  <option value="critical">Critical</option>
                  <option value="major">Major</option>
                  <option value="medium">Medium</option>
                  <option value="minor">Minor</option>
                </select>
              </div>

              <div>
                <label htmlFor="event-location" className="block text-sm font-medium text-gray-700 mb-1">
                  Location (Element ID)
                </label>
                <input
                  id="event-location"
                  type="text"
                  value={newEventLocationId}
                  onChange={(e) => setNewEventLocationId(e.target.value)}
                  className="block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Element ID of location"
                />
              </div>
            </div>

            <div>
              <label htmlFor="event-consequences" className="block text-sm font-medium text-gray-700 mb-1">
                Consequences
              </label>
              <textarea
                id="event-consequences"
                value={newEventConsequences}
                onChange={(e) => setNewEventConsequences(e.target.value)}
                rows={2}
                className="block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="What were the results or aftermath of this event?"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Participants (Element IDs)
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={newParticipantId}
                  onChange={(e) => setNewParticipantId(e.target.value)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Element ID of participant"
                />
                <button
                  type="button"
                  onClick={() => addParticipant(newParticipantId, false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm"
                >
                  Add
                </button>
              </div>
              {newEventParticipants.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {newEventParticipants.map((id, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm"
                    >
                      {id.substring(0, 8)}...
                      <button
                        type="button"
                        onClick={() => removeParticipant(id, false)}
                        className="text-indigo-600 hover:text-indigo-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={isSaving}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors duration-150 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? 'Creating...' : 'Create Event'}
              </button>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors duration-150 text-sm font-medium"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Timeline Events */}
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold text-gray-800">
          Events ({events.length})
        </h2>

        {events.length > 0 ? (
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-300"></div>

            {events.map((event, index) => (
              <div key={event.id} className="relative pl-20 pb-8">
                {/* Timeline dot */}
                <div
                  className={`absolute left-6 top-2 w-5 h-5 rounded-full border-4 ${
                    event.significance === 'critical'
                      ? 'bg-red-500 border-red-200'
                      : event.significance === 'major'
                      ? 'bg-orange-500 border-orange-200'
                      : event.significance === 'medium'
                      ? 'bg-blue-500 border-blue-200'
                      : 'bg-gray-500 border-gray-200'
                  }`}
                ></div>

                <div className="bg-white shadow-lg rounded-lg p-6 border border-gray-200">
                  {editingEvent?.id === event.id ? (
                    // Edit Mode (similar to add form but pre-populated)
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        handleUpdateEvent(event.id);
                      }}
                      className="space-y-4"
                    >
                      {/* Similar form fields as add form */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Event Title <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={editEventTitle}
                            onChange={(e) => setEditEventTitle(e.target.value)}
                            className="block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Date & Time <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="datetime-local"
                            value={editEventTimestamp}
                            onChange={(e) => setEditEventTimestamp(e.target.value)}
                            className="block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                            required
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                        <textarea
                          value={editEventDescription}
                          onChange={(e) => setEditEventDescription(e.target.value)}
                          rows={3}
                          className="block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        />
                      </div>

                      <div className="flex gap-2 pt-2">
                        <button
                          type="submit"
                          disabled={isSaving}
                          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm font-medium disabled:opacity-50"
                        >
                          {isSaving ? 'Saving...' : 'Save Changes'}
                        </button>
                        <button
                          type="button"
                          onClick={cancelEditing}
                          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 text-sm font-medium"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  ) : (
                    // Display Mode
                    <>
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <h3 className="text-xl font-bold text-gray-900">{event.title}</h3>
                          <p className="text-sm text-gray-500 mt-1">
                            {new Date(event.event_timestamp).toLocaleString()}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => startEditingEvent(event)}
                            className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => openDeleteModal(event.id)}
                            className="text-sm text-red-600 hover:text-red-800 font-medium"
                          >
                            Delete
                          </button>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2 mb-3">
                        {event.significance && (
                          <span
                            className={`text-xs px-3 py-1 rounded-full border ${getSignificanceColor(
                              event.significance
                            )}`}
                          >
                            {event.significance}
                          </span>
                        )}
                        {event.event_type && (
                          <span className="text-xs px-3 py-1 bg-purple-100 text-purple-800 rounded-full border border-purple-200">
                            {event.event_type}
                          </span>
                        )}
                      </div>

                      {event.description && (
                        <p className="text-gray-700 mb-3 whitespace-pre-wrap">{event.description}</p>
                      )}

                      {event.consequences && (
                        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-3">
                          <p className="text-sm font-medium text-yellow-900 mb-1">Consequences:</p>
                          <p className="text-sm text-yellow-800">{event.consequences}</p>
                        </div>
                      )}

                      {event.participants && event.participants.length > 0 && (
                        <div className="mt-3">
                          <p className="text-sm font-medium text-gray-700 mb-2">Participants:</p>
                          <div className="flex flex-wrap gap-2">
                            {event.participants.map((id, idx) => (
                              <span
                                key={idx}
                                className="text-xs px-2 py-1 bg-indigo-50 text-indigo-700 rounded border border-indigo-200 font-mono"
                              >
                                {id.substring(0, 8)}...
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyTimeline />
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setEventToDelete(null);
        }}
        onConfirm={handleDeleteEvent}
        title="Delete Timeline Event"
        message="Are you sure you want to delete this timeline event? This action cannot be undone."
        confirmText="Delete Event"
        cancelText="Cancel"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
}
