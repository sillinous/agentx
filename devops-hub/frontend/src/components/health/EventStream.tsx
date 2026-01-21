import { useEffect, useRef, useState } from 'react';
import { Badge, Card } from '../ui';
import type { Event } from '../../types';

interface EventStreamProps {
  events: Event[];
  maxHeight?: string;
  autoScroll?: boolean;
  onEventClick?: (event: Event) => void;
}

const eventTypeVariants: Record<string, 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple'> = {
  'agent.registered': 'success',
  'agent.updated': 'info',
  'agent.deleted': 'danger',
  'agent.executed': 'purple',
  'workflow.started': 'info',
  'workflow.completed': 'success',
  'workflow.failed': 'danger',
  'system.startup': 'success',
  'system.shutdown': 'warning',
  'system.error': 'danger',
  'system.health': 'default',
};

function getEventVariant(eventType: string): 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple' {
  return eventTypeVariants[eventType] || 'default';
}

function formatEventTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

function formatEventDate(timestamp: string): string {
  const date = new Date(timestamp);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (date.toDateString() === today.toDateString()) {
    return 'Today';
  }
  if (date.toDateString() === yesterday.toDateString()) {
    return 'Yesterday';
  }
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

interface EventItemProps {
  event: Event;
  onClick?: () => void;
}

function EventItem({ event, onClick }: EventItemProps) {
  return (
    <div
      className={`flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors ${
        onClick ? 'cursor-pointer' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex-shrink-0 w-16 text-xs text-gray-500 font-mono">
        {formatEventTime(event.timestamp)}
      </div>
      <div className="flex-shrink-0">
        <Badge variant={getEventVariant(event.type)}>{event.type}</Badge>
      </div>
      <div className="flex-grow min-w-0">
        <p className="text-sm text-gray-700 truncate">{event.source}</p>
        {event.correlation_id && (
          <p className="text-xs text-gray-400 font-mono truncate mt-0.5">
            {event.correlation_id}
          </p>
        )}
      </div>
    </div>
  );
}

export default function EventStream({
  events,
  maxHeight = '400px',
  autoScroll = true,
  onEventClick,
}: EventStreamProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');

  const eventTypes = ['all', ...new Set(events.map((e) => e.type))];

  const filteredEvents = filterType === 'all'
    ? events
    : events.filter((e) => e.type === filterType);

  useEffect(() => {
    if (autoScroll && !isUserScrolling && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [filteredEvents, autoScroll, isUserScrolling]);

  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      setIsUserScrolling(!isAtBottom);
    }
  };

  const groupedEvents = filteredEvents.reduce((groups, event) => {
    const date = formatEventDate(event.timestamp);
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(event);
    return groups;
  }, {} as Record<string, Event[]>);

  return (
    <Card padding="none" className="overflow-hidden">
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">Event Stream</h3>
        <div className="flex items-center gap-2">
          <label htmlFor="event-filter" className="text-sm text-gray-500">
            Filter:
          </label>
          <select
            id="event-filter"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {eventTypes.map((type) => (
              <option key={type} value={type}>
                {type === 'all' ? 'All Events' : type}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="overflow-auto"
        style={{ maxHeight }}
      >
        {filteredEvents.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            No events to display
          </div>
        ) : (
          <div className="p-4 space-y-4">
            {Object.entries(groupedEvents).map(([date, dateEvents]) => (
              <div key={date}>
                <div className="sticky top-0 bg-white py-1 mb-2">
                  <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    {date}
                  </span>
                </div>
                <div className="space-y-2">
                  {dateEvents.map((event) => (
                    <EventItem
                      key={event.id}
                      event={event}
                      onClick={onEventClick ? () => onEventClick(event) : undefined}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {isUserScrolling && filteredEvents.length > 0 && (
        <div className="p-2 border-t border-gray-200 bg-gray-50 text-center">
          <button
            onClick={() => {
              if (containerRef.current) {
                containerRef.current.scrollTop = containerRef.current.scrollHeight;
                setIsUserScrolling(false);
              }
            }}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Scroll to latest events
          </button>
        </div>
      )}
    </Card>
  );
}

interface CompactEventListProps {
  events: Event[];
  limit?: number;
}

export function CompactEventList({ events, limit = 5 }: CompactEventListProps) {
  const displayEvents = events.slice(0, limit);

  return (
    <div className="space-y-2">
      {displayEvents.map((event) => (
        <div
          key={event.id}
          className="flex items-center gap-2 text-sm"
        >
          <span className="text-gray-400 text-xs font-mono">
            {formatEventTime(event.timestamp)}
          </span>
          <Badge variant={getEventVariant(event.type)}>{event.type}</Badge>
          <span className="text-gray-600 truncate">{event.source}</span>
        </div>
      ))}
      {events.length === 0 && (
        <p className="text-gray-400 text-sm text-center py-4">No recent events</p>
      )}
    </div>
  );
}
